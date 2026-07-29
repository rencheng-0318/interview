import pytest

from app.clients.embedding import EmbeddingClient, EmbeddingInputRejected

pytestmark = pytest.mark.integration

EXPECTED_DIMENSIONS = 384


def cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


async def test_service_returns_unit_vectors_of_the_expected_width(
    real_embedding_client: EmbeddingClient,
) -> None:
    batch = await real_embedding_client.embed(["polyuria and polydipsia"])

    assert batch.dimensions == EXPECTED_DIMENSIONS
    assert len(batch.vectors[0]) == EXPECTED_DIMENSIONS
    assert abs(cosine(batch.vectors[0], batch.vectors[0]) - 1.0) < 1e-5


async def test_service_is_deterministic(real_embedding_client: EmbeddingClient) -> None:
    text = ["recurrent unilateral cephalalgia with scintillating scotoma"]

    first = await real_embedding_client.embed(text)
    second = await real_embedding_client.embed(text)

    assert first.vectors == second.vectors


async def test_clinical_paraphrase_scores_above_unrelated_text(
    real_embedding_client: EmbeddingClient,
) -> None:
    batch = await real_embedding_client.embed(
        [
            "frequent urination and persistent thirst",
            "The patient reports polyuria and polydipsia over the past three weeks.",
            "Medial joint space narrowing with subchondral sclerosis of the knee.",
        ]
    )
    query, paraphrase, unrelated = batch.vectors

    assert cosine(query, paraphrase) > cosine(query, unrelated) + 0.15


async def test_oversized_text_is_rejected_rather_than_silently_truncated(
    real_embedding_client: EmbeddingClient,
) -> None:
    with pytest.raises(EmbeddingInputRejected):
        await real_embedding_client.embed(["padding " * 3000])


async def test_blank_text_is_rejected(real_embedding_client: EmbeddingClient) -> None:
    with pytest.raises(EmbeddingInputRejected):
        await real_embedding_client.embed(["   \n  "])


async def test_batches_larger_than_the_service_limit_are_split_transparently(
    real_embedding_client: EmbeddingClient,
) -> None:
    texts = [f"clinical observation number {index}" for index in range(70)]

    batch = await real_embedding_client.embed(texts)

    assert len(batch.vectors) == len(texts)
