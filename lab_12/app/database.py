from __future__ import annotations

import os
from typing import Optional

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DEFAULT_DATABASE_URL = "sqlite:///library.db"


class Base(DeclarativeBase):
    pass


class Database:
    def __init__(self, url: Optional[str] = None) -> None:
        self.url = url or os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
        self.engine = self._create_engine(self.url)
        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)

    @staticmethod
    def _create_engine(url: str) -> Engine:
        options: dict = {"echo": os.getenv("SQL_ECHO") == "1"}
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

    def create_all(self) -> None:
        Base.metadata.create_all(self.engine)

    def drop_all(self) -> None:
        Base.metadata.drop_all(self.engine)

    def session(self) -> Session:
        return self.session_factory()
