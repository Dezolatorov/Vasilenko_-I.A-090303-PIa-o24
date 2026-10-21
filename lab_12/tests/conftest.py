"""Фикстуры для тестов ЛР 12 (SQLAlchemy ORM).

Интеграционные тесты работают с отдельной временной SQLite-базой
(создаётся и уничтожается для каждой тестовой функции), чтобы не
затрагивать реальный файл library.db.
"""
from __future__ import annotations

import tempfile
from decimal import Decimal

import pytest

from app.database import Database
from app.seed import seed_database


@pytest.fixture()
def database(tmp_path) -> Database:
    """Новая пустая БД на временном файле."""
    db = Database(url=f"sqlite:///{tmp_path / 'test.db'}")
    db.create_all()
    yield db
    db.engine.dispose()


@pytest.fixture()
def seeded_database(tmp_path) -> Database:
    """БД, заполненная тестовыми данными (сид из app/seed.py)."""
    db = Database(url=f"sqlite:///{tmp_path / 'seed.db'}")
    db.create_all()
    seed_database(db)
    yield db
    db.engine.dispose()


@pytest.fixture()
def readers() -> list[tuple[str, str]]:
    return [
        ("Тестовый Читатель", "test@example.com"),
        ("Второй Читатель", "reader2@example.com"),
    ]


@pytest.fixture()
def book_data() -> dict:
    return {
        "title": "Тестовая книга",
        "author": "Тестовый Автор",
        "genre": "Роман",
        "year": 2000,
        "price": Decimal("450.50"),
        "copies_total": 3,
        "copies_available": 3,
    }