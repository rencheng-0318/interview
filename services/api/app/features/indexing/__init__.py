"""Indexing workflow: chunk clinical documents and store embeddings."""

import logging
import re
from dataclasses import dataclass, field

import asyncpg

from app.clients.embedding import SupportsEmbedding

logger = logging.getLogger("api.indexing")

MAX_CHUNK_CHARS = 800
OVERLAP_CHARS = 50
MAX_TEXT_CHARS = 8_000


@dataclass
class IndexSummary:
    total_documents: int = 0
    already_indexed: int = 0
    indexed: int = 0
    skipped: int = 0
    failed: int = 0
    chunks_created: int = 0
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


def chunk_text(
    text: str, max_chars: int = MAX_CHUNK_CHARS, overlap: int = OVERLAP_CHARS
) -> list[str]:
    """Split text into overlapping chunks at sentence/paragraph boundaries."""
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    paragraphs = text.split("\n\n")
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        if len(current) + len(paragraph) + 2 <= max_chars:
            current = f"{current}\n\n{paragraph}" if current else paragraph
        else:
            if current:
                chunks.append(current)
            if len(paragraph) <= max_chars:
                current = paragraph
            else:
                sentences = _SENTENCE_BOUNDARY.split(paragraph)
                current = ""
                for sentence in sentences:
                    if len(current) + len(sentence) + 1 <= max_chars:
                        current = f"{current} {sentence}" if current else sentence
                    else:
                        if current:
                            chunks.append(current)
                        if len(sentence) > max_chars:
                            for i in range(0, len(sentence), max_chars - overlap):
                                chunks.append(sentence[i : i + max_chars])
                            current = ""
                        else:
                            current = sentence

    if current:
        chunks.append(current)

    # Apply overlap between consecutive chunks
    if overlap > 0 and len(chunks) > 1:
        overlapped = [chunks[0]]
        for i in range(1, len(chunks)):
            prev_tail = chunks[i - 1][-overlap:]
            overlapped.append(prev_tail + " " + chunks[i])
        chunks = overlapped

    return [c.strip() for c in chunks if c.strip()]


# ---------------------------------------------------------------------------
# SQL
# ---------------------------------------------------------------------------

TOTAL_COUNT_SQL = "SELECT count(*) FROM clinical_documents"

PENDING_DOCUMENTS_SQL = """
SELECT
    cd.id,
    cd.practice_id,
    cd.patient_id,
    cd.document_type,
    cd.body,
    cd.source_updated_at
FROM clinical_documents cd
WHERE NOT EXISTS (
    SELECT 1 FROM document_chunks dc
    WHERE dc.document_id = cd.id
      AND dc.source_updated_at = cd.source_updated_at
)
ORDER BY cd.id
"""

DELETE_CHUNKS_SQL = "DELETE FROM document_chunks WHERE document_id = $1"

INSERT_CHUNK_SQL = """
INSERT INTO document_chunks
    (document_id, practice_id, patient_id, document_type,
     chunk_index, content, embedding, source_updated_at)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
ON CONFLICT (document_id, chunk_index)
DO UPDATE SET
    content = EXCLUDED.content,
    embedding = EXCLUDED.embedding,
    source_updated_at = EXCLUDED.source_updated_at
"""


# ---------------------------------------------------------------------------
# Main indexing run
# ---------------------------------------------------------------------------


@dataclass
class _DocChunks:
    doc_id: str
    practice_id: str
    patient_id: str
    document_type: str
    source_updated_at: object
    chunks: list[str]


async def run_indexing(pool: asyncpg.Pool, embedding_client: SupportsEmbedding) -> IndexSummary:
    """Index all new/changed clinical documents."""
    summary = IndexSummary()

    async with pool.acquire() as conn:
        total_in_db = await conn.fetchval(TOTAL_COUNT_SQL)
        rows = await conn.fetch(PENDING_DOCUMENTS_SQL)

    summary.total_documents = total_in_db
    summary.already_indexed = total_in_db - len(rows)
    logger.info(
        "indexing started total=%d already_indexed=%d pending=%d",
        total_in_db,
        summary.already_indexed,
        len(rows),
    )

    if not rows:
        return summary

    # Phase 1: chunk all documents
    doc_chunks_list: list[_DocChunks] = []
    all_texts: list[str] = []
    text_to_doc: list[int] = []  # maps text index -> doc_chunks_list index

    for row in rows:
        body = row["body"]
        if not body or not body.strip():
            summary.skipped += 1
            summary.errors.append(f"{row['id']}: empty body")
            continue

        chunks = chunk_text(body)
        # Truncate any chunk exceeding embedding service limit
        chunks = [c[:MAX_TEXT_CHARS] for c in chunks if c.strip()]

        if not chunks:
            summary.skipped += 1
            summary.errors.append(f"{row['id']}: no valid chunks")
            continue

        dc = _DocChunks(
            doc_id=row["id"],
            practice_id=row["practice_id"],
            patient_id=row["patient_id"],
            document_type=row["document_type"],
            source_updated_at=row["source_updated_at"],
            chunks=chunks,
        )
        doc_idx = len(doc_chunks_list)
        doc_chunks_list.append(dc)

        for chunk in chunks:
            all_texts.append(chunk)
            text_to_doc.append(doc_idx)

    if not all_texts:
        logger.info("no embeddable content found")
        return summary

    # Phase 2: embed all chunks
    logger.info("embedding chunks=%d documents=%d", len(all_texts), len(doc_chunks_list))
    try:
        batch_result = await embedding_client.embed(all_texts)
    except Exception as exc:
        logger.error("embedding failure: %s", type(exc).__name__)
        summary.failed = len(doc_chunks_list)
        summary.errors.append(f"embedding: {type(exc).__name__}")
        return summary

    vectors = batch_result.vectors

    # Phase 3: persist per document (transaction per doc for fault isolation)
    # Build vector slices per document
    doc_vector_ranges: dict[int, list[int]] = {}
    for text_idx, doc_idx in enumerate(text_to_doc):
        doc_vector_ranges.setdefault(doc_idx, []).append(text_idx)

    async with pool.acquire() as conn:
        for doc_idx, dc in enumerate(doc_chunks_list):
            text_indices = doc_vector_ranges[doc_idx]
            try:
                async with conn.transaction():
                    await conn.execute(DELETE_CHUNKS_SQL, dc.doc_id)
                    for chunk_pos, text_idx in enumerate(text_indices):
                        await conn.execute(
                            INSERT_CHUNK_SQL,
                            dc.doc_id,
                            dc.practice_id,
                            dc.patient_id,
                            dc.document_type,
                            chunk_pos,
                            all_texts[text_idx],
                            vectors[text_idx],
                            dc.source_updated_at,
                        )
                summary.indexed += 1
                summary.chunks_created += len(text_indices)
            except Exception as exc:
                summary.failed += 1
                summary.errors.append(f"{dc.doc_id}: {type(exc).__name__}")
                logger.warning("failed document_id=%s error=%s", dc.doc_id, exc)

    logger.info(
        "indexing complete total=%d indexed=%d skipped=%d failed=%d chunks=%d",
        summary.total_documents,
        summary.indexed,
        summary.skipped,
        summary.failed,
        summary.chunks_created,
    )
    return summary
