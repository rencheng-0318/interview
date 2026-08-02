"""Indexing workflow: chunk clinical documents and store embeddings."""

import contextlib
import logging
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
# Chunking: Recursive Character Splitting
# ---------------------------------------------------------------------------

# Separator hierarchy: paragraph -> sentence -> word -> character
SEPARATORS = ["\n\n", ". ", " ", ""]


def chunk_text(
    text: str, max_chars: int = MAX_CHUNK_CHARS, overlap: int = OVERLAP_CHARS
) -> list[str]:
    """Split text using recursive character splitting at semantic boundaries."""
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    chunks = _recursive_split(text, max_chars, SEPARATORS)

    # Apply overlap between consecutive chunks
    if overlap > 0 and len(chunks) > 1:
        overlapped = [chunks[0]]
        for i in range(1, len(chunks)):
            prev_tail = chunks[i - 1][-overlap:]
            overlapped.append(prev_tail + " " + chunks[i])
        chunks = overlapped

    return [c.strip() for c in chunks if c.strip()]


def _recursive_split(
    text: str, max_chars: int, separators: list[str]
) -> list[str]:
    """Recursively split text using separator hierarchy."""
    if len(text) <= max_chars:
        return [text]

    for i, sep in enumerate(separators):
        if not sep:
            # Last resort: hard split with overlap
            step = max_chars - OVERLAP_CHARS
            return [text[j : j + max_chars] for j in range(0, len(text), step)]

        parts = text.split(sep)
        chunks: list[str] = []
        current = ""

        for part in parts:
            if not part:
                continue
            candidate = f"{current}{sep}{part}" if current else part
            if len(candidate) <= max_chars:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                if len(part) > max_chars:
                    # Recursively handle oversized parts
                    sub_chunks = _recursive_split(part, max_chars, separators[i + 1 :])
                    chunks.extend(sub_chunks)
                    current = ""
                else:
                    current = part

        if current:
            chunks.append(current)

        if chunks:
            return chunks

    return [text]


# ---------------------------------------------------------------------------
# SQL
# ---------------------------------------------------------------------------

TOTAL_COUNT_SQL = "SELECT count(*) FROM clinical_documents"

PENDING_DOCUMENTS_SQL_NO_LIMIT = """
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

PENDING_DOCUMENTS_SQL_WITH_LIMIT = """
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
LIMIT $1
"""

DELETE_CHUNKS_SQL = "DELETE FROM document_chunks WHERE document_id = $1"

INSERT_CHUNK_SQL = """
INSERT INTO document_chunks
    (document_id, practice_id, patient_id, document_type,
     chunk_index, content, embedding, source_updated_at, content_tsv)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, to_tsvector('english', $6))
ON CONFLICT (document_id, chunk_index)
DO UPDATE SET
    content = EXCLUDED.content,
    embedding = EXCLUDED.embedding,
    source_updated_at = EXCLUDED.source_updated_at,
    content_tsv = to_tsvector('english', EXCLUDED.content)
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


async def run_indexing(
    pool: asyncpg.Pool, 
    embedding_client: SupportsEmbedding,
    max_documents: int | None = None
) -> IndexSummary:
    """Index all new/changed clinical documents.
    
    Args:
        pool: Database connection pool
        embedding_client: Embedding service client
        max_documents: If set, only index up to this many pending documents (for testing)
    """
    summary = IndexSummary()

    async with pool.acquire() as conn:
        total_in_db = await conn.fetchval(TOTAL_COUNT_SQL)
        if max_documents is not None:
            rows = await conn.fetch(PENDING_DOCUMENTS_SQL_WITH_LIMIT, max_documents)
        else:
            rows = await conn.fetch(PENDING_DOCUMENTS_SQL_NO_LIMIT)

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

    # Phase 2: embed per document (failure isolation: one doc failure doesn't block others)
    logger.info("embedding chunks=%d documents=%d", len(all_texts), len(doc_chunks_list))

    # Build text slices per document
    doc_text_ranges: dict[int, list[int]] = {}
    for text_idx, doc_idx in enumerate(text_to_doc):
        doc_text_ranges.setdefault(doc_idx, []).append(text_idx)

    # Embed each document's chunks independently (serial to avoid overwhelming embedding service)
    doc_vectors: dict[int, list[list[float]]] = {}
    for doc_idx, dc in enumerate(doc_chunks_list):
        text_indices = doc_text_ranges[doc_idx]
        doc_chunks_text = [all_texts[i] for i in text_indices]
        try:
            batch_result = await embedding_client.embed(doc_chunks_text)
            doc_vectors[doc_idx] = batch_result.vectors
        except Exception as exc:
            summary.failed += 1
            summary.errors.append(f"{dc.doc_id}: embed {type(exc).__name__}")
            logger.warning("embedding failed document_id=%s error=%s", dc.doc_id, exc)

    # Phase 3: persist per document (transaction per doc for fault isolation)
    logger.info("persisting chunks to database...")
    async with pool.acquire() as conn:
        for doc_idx, dc in enumerate(doc_chunks_list):
            if doc_idx not in doc_vectors:
                # Embedding failed for this doc; clean up any partial chunks
                try:
                    await conn.execute(DELETE_CHUNKS_SQL, dc.doc_id)
                except Exception as cleanup_exc:
                    logger.warning(
                        "cleanup failed document_id=%s error=%s",
                        dc.doc_id,
                        cleanup_exc,
                    )
                continue

            vectors = doc_vectors[doc_idx]
            text_indices = doc_text_ranges[doc_idx]
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
                            vectors[chunk_pos],
                            dc.source_updated_at,
                        )
                summary.indexed += 1
                summary.chunks_created += len(text_indices)
            except Exception as exc:
                # Write failed; clean up partial data so next run can retry
                with contextlib.suppress(Exception):
                    await conn.execute(DELETE_CHUNKS_SQL, dc.doc_id)
                summary.failed += 1
                summary.errors.append(f"{dc.doc_id}: write {type(exc).__name__}")
                logger.warning("write failed document_id=%s error=%s", dc.doc_id, exc)

    logger.info(
        "indexing complete total=%d indexed=%d skipped=%d failed=%d chunks=%d",
        summary.total_documents,
        summary.indexed,
        summary.skipped,
        summary.failed,
        summary.chunks_created,
    )
    return summary
