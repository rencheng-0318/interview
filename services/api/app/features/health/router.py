import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status

from app.clients.embedding import SupportsEmbedding
from app.context import PoolDep
from app.schemas import CamelModel

logger = logging.getLogger("api.health")

router = APIRouter(tags=["health"])


class DependencyStatus(CamelModel):
    database: str
    embedding: str


class HealthResponse(CamelModel):
    status: str
    dependencies: DependencyStatus


def get_embedding_client(request: Request) -> SupportsEmbedding:
    return request.app.state.embedding_client


@router.get("/health", response_model=HealthResponse)
async def health(
    response: Response,
    pool: PoolDep,
    embedding_client: Annotated[SupportsEmbedding, Depends(get_embedding_client)],
) -> HealthResponse:
    database = "ok"
    try:
        await pool.fetchval("SELECT 1")
    except Exception:
        logger.exception("database health check failed")
        database = "unavailable"

    embedding = "ok" if await embedding_client.is_healthy() else "unavailable"

    overall = "ok" if database == "ok" and embedding == "ok" else "degraded"
    if overall != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(
        status=overall,
        dependencies=DependencyStatus(database=database, embedding=embedding),
    )
