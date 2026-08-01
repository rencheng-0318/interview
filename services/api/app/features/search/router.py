import logging
import time
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.clients.embedding import SupportsEmbedding
from app.config import get_settings
from app.context import CurrentContext, PoolDep
from app.errors import ErrorResponse, ValidationError
from app.features.search.schemas import (
    BestMatch,
    ClinicalSearchRequest,
    ClinicalSearchResponse,
    PatientSummary,
    SearchMeta,
    SearchResult,
)
from app.features.search.service import search_patients

logger = logging.getLogger("api.search")

router = APIRouter(prefix="/api", tags=["search"])


def get_embedding_client(request: Request) -> SupportsEmbedding:
    return request.app.state.embedding_client


EmbeddingDep = Annotated[SupportsEmbedding, Depends(get_embedding_client)]


@router.post(
    "/clinical-search",
    response_model=ClinicalSearchResponse,
    responses={
        422: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
async def clinical_search(
    payload: ClinicalSearchRequest,
    pool: PoolDep,
    context: CurrentContext,
    embedding_client: EmbeddingDep,
) -> ClinicalSearchResponse:
    settings = get_settings()
    started = time.perf_counter()

    # --- Validate request ---
    query = payload.query.strip()
    if not query:
        raise ValidationError("query must not be empty or whitespace only.")
    if len(query) > settings.search_max_query_length:
        raise ValidationError(
            f"query must be at most {settings.search_max_query_length} characters."
        )

    limit = payload.limit if payload.limit is not None else settings.search_default_limit
    if limit > settings.search_max_limit:
        raise ValidationError(f"limit must be at most {settings.search_max_limit}.")

    # --- Vector retrieval + patient aggregation ---
    doc_types = payload.document_types if payload.document_types else None
    async with pool.acquire() as conn:
        patient_results = await search_patients(
            conn, embedding_client, query, context.practice_id, doc_types, limit
        )

    results = [
        SearchResult(
            patient=PatientSummary(id=r["patient_id"], display_name=r["display_name"]),
            best_match=BestMatch(
                document_id=r["document_id"],
                document_type=r["document_type"],
                document_title=r["document_title"],
                document_date=r["document_date"],
                snippet=r["snippet"],
                relevance_score=r["relevance_score"],
            ),
            additional_matching_documents=r["additional_matching_documents"],
        )
        for r in patient_results
    ]

    took_ms = int((time.perf_counter() - started) * 1000)

    return ClinicalSearchResponse(
        query=payload.query,
        results=results,
        meta=SearchMeta(result_count=len(results), took_ms=took_ms),
    )
