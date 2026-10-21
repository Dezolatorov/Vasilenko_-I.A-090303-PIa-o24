from __future__ import annotations

from typing import Iterator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


def build_engine(url: str) -> Engine:
    options: dict = {}
    if url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}

    engine = create_engine(url, **options)

    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, _record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.close()

    return engine


engine = build_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def create_tables(target_engine: Engine | None = None) -> None:
    from app.models import Book

    Base.metadata.create_all(target_engine or engine)
