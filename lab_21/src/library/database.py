"""Настройка SQLAlchemy: движок, сессия, базовый класс моделей."""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings


class Base(DeclarativeBase):
    pass


def _build_engine(uri: str | None = None):
    url = uri or settings.database_url
    kwargs: dict = {"future": True}
    if url.startswith("sqlite"):
        # Для SQLite одиночный процесс; enable shared cache для вложенных сессий в тестах
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)


engine = _build_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


def get_session() -> Generator[Session, None, None]:
    """FastAPI-зависимость: даёт сессию БД на время запроса.

    Коммитим по завершении успешного запроса, откатываем при ошибке,
    чтобы данные мутирующих операций реально сохранялись.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """Создаёт таблицы (миграции вне рамок проекта)."""
    from . import models  # noqa: F401  # регистрация моделей в метаданных

    Base.metadata.create_all(bind=engine)