import logging
import random
import time
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings
from app.encoder import Encoder
from app.schemas import EmbeddingRequest, EmbeddingResponse, ErrorResponse, HealthResponse

logger = logging.getLogger("embedding")


class ServiceError(Exception):
    def __init__(self, status_code: int, error: str, detail: str) -> None:
        self.status_code = status_code
        self.error = error
        self.detail = detail
        super().__init__(detail)


def validate_texts(texts: list[str], settings: Settings) -> None:
    if len(texts) > settings.max_batch_size:
        raise ServiceError(
            422,
            "batch_too_large",
            f"received {len(texts)} texts, maximum is {settings.max_batch_size}",
        )
    for index, text in enumerate(texts):
        if not text.strip():
            raise ServiceError(422, "blank_text", f"texts[{index}] is empty or whitespace only")
        if len(text) > settings.max_characters_per_text:
            raise ServiceError(
                422,
                "text_too_long",
                f"texts[{index}] is {len(text)} characters, maximum is "
                f"{settings.max_characters_per_text}",
            )


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    started = time.perf_counter()
    app.state.encoder = Encoder(
        model_dir=settings.model_dir,
        max_sequence_length=settings.max_sequence_length,
        inference_batch_size=settings.inference_batch_size,
    )
    logger.info(
        "encoder ready model=%s dimensions=%d load_ms=%d",
        settings.model_name,
        app.state.encoder.dimensions,
        int((time.perf_counter() - started) * 1000),
    )
    yield


app = FastAPI(title="Interview Embedding Service", version="1.0.0", lifespan=lifespan)


@app.exception_handler(ServiceError)
async def handle_service_error(request: Request, exc: ServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error=exc.error, detail=exc.detail).model_dump(),
    )


def get_encoder(request: Request) -> Encoder:
    return request.app.state.encoder


SettingsDep = Annotated[Settings, Depends(get_settings)]
EncoderDep = Annotated[Encoder, Depends(get_encoder)]


@app.get("/health", response_model=HealthResponse)
async def health(encoder: EncoderDep, settings: SettingsDep) -> HealthResponse:
    return HealthResponse(
        status="ok",
        model=settings.model_name,
        dimensions=encoder.dimensions,
        max_sequence_length=encoder.max_sequence_length,
        max_batch_size=settings.max_batch_size,
    )


@app.post(
    "/v1/embeddings",
    response_model=EmbeddingResponse,
    responses={422: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
async def create_embeddings(
    payload: EmbeddingRequest,
    encoder: EncoderDep,
    settings: SettingsDep,
) -> EmbeddingResponse:
    if settings.failure_rate > 0 and random.random() < settings.failure_rate:
        raise ServiceError(503, "injected_failure", "synthetic failure for testing")

    validate_texts(payload.texts, settings)

    started = time.perf_counter()
    embeddings = await run_in_threadpool(encoder.encode, payload.texts)
    logger.info(
        "embedded texts=%d duration_ms=%d",
        len(payload.texts),
        int((time.perf_counter() - started) * 1000),
    )
    return EmbeddingResponse(
        model=settings.model_name,
        dimensions=encoder.dimensions,
        embeddings=embeddings,
    )
