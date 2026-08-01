import pytest

from app.clients.embedding import EmbeddingInputRejected, split_batches
from tests.stubs import DIMENSIONS, StubEmbeddingClient, deterministic_vector


def test_stub_vectors_are_unit_length_and_correctly_sized() -> None:
    vector = deterministic_vector("recurrent headaches with visual aura")

    assert len(vector) == DIMENSIONS
    assert abs(sum(value * value for value in vector) - 1.0) < 1e-9


def test_stub_vectors_are_stable_across_calls() -> None:
    assert deterministic_vector("same text") == deterministic_vector("same text")
    assert deterministic_vector("one") != deterministic_vector("two")


def test_batches_are_split_to_the_configured_maximum() -> None:
    batches = split_batches([f"text-{index}" for index in range(150)], max_batch_size=64)

    assert [len(batch) for batch in batches] == [64, 64, 22]


async def test_stub_records_calls_so_tests_can_count_embedding_requests() -> None:
    client = StubEmbeddingClient()

    await client.embed(["a", "b"])
    await client.embed(["c"])

    assert client.call_count == 2
    assert client.embedded_text_count == 3


async def test_stub_rejects_blank_text_like_the_real_service() -> None:
    client = StubEmbeddingClient()

    with pytest.raises(EmbeddingInputRejected):
        await client.embed(["valid text", "   "])


async def test_retry_succeeds_after_transient_failures() -> None:
    """Test that EmbeddingClient retries on transient failures."""
    from unittest.mock import MagicMock, patch

    from app.clients.embedding import EmbeddingClient

    client = EmbeddingClient(
        base_url="http://test:8080",
        timeout_seconds=1.0,
        max_batch_size=64,
        retry_max_attempts=3,
        retry_base_delay=0.01,  # fast for testing
    )

    call_count = 0

    async def mock_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            # Simulate transient failure
            import httpx
            raise httpx.ConnectError("connection refused")
        # Success on 3rd attempt - return a regular MagicMock (not async)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "test-model",
            "dimensions": 384,
            "embeddings": [[0.1] * 384],
        }
        mock_response.raise_for_status = lambda: None
        return mock_response

    with patch.object(client._client, "post", side_effect=mock_post):
        result = await client.embed(["test text"])

    assert call_count == 3
    assert len(result.vectors) == 1
    await client.aclose()
