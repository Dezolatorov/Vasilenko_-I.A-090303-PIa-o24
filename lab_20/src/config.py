from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Конфигурация приложения, загружаемая из переменных окружения / .env."""

    app_name: str = "Library API"
    app_version: str = "1.0.0"
    debug: bool = False

    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "library"
    database_user: str = "library"
    database_password: str = ""
    use_sqlite: bool = False

    secret_key: str = "change-me-in-production"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def database_url(self) -> str:
        """Собирает URL подключения к БД."""
        if self.use_sqlite:
            return "sqlite:///./library_local.db"
        return (
            f"postgresql+psycopg://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )


@lru_cache
def get_settings() -> "Settings":
    return Settings()
