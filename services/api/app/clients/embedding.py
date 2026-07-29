import logging
from dataclasses import dataclass
from typing import Protocol

import httpx

from app.errors import EmbeddingServiceError

logger = logging.getLogger("api.embedding")

EMBEDDINGS_PATH = "/v1/embeddings"
HEALTH_PATH = "/health"


@dataclass(frozen=True)
class EmbeddingBatch:
    model: str
    dimensions: int
    vectors: list[list[float]]


class SupportsEmbedding(Protocol):
    async def is_healthy(self) -> bool: ...

    async def embed(self, texts: list[str]) -> EmbeddingBatch: ...


def split_batches(texts: list[str], max_batch_size: int) -> list[list[str]]:
    return [texts[start : start + max_batch_size] for start in range(0, len(texts), max_batch_size)]


class EmbeddingClient:
    def __init__(self, base_url: str, timeout_seconds: float, max_batch_size: int) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout_seconds)
        self._max_batch_size = max_batch_size

    async def aclose(self) -> None:
        await self._client.aclose()

    async def is_healthy(self) -> bool:
        try:
            response = await self._client.get(HEALTH_PATH)
            return response.status_code == httpx.codes.OK
        except httpx.HTTPError:
            return False

    async def embed(self, texts: list[str]) -> EmbeddingBatch:
        if not texts:
            return EmbeddingBatch(model="", dimensions=0, vectors=[])

        model = ""
        dimensions = 0
        vectors: list[list[float]] = []

        for batch in split_batches(texts, self._max_batch_size):
            payload = await self._post_batch(batch)
            model = payload["model"]
            dimensions = payload["dimensions"]
            vectors.extend(payload["embeddings"])

        return EmbeddingBatch(model=model, dimensions=dimensions, vectors=vectors)

    async def _post_batch(self, batch: list[str]) -> dict:
        try:
            response = await self._client.post(EMBEDDINGS_PATH, json={"texts": batch})
        except httpx.HTTPError as exc:
            logger.error(
                "embedding transport failure texts=%d error=%s",
                len(batch),
                type(exc).__name__,
            )
            raise EmbeddingServiceError() from exc

        if response.status_code == httpx.codes.UNPROCESSABLE_ENTITY:
            detail = response.json().get("detail", "the embedding service rejected the input")
            logger.warning("embedding rejected input texts=%d detail=%s", len(batch), detail)
            raise EmbeddingInputRejected(detail)

        if response.status_code >= httpx.codes.INTERNAL_SERVER_ERROR:
            logger.error("embedding service error status=%d", response.status_code)
            raise EmbeddingServiceError()

        response.raise_for_status()
        return response.json()


class EmbeddingInputRejected(Exception):
    pass
