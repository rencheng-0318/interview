import asyncpg
import pytest
from httpx import AsyncClient

from tests.stubs import StubEmbeddingClient, UnavailableEmbeddingClient

TODO = "candidate: implement"


@pytest.mark.xfail(reason=TODO, strict=False)
async def test_reindexing_unchanged_documents_creates_no_duplicates(
    connection: asyncpg.Connection, embedding_client: StubEmbeddingClient
) -> None:
    raise NotImplementedError(
        "Run the indexing workflow twice over the same data and assert the chunk count "
        "is identical after the second run."
    )


@pytest.mark.xfail(reason=TODO, strict=False)
async def test_changed_document_is_reindexed(
    connection: asyncpg.Connection, embedding_client: StubEmbeddingClient
) -> None:
    raise NotImplementedError(
        "Index, UPDATE a document body, re-index, then assert the stale chunks are gone "
        "and the replacements reflect the new text."
    )


@pytest.mark.xfail(reason=TODO, strict=False)
async def test_unindexable_document_does_not_abort_the_run(
    connection: asyncpg.Connection, embedding_client: StubEmbeddingClient
) -> None:
    raise NotImplementedError(
        "Index the full seed set and assert the run completes, reports the unindexable "
        "documents as failed, and still indexed everything else."
    )


@pytest.mark.xfail(reason=TODO, strict=False)
async def test_search_never_returns_a_patient_from_another_practice(
    api: AsyncClient,
    connection: asyncpg.Connection,
    curated_cases: dict,
    northside_headers: dict[str, str],
) -> None:
    raise NotImplementedError(
        "For each curated case, search as northside and assert "
        "crossPracticeDecoyPatientId is absent from the results."
    )


@pytest.mark.xfail(reason=TODO, strict=False)
async def test_patient_with_multiple_matching_documents_appears_once(
    api: AsyncClient, connection: asyncpg.Connection, curated_cases: dict
) -> None:
    raise NotImplementedError(
        "Search a curated query and assert the returned patient ids are unique, with "
        "additionalMatchingDocuments reflecting the extra evidence."
    )


@pytest.mark.xfail(reason=TODO, strict=False)
async def test_search_performs_exactly_one_embedding_call(
    api: AsyncClient, embedding_client: StubEmbeddingClient
) -> None:
    raise NotImplementedError(
        "Assert embedding_client.call_count == 1 after a single search request."
    )


@pytest.mark.xfail(reason=TODO, strict=False)
@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({"query": ""}, id="empty"),
        pytest.param({"query": "   \t "}, id="whitespace-only"),
        pytest.param({"query": "x" * 5000}, id="over-max-length"),
        pytest.param({"query": "chest pain", "documentTypes": ["not_a_type"]}, id="bad-type"),
        pytest.param({"query": "chest pain", "limit": 10_000}, id="limit-too-large"),
    ],
)
async def test_invalid_requests_are_rejected_without_embedding(
    api: AsyncClient, embedding_client: StubEmbeddingClient, payload: dict
) -> None:
    raise NotImplementedError(
        "Assert a 422 with the validation_error code and embedding_client.call_count == 0."
    )


@pytest.mark.xfail(reason=TODO, strict=False)
async def test_search_reports_service_unavailable_when_embedding_is_down(
    connection: asyncpg.Connection,
) -> None:
    raise NotImplementedError(
        f"Build the app with {UnavailableEmbeddingClient.__name__} and assert a 503 whose "
        "body contains no stack trace."
    )


@pytest.mark.xfail(reason=TODO, strict=False)
@pytest.mark.integration
async def test_curated_query_returns_the_expected_patient_in_top_results(
    api: AsyncClient, connection: asyncpg.Connection, curated_cases: dict, real_embedding_client
) -> None:
    raise NotImplementedError(
        "Index with the real embedder, then assert every case's expectedPatientId appears "
        "within the default result limit."
    )
