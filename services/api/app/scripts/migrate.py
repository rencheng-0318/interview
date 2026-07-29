import argparse
import asyncio
import logging
import sys

from app.config import get_settings
from app.db.migrations import apply_migrations
from app.db.pool import open_pool
from app.observability import configure_logging

logger = logging.getLogger("api.scripts.migrate")


async def run(database: str) -> int:
    settings = get_settings()
    dsn = settings.test_database_url if database == "test" else settings.database_url

    async with open_pool(dsn, min_size=1, max_size=2) as pool:
        result = await apply_migrations(pool, settings.migrations_dir)

    for filename in result.applied:
        print(f"applied  {filename}")
    for filename in result.skipped:
        print(f"skipped  {filename}")
    print(
        f"\n{database} database: {len(result.applied)} applied, "
        f"{len(result.skipped)} already present"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply pending SQL migrations.")
    parser.add_argument("--database", choices=("app", "test"), default="app")
    args = parser.parse_args()

    configure_logging(get_settings().api_log_level)
    try:
        return asyncio.run(run(args.database))
    except Exception as exc:
        logger.error("migration failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
