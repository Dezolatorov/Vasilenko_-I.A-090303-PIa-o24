from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/library",
    )
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-change-me")
    flask_env: str = os.getenv("FLASK_ENV", "development")
    page_size: int = int(os.getenv("PAGE_SIZE", "10"))


settings = Settings()
