import logging
from dataclasses import dataclass
from pathlib import Path

import asyncpg

logger = logging.getLogger("api.migrations")

NO_TRANSACTION_MARKER = "migrate:no-transaction"

LEDGER_DDL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    filename    text PRIMARY KEY,
    applied_at  timestamptz NOT NULL DEFAULT now()
)
"""


@dataclass(frozen=True)
class Migration:
    filename: str
    sql: str

    @property
    def runs_in_transaction(self) -> bool:
        first_line = self.sql.lstrip().splitlines()[0] if self.sql.strip() else ""
        return NO_TRANSACTION_MARKER not in first_line


@dataclass(frozen=True)
class MigrationResult:
    applied: list[str]
    skipped: list[str]


def discover_migrations(migrations_dir: Path) -> list[Migration]:
    if not migrations_dir.is_dir():
        raise FileNotFoundError(f"migrations directory not found: {migrations_dir}")
    return [
        Migration(filename=path.name, sql=path.read_text(encoding="utf-8"))
        for path in sorted(migrations_dir.glob("*.sql"))
    ]


async def apply_migrations(pool: asyncpg.Pool, migrations_dir: Path) -> MigrationResult:
    migrations = discover_migrations(migrations_dir)
    applied: list[str] = []
    skipped: list[str] = []

    async with pool.acquire() as connection:
        await connection.execute(LEDGER_DDL)
        recorded = await connection.fetch("SELECT filename FROM schema_migrations")
        already_applied = {record["filename"] for record in recorded}

        for migration in migrations:
            if migration.filename in already_applied:
                skipped.append(migration.filename)
                continue

            logger.info("applying migration %s", migration.filename)
            if migration.runs_in_transaction:
                async with connection.transaction():
                    await connection.execute(migration.sql)
                    await connection.execute(
                        "INSERT INTO schema_migrations (filename) VALUES ($1)", migration.filename
                    )
            else:
                await connection.execute(migration.sql)
                await connection.execute(
                    "INSERT INTO schema_migrations (filename) VALUES ($1)", migration.filename
                )
            applied.append(migration.filename)

    return MigrationResult(applied=applied, skipped=skipped)
