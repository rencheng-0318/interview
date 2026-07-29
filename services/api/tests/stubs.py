import hashlib
import math

from app.clients.embedding import EmbeddingBatch, EmbeddingInputRejected

DIMENSIONS = 384
STUB_MODEL = "stub-embedding-v1"
MAX_CHARACTERS_PER_TEXT = 8_000


def deterministic_vector(text: str, dimensions: int = DIMENSIONS) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values: list[float] = []
    counter = 0
    while len(values) < dimensions:
        block = hashlib.sha256(digest + counter.to_bytes(4, "big")).digest()
        values.extend(byte - 127.5 for byte in block)
        counter += 1
    trimmed = values[:dimensions]
    norm = math.sqrt(sum(value * value for value in trimmed)) or 1.0
    return [value / norm for value in trimmed]


class StubEmbeddingClient:
    def __init__(self, healthy: bool = True) -> None:
        self.healthy = healthy
        self.calls: list[list[str]] = []

    @property
    def call_count(self) -> int:
        return len(self.calls)

    @property
    def embedded_text_count(self) -> int:
        return sum(len(call) for call in self.calls)

    async def aclose(self) -> None:
        return None

    async def is_healthy(self) -> bool:
        return self.healthy

    async def embed(self, texts: list[str]) -> EmbeddingBatch:
        self.calls.append(list(texts))
        for index, text in enumerate(texts):
            if not text.strip():
                raise EmbeddingInputRejected(f"texts[{index}] is empty or whitespace only")
            if len(text) > MAX_CHARACTERS_PER_TEXT:
                raise EmbeddingInputRejected(f"texts[{index}] is {len(text)} characters")
        return EmbeddingBatch(
            model=STUB_MODEL,
            dimensions=DIMENSIONS,
            vectors=[deterministic_vector(text) for text in texts],
        )


class UnavailableEmbeddingClient(StubEmbeddingClient):
    def __init__(self) -> None:
        super().__init__(healthy=False)

    async def embed(self, texts: list[str]) -> EmbeddingBatch:
        from app.errors import EmbeddingServiceError

        self.calls.append(list(texts))
        raise EmbeddingServiceError()
