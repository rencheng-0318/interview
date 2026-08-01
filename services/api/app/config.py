from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    database_url: str = "postgresql://clinical:local_dev_only@db:5432/clinical_search"
    test_database_url: str = "postgresql://clinical:local_dev_only@db:5432/clinical_search_test"
    database_pool_min_size: int = 1
    database_pool_max_size: int = 10
    database_pool_max_inactive_lifetime: float = 300.0
    database_pool_connection_timeout: float = 10.0

    embedding_service_url: str = "http://embedding:8080"
    embedding_request_timeout_seconds: float = 30.0
    embedding_max_batch_size: int = 64
    embedding_retry_max_attempts: int = 3
    embedding_retry_base_delay: float = 1.0
    embedding_cache_max_size: int = 1000

    api_log_level: str = "INFO"
    api_cors_origins: str = "http://localhost:3000"

    search_default_limit: int = 10
    search_max_limit: int = 25
    search_max_query_length: int = 500

    default_demo_user_id: str = "user-northside-01"

    migrations_dir: Path = Path("/srv/database/migrations")
    seed_data_dir: Path = Path("/srv/database/seed/data")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
