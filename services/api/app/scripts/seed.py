import argparse
import asyncio
import csv
import logging
import sys
from pathlib import Path

import asyncpg

from app.config import get_settings
from app.db.pool import open_pool
from app.observability import configure_logging

logger = logging.getLogger("api.scripts.seed")

TABLES = (
    ("practices", ("id", "name", "slug", "city", "region")),
    ("users", ("id", "practice_id", "display_name", "email", "role")),
    (
        "patients",
        ("id", "practice_id", "mrn", "first_name", "last_name", "date_of_birth", "sex"),
    ),
    (
        "clinical_documents",
        (
            "id",
            "practice_id",
            "patient_id",
            "document_type",
            "title",
            "document_date",
            "author_name",
            "body",
        ),
    ),
)


def assert_header_matches(path: Path, columns: tuple[str, ...]) -> None:
    csv.field_size_limit(1 << 30)
    with path.open(encoding="utf-8", newline="") as handle:
        header = next(csv.reader(handle), [])
    if tuple(header) != columns:
        raise ValueError(
            f"{path.name} header {header} does not match the expected columns {list(columns)}"
        )


async def count_existing(connection: asyncpg.Connection) -> int:
    return await connection.fetchval("SELECT count(*) FROM clinical_documents")


async def load(connection: asyncpg.Connection, seed_dir: Path) -> dict[str, int]:
    loaded: dict[str, int] = {}
    for table, _ in reversed(TABLES):
        await connection.execute(f"TRUNCATE TABLE {table} CASCADE")

    for table, columns in TABLES:
        path = seed_dir / f"{table}.csv"
        assert_header_matches(path, columns)
        with path.open("rb") as handle:
            await connection.copy_to_table(
                table,
                source=handle,
                columns=list(columns),
                format="csv",
                header=True,
            )
        loaded[table] = await connection.fetchval(f"SELECT count(*) FROM {table}")
    return loaded


async def run(database: str, force: bool) -> int:
    settings = get_settings()
    dsn = settings.test_database_url if database == "test" else settings.database_url
    seed_dir = settings.seed_data_dir

    if not seed_dir.is_dir():
        print(f"seed data directory not found: {seed_dir}", file=sys.stderr)
        return 1

    async with open_pool(dsn, min_size=1, max_size=2) as pool, pool.acquire() as connection:
        existing = await count_existing(connection)
        if existing and not force:
            print(f"{existing} documents already present; reloading to stay deterministic")

        async with connection.transaction():
            loaded = await load(connection, seed_dir)

    for table, count in loaded.items():
        print(f"{table:<20} {count:>6}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Load the committed synthetic dataset.")
    parser.add_argument("--database", choices=("app", "test"), default="app")
    parser.add_argument("--force", action="store_true", help="reload without the notice")
    args = parser.parse_args()

    configure_logging(get_settings().api_log_level)
    try:
        return asyncio.run(run(args.database, args.force))
    except Exception as exc:
        logger.error("seeding failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
