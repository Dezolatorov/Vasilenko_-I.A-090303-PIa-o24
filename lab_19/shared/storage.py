"""Хранилище, реализующее паттерн Database per Service.

Каждый микросервис владеет собственным хранилищем - отдельным JSON-файлом.
Сервисы не обращаются к данным друг друга напрямую, а только через REST API
(принцип изоляции данных сервисов).
"""

from __future__ import annotations

import json
import os
import threading
import uuid


class JsonStorage:
    """Простое потокобезопасное хранилище на базе JSON-файла."""

    def __init__(self, path: str):
        self._path = path
        self._lock = threading.RLock()
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        if not os.path.exists(path):
            self._write([])

    def _read(self) -> list:
        with open(self._path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    def _write(self, data: list) -> None:
        with open(self._path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)

    def all(self) -> list:
        with self._lock:
            return self._read()

    def get(self, entity_id: str) -> dict | None:
        with self._lock:
            for item in self._read():
                if item.get("id") == entity_id:
                    return item
            return None

    def insert(self, record: dict) -> dict:
        with self._lock:
            record = dict(record)
            record.setdefault("id", uuid.uuid4().hex)
            data = self._read()
            data.append(record)
            self._write(data)
            return record

    def update(self, entity_id: str, fields: dict) -> dict | None:
        with self._lock:
            data = self._read()
            for item in data:
                if item.get("id") == entity_id:
                    item.update(fields)
                    self._write(data)
                    return item
            return None

    def delete(self, entity_id: str) -> bool:
        with self._lock:
            data = self._read()
            new_data = [item for item in data if item.get("id") != entity_id]
            if len(new_data) == len(data):
                return False
            self._write(new_data)
            return True

    def next_id(self) -> str:
        return uuid.uuid4().hex


class PostgresStorage:
    """Хранилище сервиса в отдельной базе PostgreSQL.

    Каждый микросервис получает собственный DATABASE_URL, поэтому базы
    физически изолированы (паттерн Database per Service). Таблица `records`
    хранит документы в JSONB-колонке, а публичный интерфейс совпадает
    с JsonStorage, чтобы слой репозиториев не зависел от типа хранилища.
    """

    def __init__(self, url: str, table: str = "records") -> None:
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)

        from sqlalchemy import (
            Column,
            Integer,
            JSON,
            MetaData,
            String,
            Table,
            create_engine,
        )

        self._engine = create_engine(url, pool_pre_ping=True, future=True)
        self._metadata = MetaData()
        self._table = Table(
            table,
            self._metadata,
            Column("seq", Integer, primary_key=True, autoincrement=True),
            Column("id", String(32), unique=True, nullable=False),
            Column("data", JSON, nullable=False),
        )
        self._metadata.create_all(self._engine)

    def _rows(self) -> list[dict]:
        from sqlalchemy import select

        with self._engine.connect() as conn:
            result = conn.execute(select(self._table.c.data).order_by(self._table.c.seq))
            return [row[0] for row in result]

    def all(self) -> list:
        return self._rows()

    def get(self, entity_id: str) -> dict | None:
        from sqlalchemy import select

        with self._engine.connect() as conn:
            row = conn.execute(
                select(self._table.c.data).where(self._table.c.id == entity_id)
            ).first()
        return row[0] if row else None

    def insert(self, record: dict) -> dict:
        from sqlalchemy import insert

        record = dict(record)
        record.setdefault("id", uuid.uuid4().hex)
        with self._engine.begin() as conn:
            conn.execute(
                insert(self._table).values(id=record["id"], data=record)
            )
        return record

    def update(self, entity_id: str, fields: dict) -> dict | None:
        from sqlalchemy import select, update

        with self._engine.begin() as conn:
            row = conn.execute(
                select(self._table.c.data).where(self._table.c.id == entity_id)
            ).first()
            if row is None:
                return None
            merged = dict(row[0])
            merged.update(fields)
            conn.execute(
                update(self._table)
                .where(self._table.c.id == entity_id)
                .values(data=merged)
            )
        return merged

    def delete(self, entity_id: str) -> bool:
        from sqlalchemy import delete

        with self._engine.begin() as conn:
            result = conn.execute(
                delete(self._table).where(self._table.c.id == entity_id)
            )
        return result.rowcount > 0

    def next_id(self) -> str:
        return uuid.uuid4().hex


def make_storage(source: str):
    """Возвращает PostgreSQL-хранилище для URL или JSON-хранилище для пути."""
    if source.startswith(("postgres://", "postgresql://", "postgresql+psycopg://")):
        return PostgresStorage(source)
    return JsonStorage(source)
