"""Core semantic search logic shared by the search API and evaluation.

Primary strategy: hybrid search combining vector similarity + BM25 via
Reciprocal Rank Fusion (RRF).
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

# RRF constant: controls how much weight is given to lower-ranked results.
# k=60 is the standard value used in information retrieval literature.
RRF_K = 60

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


def _rrf_fuse(
    vector_rows: list[dict] | None,
    bm25_rows: list[dict] | None,
) -> list[dict]:
    """Fuse two ranked result lists using Reciprocal Rank Fusion.

    Each chunk-level result gets an RRF score:
        RRF_score(chunk) = sum(1 / (k + rank)) across strategies

    Results are then aggregated to patient level by summing RRF scores
    across all chunks belonging to the same patient.

    Returns a list of patient dicts sorted by fused RRF score desc.
    """
    # Map: chunk_key -> {patient_id, rrf_score, best_row}
    chunk_rrf: dict[str, dict] = {}

    for rank, row in enumerate((vector_rows or []), start=1):
        key = row["document_id"]
        if key not in chunk_rrf:
            chunk_rrf[key] = {
                "patient_id": row["patient_id"],
                "rrf_score": 0.0,
                "best": row,
            }
        chunk_rrf[key]["rrf_score"] += 1.0 / (RRF_K + rank)
        # Keep the row with the higher original relevance for snippet
        if row["relevance_score"] > chunk_rrf[key]["best"]["relevance_score"]:
            chunk_rrf[key]["best"] = row

    for rank, row in enumerate((bm25_rows or []), start=1):
        key = row["document_id"]
        if key not in chunk_rrf:
            chunk_rrf[key] = {
                "patient_id": row["patient_id"],
                "rrf_score": 0.0,
                "best": row,
            }
        chunk_rrf[key]["rrf_score"] += 1.0 / (RRF_K + rank)
        if row["relevance_score"] > chunk_rrf[key]["best"]["relevance_score"]:
            chunk_rrf[key]["best"] = row

    if not chunk_rrf:
        return []

    # Aggregate to patient level: sum RRF scores, keep best chunk
    patient_map: dict[str, dict] = {}
    for entry in chunk_rrf.values():
        pid = entry["patient_id"]
        if pid not in patient_map:
            patient_map[pid] = {
                "display_name": entry["best"]["display_name"],
                "rrf_score": entry["rrf_score"],
                "best": entry["best"],
                "doc_ids": {entry["best"]["document_id"]},
            }
        else:
            patient_map[pid]["rrf_score"] += entry["rrf_score"]
            patient_map[pid]["doc_ids"].add(entry["best"]["document_id"])
            if entry["rrf_score"] > patient_map[pid]["rrf_score"]:
                patient_map[pid]["best"] = entry["best"]

    sorted_patients = sorted(
        patient_map.items(),
        key=lambda item: item[1]["rrf_score"],
        reverse=True,
    )

    results = []
    for patient_id, data in sorted_patients:
        best = data["best"]
        results.append(
            {
                "patient_id": patient_id,
                "display_name": data["display_name"],
                "document_id": best["document_id"],
                "document_type": best["document_type"],
                "document_title": best["document_title"],
                "document_date": best["document_date"],
                "snippet": best["content"][:300],
                "relevance_score": round(float(data["rrf_score"]), 6),
                "additional_matching_documents": max(0, len(data["doc_ids"]) - 1),
            }
        )
    return results


async def search_patients(
    conn: asyncpg.Connection,
    embedding_client: SupportsEmbedding,
    query: str,
    practice_id: str,
    doc_types: list[str] | None,
    limit: int,
    embedding_cache: EmbeddingCache | None = None,
) -> tuple[list[dict], bool]:
    """Run hybrid search (vector + BM25) with RRF fusion.

    Primary strategy: run vector similarity and BM25 in parallel, then fuse
    results using Reciprocal Rank Fusion for robust ranking.
    If the embedding service is unavailable, falls back to BM25-only.

    Returns (results, degraded) where results is a list of patient dicts
    sorted by fused relevance score desc.
    """
    degraded = False
    candidate_limit = limit * 5

    # --- Prepare query vector (if possible) ---
    query_vector = None
    try:
        cached_vector = None
        if embedding_cache is not None:
            cached_vector = embedding_cache.get(query)

        if cached_vector is not None:
            query_vector = np.array(cached_vector, dtype=np.float32)
        else:
            batch = await embedding_client.embed([query])
            query_vector = np.array(batch.vectors[0], dtype=np.float32)
            if embedding_cache is not None:
                embedding_cache.put(query, batch.vectors[0])
    except (CircuitOpenError, EmbeddingServiceError) as exc:
        logger.warning(
            "embedding unavailable, BM25-only: %s",
            type(exc).__name__,
        )
        degraded = True

    # --- Run searches ---
    if query_vector is not None:
        # Run vector and BM25 sequentially (single connection cannot do concurrent queries)
        vector_rows_raw = await conn.fetch(
            VECTOR_SEARCH_SQL,
            query_vector,
            practice_id,
            doc_types,
            candidate_limit,
        )
        bm25_rows_raw = await conn.fetch(
            BM25_SEARCH_SQL,
            query,
            practice_id,
            doc_types,
            candidate_limit,
        )
        vector_rows = [dict(r) for r in vector_rows_raw]
        bm25_rows = [dict(r) for r in bm25_rows_raw]
    else:
        # BM25-only fallback
        vector_rows = None
        bm25_rows_raw = await conn.fetch(
            BM25_SEARCH_SQL,
            query,
            practice_id,
            doc_types,
            candidate_limit,
        )
        bm25_rows = [dict(r) for r in bm25_rows_raw]

    if not vector_rows and not bm25_rows:
        return [], degraded

    # --- RRF fusion ---
    fused = _rrf_fuse(vector_rows, bm25_rows)

    return fused[:limit], degraded
