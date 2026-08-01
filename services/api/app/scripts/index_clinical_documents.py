import argparse
import asyncio
import logging
import sys

from app.clients.embedding import EmbeddingClient
from app.config import get_settings
from app.db.pool import open_pool
from app.features.indexing import run_indexing
from app.observability import configure_logging

logger = logging.getLogger("api.scripts.index")


async def run(database: str) -> int:
    settings = get_settings()
    dsn = settings.test_database_url if database == "test" else settings.database_url

    embedding_client = EmbeddingClient(
        base_url=settings.embedding_service_url,
        timeout_seconds=settings.embedding_request_timeout_seconds,
        max_batch_size=settings.embedding_max_batch_size,
    )

    try:
        async with open_pool(dsn, min_size=1, max_size=3) as pool:
            summary = await run_indexing(pool, embedding_client)
    finally:
        await embedding_client.aclose()

    print(f"\n{'='*40}")
    print(f"  total documents:  {summary.total_documents}")
    print(f"  already indexed:  {summary.already_indexed}")
    print(f"  indexed:          {summary.indexed}")
    print(f"  skipped:          {summary.skipped}")
    print(f"  failed:           {summary.failed}")
    print(f"  chunks created:   {summary.chunks_created}")
    print(f"{'='*40}")

    if summary.errors:
        print(f"\nerrors ({len(summary.errors)}):")
        for err in summary.errors[:20]:
            print(f"  - {err}")
        if len(summary.errors) > 20:
            print(f"  ... and {len(summary.errors) - 20} more")

    return 1 if summary.failed > 0 and summary.indexed == 0 else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the semantic search index.")
    parser.add_argument("--database", choices=("app", "test"), default="app")
    args = parser.parse_args()

    configure_logging(get_settings().api_log_level)
    try:
        return asyncio.run(run(args.database))
    except Exception as exc:
        logger.error("indexing failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
