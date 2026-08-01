import logging
import time
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.clients.embedding import SupportsEmbedding
from app.clients.embedding_cache import EmbeddingCache
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
    SearchSuggestionsResponse,
)
from app.features.search.service import search_patients

logger = logging.getLogger("api.search")

router = APIRouter(prefix="/api", tags=["search"])


def get_embedding_client(request: Request) -> SupportsEmbedding:
    return request.app.state.embedding_client


def get_embedding_cache(request: Request) -> EmbeddingCache | None:
    return getattr(request.app.state, "embedding_cache", None)


EmbeddingDep = Annotated[SupportsEmbedding, Depends(get_embedding_client)]
EmbeddingCacheDep = Annotated[EmbeddingCache | None, Depends(get_embedding_cache)]


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
    embedding_cache: EmbeddingCacheDep,
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
        patient_results, degraded = await search_patients(
            conn,
            embedding_client,
            query,
            context.practice_id,
            doc_types,
            limit,
            embedding_cache=embedding_cache,
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
        meta=SearchMeta(result_count=len(results), took_ms=took_ms, degraded=degraded),
    )


# SQL to extract common phrases from document chunks for suggestions
# Returns terms that start with or contain the query prefix
SUGGESTIONS_SQL = """
WITH terms AS (
    SELECT DISTINCT unnest(string_to_array(
        regexp_replace(
            regexp_replace(LOWER(LEFT(content, 500)),
            '[^a-z0-9\\s]', ' ', 'g'),
        '\\s+', ' ', 'g')
    , ' ')) AS term
    FROM document_chunks
    WHERE practice_id = $1
      AND ($2::text IS NULL OR content ILIKE '%' || $2 || '%')
),
filtered AS (
    SELECT DISTINCT term,
           LENGTH(term) AS len,
           CASE WHEN term LIKE $2 || '%' THEN 0 ELSE 1 END AS priority
    FROM terms
    WHERE LENGTH(term) > 3
      AND ($2::text IS NULL OR term LIKE $2 || '%' OR term LIKE '%' || $2 || '%')
      AND term NOT IN ('that', 'this', 'with', 'from', 'have', 'were', 'been',
                       'will', 'would', 'could', 'should', 'their', 'there',
                       'which', 'when', 'where', 'what', 'than', 'then')
)
SELECT term FROM filtered
WHERE len <= 30
ORDER BY priority, term
LIMIT 50
"""


@router.get(
    "/search/suggestions",
    response_model=SearchSuggestionsResponse,
    responses={422: {"model": ErrorResponse}},
)
async def search_suggestions(
    pool: PoolDep,
    context: CurrentContext,
    q: str = "",
) -> SearchSuggestionsResponse:
    """Return search suggestions based on document content.

    Extracts common terms from documents that match the query prefix.
    Helps users discover relevant medical terminology.
    """
    query = q.strip().lower()[:50]  # Limit query length

    async with pool.acquire() as conn:
        rows = await conn.fetch(SUGGESTIONS_SQL, context.practice_id, query if query else None)

    suggestions = [row["term"] for row in rows]

    # If we have a query, prioritize terms that start with the query
    if query:
        suggestions.sort(key=lambda s: (not s.startswith(query), s))

    return SearchSuggestionsResponse(
        query=query,
        suggestions=suggestions[:20],  # Limit to 20 suggestions
    )
