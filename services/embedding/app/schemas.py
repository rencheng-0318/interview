from pydantic import BaseModel, Field


class EmbeddingRequest(BaseModel):
    texts: list[str] = Field(min_length=1)


class EmbeddingResponse(BaseModel):
    model: str
    dimensions: int
    embeddings: list[list[float]]


class HealthResponse(BaseModel):
    status: str
    model: str
    dimensions: int
    max_sequence_length: int
    max_batch_size: int


class ErrorResponse(BaseModel):
    error: str
    detail: str
