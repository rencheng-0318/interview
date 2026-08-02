"""Core semantic search logic shared by the search API and evaluation.

Primary strategy: vector similarity search via pgvector.
Degradation: falls back to BM25-only when embedding service is unavailable.
"""

import logging

import asyncpg
import numpy as np

from app.clients.circuit_breaker import CircuitOpenError
from app.clients.embedding import SupportsEmbedding
from app.clients.embedding_cache import EmbeddingCache
from app.errors import EmbeddingServiceError

logger = logging.getLogger("api.search.service")

# Vector similarity search using HNSW index
VECTOR_SEARCH_SQL = """
SELECT
    dc.patient_id,
    p.first_name || ' ' || p.last_name AS display_name,
    dc.document_id,
    dc.document_type,
    cd.title AS document_title,
    cd.document_date,
    dc.content,
    1 - (dc.embedding <=> $1::vector) AS relevance_score
FROM document_chunks dc
JOIN patients p ON p.id = dc.patient_id
JOIN clinical_documents cd ON cd.id = dc.document_id
WHERE dc.practice_id = $2
  AND ($3::document_type[] IS NULL OR dc.document_type = ANY($3))
ORDER BY dc.embedding <=> $1::vector
LIMIT $4
"""

# BM25 full-text search using precomputed tsvector column with GIN index
# Uses plainto_tsquery for natural language query parsing
BM25_SEARCH_SQL = """
SELECT
    dc.patient_id,
    p.first_name || ' ' || p.last_name AS display_name,
    dc.document_id,
    dc.document_type,
    cd.title AS document_title,
    cd.document_date,
    dc.content,
    ts_rank(dc.content_tsv, plainto_tsquery('english', $1)) AS relevance_score
FROM document_chunks dc
JOIN patients p ON p.id = dc.patient_id
JOIN clinical_documents cd ON cd.id = dc.document_id
WHERE dc.content_tsv @@ plainto_tsquery('english', $1)
  AND dc.practice_id = $2
  AND ($3::document_type[] IS NULL OR dc.document_type = ANY($3))
ORDER BY relevance_score DESC
LIMIT $4
"""

# --- Constants ---
# Candidate retrieval multiplier (based on dataset statistics)
# Average 3.36 docs per patient, P95=6, max=6
# Multiplier of 3 provides adequate coverage for limit=10 (30 candidates → ~9 patients)
# Capped at 100 to reduce database query load
DEFAULT_CANDIDATE_MULTIPLIER = 3
MAX_CANDIDATE_LIMIT = 100


def make_snippet(content: str, max_length: int = 300) -> str:
    """Truncate content to max_length at word boundary with ellipsis."""
    if len(content) <= max_length:
        return content
    truncated = content[:max_length].rsplit(" ", 1)[0]
    return truncated + " ..."


def _aggregate_patients(rows: list[dict]) -> list[dict]:
    """Aggregate chunk-level results to patient level (one row per patient).

    Groups chunks by patient_id, keeps the highest raw score as the best match,
    counts additional matching documents, and sorts by relevance score descending.
    Optimized for performance with minimal dictionary operations.
    """
    patient_map: dict[str, dict] = {}
    
    for row in rows:
        pid = row["patient_id"]
        # Extract once to avoid repeated dict lookups
        score = float(row["relevance_score"])
        if score > patient_map.get(pid, {}).get("relevance_score", -1.0):
            # Only update when we find a higher score
            if pid not in patient_map:
                # First time seeing this patient - create full dict
                patient_map[pid] = {
                    "patient_id": pid,
                    "display_name": row["display_name"],
                    "document_id": row["document_id"],
                    "document_type": row["document_type"],
                    "document_title": row["document_title"],
                    "document_date": row["document_date"],
                    "snippet": make_snippet(row["content"]),
                    "relevance_score": score,
                    "_doc_ids": {row["document_id"]},
                }
            else:
                # Update best match and track document
                pm = patient_map[pid]
                pm["_doc_ids"].add(row["document_id"])
                pm["relevance_score"] = score
                pm["document_id"] = row["document_id"]
                pm["document_type"] = row["document_type"]
                pm["document_title"] = row["document_title"]
                pm["document_date"] = row["document_date"]
                pm["snippet"] = make_snippet(row["content"])

    # Build final results without additional sorting overhead
    results = []
    for data in patient_map.values():
        doc_count = len(data.pop("_doc_ids"))
        results.append({
            "patient_id": data["patient_id"],
            "display_name": data["display_name"],
            "document_id": data["document_id"],
            "document_type": data["document_type"],
            "document_title": data["document_title"],
            "document_date": data["document_date"],
            "snippet": data["snippet"],
            "relevance_score": round(data["relevance_score"], 6),
            "additional_matching_documents": max(0, doc_count - 1),
        })

    results.sort(key=lambda r: r["relevance_score"], reverse=True)
    return results


async def search_patients(
    conn: asyncpg.Connection,
    embedding_client: SupportsEmbedding | None,
    query: str,
    practice_id: str,
    doc_types: list[str] | None,
    limit: int,
    query_vector: list[float] | None = None,
) -> tuple[list[dict], bool]:
    """Run vector-first search with BM25 degradation fallback.

    Primary strategy: vector similarity search via pgvector HNSW index.
    If the embedding service is unavailable, falls back to BM25-only.

    Args:
        conn: Database connection
        embedding_client: Embedding client (only used if query_vector is None)
        query: Search query text
        practice_id: Practice ID for isolation
        doc_types: Optional document type filter
        limit: Target result limit
        query_vector: Pre-computed query embedding (if None, uses embedding_client)

    Returns (results, degraded) where results is a list of patient dicts
    sorted by relevance score desc.
    """
    degraded = False
    # Dynamic candidate limit based on dataset statistics (avg 3.36 docs/patient)
    candidate_limit = min(limit * DEFAULT_CANDIDATE_MULTIPLIER, MAX_CANDIDATE_LIMIT)

    # --- Run search ---
    if query_vector is not None:
        rows_raw = await conn.fetch(
            VECTOR_SEARCH_SQL,
            query_vector,
            practice_id,
            doc_types,
            candidate_limit,
        )
    else:
        # Try to get embedding
        try:
            batch = await embedding_client.embed([query])
            query_vector = batch.vectors[0]
            rows_raw = await conn.fetch(
                VECTOR_SEARCH_SQL,
                query_vector,
                practice_id,
                doc_types,
                candidate_limit,
            )
        except (CircuitOpenError, EmbeddingServiceError) as exc:
            logger.warning(
                "embedding unavailable, BM25-only fallback: %s",
                type(exc).__name__,
            )
            degraded = True
            rows_raw = await conn.fetch(
                BM25_SEARCH_SQL,
                query,
                practice_id,
                doc_types,
                candidate_limit,
            )

    rows = [dict(r) for r in rows_raw]
    if not rows:
        return [], degraded

    # --- Patient-level aggregation ---
    aggregated = _aggregate_patients(rows)

    return aggregated[:limit], degraded
