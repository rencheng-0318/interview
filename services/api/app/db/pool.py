import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import asyncpg
from pgvector.asyncpg import register_vector

logger = logging.getLogger("api.db")


async def _init_connection(connection: asyncpg.Connection) -> None:
    try:
        await register_vector(connection)
    except ValueError as exc:
        raise RuntimeError(
            "pgvector types are not available on this database. "
            "Run `make migrate` before starting the API."
        ) from exc


async def create_pool(
    dsn: str,
    min_size: int,
    max_size: int,
    max_inactive_connection_lifetime: float = 300.0,
    connection_timeout: float = 10.0,
) -> asyncpg.Pool:
    pool = await asyncpg.create_pool(
        dsn=dsn,
        min_size=min_size,
        max_size=max_size,
        init=_init_connection,
        max_inactive_connection_lifetime=max_inactive_connection_lifetime,
        timeout=connection_timeout,
    )
    logger.info(
        "database pool ready min_size=%d max_size=%d "
        "max_inactive_lifetime=%.0fs connection_timeout=%.0fs",
        min_size,
        max_size,
        max_inactive_connection_lifetime,
        connection_timeout,
    )
    return pool


@asynccontextmanager
async def open_pool(
    dsn: str,
    min_size: int = 1,
    max_size: int = 5,
    max_inactive_connection_lifetime: float = 300.0,
    connection_timeout: float = 10.0,
) -> AsyncIterator[asyncpg.Pool]:
    pool = await create_pool(
        dsn,
        min_size,
        max_size,
        max_inactive_connection_lifetime=max_inactive_connection_lifetime,
        connection_timeout=connection_timeout,
    )
    try:
        yield pool
    finally:
        await pool.close()
