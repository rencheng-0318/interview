import json
from collections.abc import AsyncIterator
from pathlib import Path

import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient

from app.clients.embedding import EmbeddingClient
from app.config import Settings, get_settings
from app.db.migrations import apply_migrations
from app.main import create_app
from app.scripts.seed import load
from tests.stubs import StubEmbeddingClient


@pytest.fixture(scope="session")
def settings() -> Settings:
    return get_settings()


@pytest.fixture(scope="session")
def curated_cases(settings: Settings) -> dict:
    path: Path = settings.seed_data_dir / "curated_cases.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def primary_practice_id(curated_cases: dict) -> str:
    return curated_cases["primaryPracticeId"]


@pytest.fixture(scope="session")
async def prepared_database(settings: Settings) -> AsyncIterator[str]:
    pool = await asyncpg.create_pool(dsn=settings.test_database_url, min_size=1, max_size=2)
    try:
        await apply_migrations(pool, settings.migrations_dir)
        async with pool.acquire() as connection, connection.transaction():
            await load(connection, settings.seed_data_dir)
    finally:
        await pool.close()
    yield settings.test_database_url


@pytest.fixture
async def connection(prepared_database: str) -> AsyncIterator[asyncpg.Connection]:
    from pgvector.asyncpg import register_vector

    conn = await asyncpg.connect(dsn=prepared_database)
    await register_vector(conn)
    transaction = conn.transaction()
    await transaction.start()
    try:
        yield conn
    finally:
        await transaction.rollback()
        await conn.close()


class SingleConnectionPool:
    def __init__(self, connection: asyncpg.Connection) -> None:
        self._connection = connection

    def acquire(self):
        connection = self._connection

        class _Acquired:
            async def __aenter__(self):
                return connection

            async def __aexit__(self, *exc_info):
                return False

        return _Acquired()

    async def execute(self, *args, **kwargs):
        return await self._connection.execute(*args, **kwargs)

    async def fetch(self, *args, **kwargs):
        return await self._connection.fetch(*args, **kwargs)

    async def fetchrow(self, *args, **kwargs):
        return await self._connection.fetchrow(*args, **kwargs)

    async def fetchval(self, *args, **kwargs):
        return await self._connection.fetchval(*args, **kwargs)

    async def close(self) -> None:
        return None


@pytest.fixture
def embedding_client() -> StubEmbeddingClient:
    return StubEmbeddingClient()


@pytest.fixture
async def api(
    connection: asyncpg.Connection,
    embedding_client: StubEmbeddingClient,
    settings: Settings,
) -> AsyncIterator[AsyncClient]:
    app = create_app()
    app.state.settings = settings
    app.state.pool = SingleConnectionPool(connection)
    app.state.embedding_client = embedding_client

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.fixture
async def real_embedding_client(settings: Settings) -> AsyncIterator[EmbeddingClient]:
    client = EmbeddingClient(
        base_url=settings.embedding_service_url,
        timeout_seconds=settings.embedding_request_timeout_seconds,
        max_batch_size=settings.embedding_max_batch_size,
    )
    if not await client.is_healthy():
        await client.aclose()
        pytest.skip(
            "embedding service is not reachable; start it with `docker compose up -d embedding`"
        )
    try:
        yield client
    finally:
        await client.aclose()


def practice_token(user_id: str) -> dict[str, str]:
    return {"Authorization": f"Bearer demo_{user_id}"}


@pytest.fixture
def northside_headers() -> dict[str, str]:
    return practice_token("user-northside-01")


@pytest.fixture
def lakeshore_headers() -> dict[str, str]:
    return practice_token("user-lakeshore-01")


@pytest.fixture
def summit_headers() -> dict[str, str]:
    return practice_token("user-summit-01")
