import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.clients.circuit_breaker import CircuitBreaker
from app.clients.embedding import EmbeddingClient
from app.clients.embedding_cache import EmbeddingCache
from app.config import get_settings
from app.db.pool import create_pool
from app.errors import register_error_handlers
from app.features.evaluation.router import router as evaluation_router
from app.features.health.router import router as health_router
from app.features.patients.router import router as patients_router
from app.features.search.router import router as search_router
from app.features.session.router import router as session_router
from app.observability import configure_logging, register_request_logging

logger = logging.getLogger("api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.api_log_level)

    app.state.settings = settings
    app.state.pool = await create_pool(
        dsn=settings.database_url,
        min_size=settings.database_pool_min_size,
        max_size=settings.database_pool_max_size,
        max_inactive_connection_lifetime=settings.database_pool_max_inactive_lifetime,
        connection_timeout=settings.database_pool_connection_timeout,
    )
    app.state.embedding_circuit_breaker = CircuitBreaker(
        failure_threshold=5,
        recovery_timeout=30.0,
        half_open_max=2,
        name="embedding",
    )
    app.state.embedding_client = EmbeddingClient(
        base_url=settings.embedding_service_url,
        timeout_seconds=settings.embedding_request_timeout_seconds,
        max_batch_size=settings.embedding_max_batch_size,
        circuit_breaker=app.state.embedding_circuit_breaker,
        retry_max_attempts=settings.embedding_retry_max_attempts,
        retry_base_delay=settings.embedding_retry_base_delay,
    )
    app.state.embedding_cache = EmbeddingCache(
        max_size=settings.embedding_cache_max_size,
    )
    logger.info("api ready")
    try:
        yield
    finally:
        await app.state.embedding_client.aclose()
        await app.state.pool.close()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Clinical Record Search API",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-Id"],
    )

    register_request_logging(app)
    register_error_handlers(app)

    app.include_router(health_router)
    app.include_router(session_router)
    app.include_router(patients_router)
    app.include_router(search_router)
    app.include_router(evaluation_router)
    return app


app = create_app()
