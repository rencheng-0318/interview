from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EMBEDDING_", extra="ignore")

    model_dir: Path = Path("/opt/model")
    model_name: str = "interview-embedding-v1"
    max_sequence_length: int = 256
    max_batch_size: int = 64
    max_characters_per_text: int = 8_000
    inference_batch_size: int = 32
    log_level: str = "INFO"

    failure_rate: float = Field(default=0.0, ge=0.0, le=1.0)


@lru_cache
def get_settings() -> Settings:
    return Settings()
