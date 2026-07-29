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
