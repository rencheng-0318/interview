"""Core semantic search logic shared by the search API and evaluation."""

import asyncpg
import numpy as np

from app.clients.embedding import SupportsEmbedding

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


async def search_patients(
    conn: asyncpg.Connection,
    embedding_client: SupportsEmbedding,
    query: str,
    practice_id: str,
    doc_types: list[str] | None,
    limit: int,
) -> list[dict]:
    """Run vector search and aggregate to patient level.

    Returns a list of patient dicts sorted by best relevance score desc.
    """
    await conn.execute("SET ivfflat.probes = 50")

    batch = await embedding_client.embed([query])
    query_vector = np.array(batch.vectors[0], dtype=np.float32)

    candidate_limit = limit * 5
    rows = await conn.fetch(
        VECTOR_SEARCH_SQL,
        query_vector,
        practice_id,
        doc_types,
        candidate_limit,
    )

    patient_map: dict[str, dict] = {}
    for row in rows:
        pid = row["patient_id"]
        if pid not in patient_map:
            patient_map[pid] = {
                "display_name": row["display_name"],
                "best": row,
                "doc_ids": {row["document_id"]},
            }
        else:
            patient_map[pid]["doc_ids"].add(row["document_id"])
            if row["relevance_score"] > patient_map[pid]["best"]["relevance_score"]:
                patient_map[pid]["best"] = row

    sorted_patients = sorted(
        patient_map.items(),
        key=lambda item: item[1]["best"]["relevance_score"],
        reverse=True,
    )[:limit]

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
                "relevance_score": round(float(best["relevance_score"]), 4),
                "additional_matching_documents": max(0, len(data["doc_ids"]) - 1),
            }
        )
    return results
