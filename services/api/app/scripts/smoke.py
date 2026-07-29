import asyncio
import sys

from app.clients.embedding import EmbeddingClient
from app.config import get_settings
from app.db.pool import open_pool

PROBE_TEXTS = ["persistent thirst and frequent urination", "left knee pain on stairs"]


async def run() -> int:
    settings = get_settings()
    failures: list[str] = []

    async with open_pool(settings.database_url, min_size=1, max_size=2) as pool:
        for table in ("practices", "users", "patients", "clinical_documents"):
            count = await pool.fetchval(f"SELECT count(*) FROM {table}")
            print(f"{table:<20} {count:>6}")
            if count == 0:
                failures.append(f"{table} is empty; run `make seed`")

        applied = await pool.fetchval("SELECT count(*) FROM schema_migrations")
        print(f"{'migrations applied':<20} {applied:>6}")

    client = EmbeddingClient(
        base_url=settings.embedding_service_url,
        timeout_seconds=settings.embedding_request_timeout_seconds,
        max_batch_size=settings.embedding_max_batch_size,
    )
    try:
        batch = await client.embed(PROBE_TEXTS)
        print(f"{'embedding model':<20} {batch.model:>6}")
        print(f"{'dimensions':<20} {batch.dimensions:>6}")
        if batch.dimensions != 384:
            failures.append(f"expected 384 dimensions, got {batch.dimensions}")
        if len(batch.vectors) != len(PROBE_TEXTS):
            failures.append("embedding count did not match the number of texts")
    finally:
        await client.aclose()

    for failure in failures:
        print(f"FAIL {failure}", file=sys.stderr)
    print("\nsmoke: " + ("ok" if not failures else "failed"))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
