import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import get_settings


class Base(DeclarativeBase):
    pass


def get_engine():
    settings = get_settings()
    connect_args = {"check_same_thread": False} if settings.use_sqlite else {}
    return create_engine(settings.database_url, connect_args=connect_args, pool_pre_ping=True)


engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db() -> None:
    """Создаёт таблицы и логирует результат."""
    from . import models  # noqa: F401  (регистрирует модели в Base)

    logger = logging.getLogger("library.db")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured (engine=%s)", engine.url.drivername)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
