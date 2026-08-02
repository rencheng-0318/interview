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
from app.features.search.service import VECTOR_SEARCH_SQL, BM25_SEARCH_SQL, _aggregate_patients, DEFAULT_CANDIDATE_MULTIPLIER, MAX_CANDIDATE_LIMIT

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
    if limit < 1:
        raise ValidationError("limit must be at least 1.")
    if limit > settings.search_max_limit:
        raise ValidationError(f"limit must be at most {settings.search_max_limit}.")

    # --- Get or create embedding (with caching) ---
    query_vector = None
    degraded = False
    try:
        cached_vector = None
        if embedding_cache is not None:
            cached_vector = embedding_cache.get(query)

        if cached_vector is not None:
            # Cache hit - use cached vector directly
            query_vector = cached_vector
        else:
            # Cache miss - call embedding service
            batch = await embedding_client.embed([query])
            query_vector = batch.vectors[0]
            if embedding_cache is not None:
                embedding_cache.put(query, query_vector)
    except Exception as exc:
        logger.warning(
            "embedding unavailable, BM25-only fallback: %s",
            type(exc).__name__,
        )
        degraded = True

    # --- Vector retrieval + patient aggregation ---
    doc_types = payload.document_types if payload.document_types else None
    
    # Dynamic candidate limit based on dataset statistics (avg 3.36 docs/patient)
    candidate_limit = min(limit * DEFAULT_CANDIDATE_MULTIPLIER, MAX_CANDIDATE_LIMIT)
    
    async with pool.acquire() as conn:
        if query_vector is not None:
            rows_raw = await conn.fetch(
                VECTOR_SEARCH_SQL,
                query_vector,
                context.practice_id,
                doc_types,
                candidate_limit,
            )
        else:
            # BM25-only fallback when embedding service is unavailable
            rows_raw = await conn.fetch(
                BM25_SEARCH_SQL,
                query,
                context.practice_id,
                doc_types,
                candidate_limit,
            )
        
        patient_results = _aggregate_patients([dict(r) for r in rows_raw])
        patient_results = patient_results[:limit]

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


# Extract natural 2-3 word phrases (bigrams/trigrams) from document chunks.
# Optimized with WHERE clause to filter relevant content early.
SUGGESTIONS_SQL = """
WITH base AS (
    SELECT
        regexp_replace(
            regexp_replace(LOWER(LEFT(content, 600)), '[^a-z0-9\\s]', ' ', 'g'),
            '\\s+', ' ', 'g'
        ) AS text
    FROM document_chunks
    WHERE practice_id = $1
      AND LENGTH(content) > 10  -- Quick filter: skip very short content
),
words AS (
    SELECT
        trim(unnest(string_to_array(text, ' '))) AS word,
        generate_subscripts(string_to_array(text, ' '), 1) AS pos
    FROM base
    WHERE POSITION(' ' IN text) > 0  -- Only process text with spaces
),
bigrams AS (
    SELECT w1.word || ' ' || w2.word AS phrase
    FROM words w1
    JOIN words w2 ON w2.pos = w1.pos + 1
    WHERE LENGTH(w1.word) > 1 AND LENGTH(w2.word) > 2
      AND w1.word NOT IN ('the', 'and', 'for', 'are', 'was', 'has', 'had', 'not',
                          'that', 'this', 'with', 'from', 'have', 'were', 'been',
                          'will', 'would', 'could', 'should', 'their', 'there',
                          'which', 'when', 'where', 'what', 'than', 'then',
                          'patient', 'patients', 'history', 'report')
      AND w2.word NOT IN ('the', 'and', 'for', 'are', 'was', 'has', 'had', 'not')
),
trigrams AS (
    SELECT w1.word || ' ' || w2.word || ' ' || w3.word AS phrase
    FROM words w1
    JOIN words w2 ON w2.pos = w1.pos + 1
    JOIN words w3 ON w3.pos = w2.pos + 1
    WHERE LENGTH(w1.word) > 1 AND LENGTH(w3.word) > 2
      AND w1.word NOT IN ('the', 'and', 'for', 'are', 'was', 'has', 'had', 'not',
                          'that', 'this', 'with', 'from', 'have', 'were', 'been',
                          'will', 'would', 'could', 'should', 'their', 'there',
                          'patient', 'patients', 'history', 'report')
      AND w3.word NOT IN ('the', 'and', 'for', 'are', 'was', 'has', 'had', 'not')
),
all_phrases AS (
    SELECT phrase FROM bigrams
    UNION
    SELECT phrase FROM trigrams
),
filtered AS (
    SELECT phrase, LENGTH(phrase) AS len
    FROM all_phrases
    WHERE LENGTH(phrase) BETWEEN 8 AND 50
      AND ($2::text IS NULL OR phrase LIKE $2 || '%')
)
SELECT phrase FROM filtered
ORDER BY len, phrase
LIMIT 30
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
    """Return search suggestions based on synonyms and common medical terms.
    
    Uses synonym mapping to suggest related medical terminology.
    For example, input 'head' will suggest 'headache', 'migraine', 'tension headache'.
    """
    query = q.strip().lower()[:50]  # Limit query length
    
    # Synonym mapping for common clinical terms
    # Keys are root words/phrases, values are lists of related terms
    SYNONYM_MAP: dict[str, list[str]] = {
        'head': ['headache', 'migraine', 'tension headache', 'dizziness', 'vertigo'],
        'chest': ['chest pain', 'angina', 'tightness', 'pressure', 'palpitations'],
        'pain': ['aching', 'soreness', 'discomfort', 'sharp pain', 'dull ache'],
        'fever': ['febrile', 'high temperature', 'pyrexia', 'chills', 'hyperthermia'],
        'blood': ['blood pressure', 'hypertension', 'bleeding', 'hemorrhage', 'anemia'],
        'breath': ['shortness of breath', 'dyspnea', 'wheezing', 'difficulty breathing'],
        'nausea': ['vomiting', 'stomach upset', 'gastrointestinal', 'queasy'],
        'fatigue': ['tiredness', 'exhaustion', 'weakness', 'malaise', 'lethargy'],
        'swelling': ['edema', 'inflammation', 'swollen', 'effusion', 'distension'],
        'cough': ['persistent cough', 'dry cough', 'productive cough', 'chronic cough'],
    }
    
    if not query:
        # Return top-level categories as default suggestions
        suggestions = [
            "headache", "migraine", "chest pain", "fever", "fatigue",
            "shortness of breath", "blood pressure", "nausea", "swelling", "cough"
        ]
    else:
        # Find matching synonym group (exact prefix match first)
        suggestions = []
        matched_key = None
        
        for key, synonyms in SYNONYM_MAP.items():
            # Check if query is a prefix of the key
            if key.startswith(query):
                matched_key = key
                suggestions.extend(synonyms)
                break
        
        # If no key match, check if query matches any synonym
        if not suggestions:
            for key, synonyms in SYNONYM_MAP.items():
                for term in synonyms:
                    if term.startswith(query):
                        # Found a matching synonym - add its entire synonym group
                        suggestions.extend(SYNONYM_MAP[key])
                        # Also add the matching term itself if not already included
                        if term not in suggestions:
                            suggestions.append(term)
                        break
                if suggestions:
                    break
        
        # Remove duplicates while preserving order
        seen = set()
        unique_suggestions = []
        for s in suggestions:
            if s.lower() not in seen:
                seen.add(s.lower())
                unique_suggestions.append(s)
        suggestions = unique_suggestions

    return SearchSuggestionsResponse(
        query=query,
        suggestions=suggestions[:20],  # Limit to 20 suggestions
    )
