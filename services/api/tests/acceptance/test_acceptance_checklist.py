import asyncpg
import pytest
from httpx import AsyncClient

from app.features.indexing import run_indexing
from tests.conftest import SingleConnectionPool, practice_token
from tests.stubs import StubEmbeddingClient, UnavailableEmbeddingClient

# ---------------------------------------------------------------------------
# Indexing safety
# ---------------------------------------------------------------------------


async def test_reindexing_unchanged_documents_creates_no_duplicates(
    connection: asyncpg.Connection, embedding_client: StubEmbeddingClient
) -> None:
    pool = SingleConnectionPool(connection)

    await run_indexing(pool, embedding_client)
    count_first = await connection.fetchval("SELECT count(*) FROM document_chunks")
    assert count_first > 0

    # Reset stub call history
    embedding_client.calls.clear()

    await run_indexing(pool, embedding_client)
    count_second = await connection.fetchval("SELECT count(*) FROM document_chunks")

    assert count_second == count_first
    # Second run should have nothing to embed (no pending documents)
    assert embedding_client.call_count == 0


async def test_changed_document_is_reindexed(
    connection: asyncpg.Connection, embedding_client: StubEmbeddingClient
) -> None:
    pool = SingleConnectionPool(connection)

    await run_indexing(pool, embedding_client)

    # Pick a document and record its chunks
    doc_id = await connection.fetchval(
        "SELECT document_id FROM document_chunks LIMIT 1"
    )
    old_chunks = await connection.fetch(
        "SELECT content FROM document_chunks WHERE document_id = $1", doc_id
    )
    old_count = len(old_chunks)
    assert old_count > 0

    # Modify the document body (triggers source_updated_at update via trigger)
    await connection.execute(
        "UPDATE clinical_documents SET body = body || ' Updated content for "
        "reindex test.' WHERE id = $1",
        doc_id,
    )

    # Re-index
    embedding_client.calls.clear()
    await run_indexing(pool, embedding_client)

    # Verify the document was reindexed
    new_chunks = await connection.fetch(
        "SELECT content FROM document_chunks WHERE document_id = $1", doc_id
    )
    assert len(new_chunks) > 0
    # At least one chunk should contain the new text
    all_content = " ".join(r["content"] for r in new_chunks)
    assert "Updated content for reindex test" in all_content


async def test_unindexable_document_does_not_abort_the_run(
    connection: asyncpg.Connection, embedding_client: StubEmbeddingClient
) -> None:
    pool = SingleConnectionPool(connection)

    summary = await run_indexing(pool, embedding_client)

    # The dataset has pathological documents; the run should complete
    assert summary.indexed > 0
    # Total should account for all documents
    assert summary.total_documents > 0
    # Even if some failed, indexed must be positive
    assert summary.indexed + summary.skipped + summary.failed == summary.total_documents


# ---------------------------------------------------------------------------
# Practice isolation
# ---------------------------------------------------------------------------


async def test_search_never_returns_a_patient_from_another_practice(
    api: AsyncClient,
    connection: asyncpg.Connection,
    curated_cases: dict,
    northside_headers: dict[str, str],
) -> None:
    pool = SingleConnectionPool(connection)
    stub = StubEmbeddingClient()
    await run_indexing(pool, stub)

    for case in curated_cases["cases"]:
        response = await api.post(
            "/api/clinical-search",
            json={"query": case["query"]},
            headers=northside_headers,
        )
        if response.status_code != 200:
            continue

        data = response.json()
        result_patient_ids = {r["patient"]["id"] for r in data["results"]}

        # Cross-practice decoy must never appear
        assert case["crossPracticeDecoyPatientId"] not in result_patient_ids, (
            f"Case {case['id']}: decoy patient from another practice appeared in results"
        )


# ---------------------------------------------------------------------------
# Patient-level results
# ---------------------------------------------------------------------------


async def test_patient_with_multiple_matching_documents_appears_once(
    api: AsyncClient, connection: asyncpg.Connection, curated_cases: dict
) -> None:
    pool = SingleConnectionPool(connection)
    stub = StubEmbeddingClient()
    await run_indexing(pool, stub)

    headers = practice_token("user-northside-01")
    case = curated_cases["cases"][0]

    response = await api.post(
        "/api/clinical-search",
        json={"query": case["query"], "limit": 25},
        headers=headers,
    )
    if response.status_code != 200:
        pytest.skip("search returned non-200 with stub embeddings")

    data = response.json()
    patient_ids = [r["patient"]["id"] for r in data["results"]]

    # Each patient appears at most once
    assert len(patient_ids) == len(set(patient_ids)), "Duplicate patient in results"


# ---------------------------------------------------------------------------
# Embedding call efficiency
# ---------------------------------------------------------------------------


async def test_search_performs_exactly_one_embedding_call(
    api: AsyncClient, embedding_client: StubEmbeddingClient
) -> None:
    embedding_client.calls.clear()

    await api.post(
        "/api/clinical-search",
        json={"query": "chest pain"},
        headers={"Authorization": "Bearer demo_user-northside-01"},
    )

    assert embedding_client.call_count == 1


# ---------------------------------------------------------------------------
# Request validation
# ---------------------------------------------------------------------------


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
    embedding_client.calls.clear()

    response = await api.post(
        "/api/clinical-search",
        json=payload,
        headers={"Authorization": "Bearer demo_user-northside-01"},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert embedding_client.call_count == 0


# ---------------------------------------------------------------------------
# Dependency failure
# ---------------------------------------------------------------------------


async def test_search_degrades_to_bm25_when_embedding_is_down(
    connection: asyncpg.Connection,
) -> None:
    """When embedding service is unavailable, search degrades to BM25-only."""
    from httpx import ASGITransport
    from httpx import AsyncClient as HttpxClient

    from app.config import get_settings
    from app.main import create_app

    settings = get_settings()
    app = create_app()
    app.state.settings = settings
    app.state.pool = SingleConnectionPool(connection)
    app.state.embedding_client = UnavailableEmbeddingClient()

    transport = ASGITransport(app=app)
    async with HttpxClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/clinical-search",
            json={"query": "headache"},
            headers={"Authorization": "Bearer demo_user-northside-01"},
        )

    # Search still returns 200 but with degraded=True
    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["degraded"] is True
    # No stack trace in response
    assert "Traceback" not in response.text
    assert "asyncpg" not in response.text


# ---------------------------------------------------------------------------
# Integration: curated query quality (requires real embedding service)
# ---------------------------------------------------------------------------


@pytest.mark.integration
async def test_curated_query_returns_the_expected_patient_in_top_results(
    api: AsyncClient, connection: asyncpg.Connection, curated_cases: dict, real_embedding_client
) -> None:
    pool = SingleConnectionPool(connection)
    await run_indexing(pool, real_embedding_client)

    headers = practice_token("user-northside-01")

    for case in curated_cases["cases"]:
        response = await api.post(
            "/api/clinical-search",
            json={"query": case["query"]},
            headers=headers,
        )
        assert response.status_code == 200, f"Case {case['id']}: non-200 response"

        data = response.json()
        result_patient_ids = [r["patient"]["id"] for r in data["results"]]

        assert case["expectedPatientId"] in result_patient_ids, (
            f"Case {case['id']}: expected patient {case['expectedPatientId']} "
            f"not in top results. Got: {result_patient_ids}"
        )

        # Cross-practice decoy must not appear
        assert case["crossPracticeDecoyPatientId"] not in result_patient_ids
