import asyncio
import sys
import time

import asyncpg
import httpx

from app.config import get_settings

TIMEOUT_SECONDS = 180
POLL_INTERVAL_SECONDS = 2


async def database_ready(dsn: str) -> bool:
    try:
        connection = await asyncpg.connect(dsn)
    except (OSError, asyncpg.PostgresError):
        return False
    try:
        await connection.fetchval("SELECT 1")
        return True
    finally:
        await connection.close()


async def embedding_ready(base_url: str) -> bool:
    try:
        async with httpx.AsyncClient(base_url=base_url, timeout=5.0) as client:
            response = await client.get("/health")
            return response.status_code == httpx.codes.OK
    except httpx.HTTPError:
        return False


async def wait_for(name: str, check) -> bool:
    deadline = time.monotonic() + TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if await check():
            print(f"{name}: ready")
            return True
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
    print(f"{name}: still unavailable after {TIMEOUT_SECONDS}s", file=sys.stderr)
    return False


async def run() -> int:
    settings = get_settings()
    checks = (
        ("database", lambda: database_ready(settings.database_url)),
        ("embedding", lambda: embedding_ready(settings.embedding_service_url)),
    )
    results = [await wait_for(name, check) for name, check in checks]
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
