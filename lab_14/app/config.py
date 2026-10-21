from __future__ import annotations

import os
from dataclasses import dataclass, field


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class Settings:
    app_name: str = "Library Books API"
    app_env: str = os.getenv("APP_ENV", "development")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///library_api.db")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    cache_ttl: int = field(default_factory=lambda: _int_env("CACHE_TTL", 60))


settings = Settings()
