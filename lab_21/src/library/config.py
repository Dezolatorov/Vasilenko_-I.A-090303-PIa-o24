"""Конфигурация приложения. Настройки задаются через переменные окружения."""
import os
from dataclasses import dataclass, field


def _env(key: str, default: str) -> str:
    return os.environ.get(key, default)


@dataclass
class Settings:
    app_name: str = field(default_factory=lambda: _env("APP_NAME", "LibraryAPI"))
    database_url: str = field(
        default_factory=lambda: _env("DATABASE_URL", "sqlite:///./library.db")
    )
    secret_key: str = field(
        default_factory=lambda: _env(
            "SECRET_KEY", "dev-secret-key-change-me-0123456789abcdef0123"
        )
    )
    jwt_algorithm: str = field(default_factory=lambda: _env("JWT_ALGORITHM", "HS256"))
    access_token_expire_minutes: int = field(
        default_factory=lambda: int(_env("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
    )
    max_active_loans: int = field(
        default_factory=lambda: int(_env("MAX_ACTIVE_LOANS", "5"))
    )
    loan_days: int = field(default_factory=lambda: int(_env("LOAN_DAYS", "30")))
    log_level: str = field(default_factory=lambda: _env("LOG_LEVEL", "INFO"))


settings = Settings()