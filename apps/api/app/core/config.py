"""
Application configuration using Pydantic Settings.
"""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

import os

_current_file = Path(__file__).resolve()
# In local development, the root is 4 levels up. In Docker, it's /app.
try:
    PROJECT_ROOT = _current_file.parents[4]
    if not (PROJECT_ROOT / "apps").exists() and not (PROJECT_ROOT / "packages").exists():
        PROJECT_ROOT = Path("/app")
except IndexError:
    PROJECT_ROOT = Path("/app")


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App settings
    app_name: str = "F1 Telemetry API"
    app_version: str = "0.1.0"
    debug: bool = False

    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # OpenF1 API
    openf1_base_url: str = "https://api.openf1.org/v1"

    # Fast-F1
    fastf1_cache_dir: str = str(PROJECT_ROOT / "data" / "cache" / "fastf1")

    # ML Models
    models_dir: str = str(PROJECT_ROOT / "packages" / "ml-models")

    # Redis (optional, for caching)
    redis_url: str = ""


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
