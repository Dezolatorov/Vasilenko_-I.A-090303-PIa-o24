"""Фикстуры для тестов ЛР 15.

Тестовое окружение использует отдельную временную SQLite-базу, чтобы не
затрагивать реальный файл library_web.db (изоляция интеграционных тестов).
"""
from __future__ import annotations

import os
import tempfile

# Важно: установить DATABASE_URL ДО первого импорта app.database,
# чтобы engine создавался на тестовой базе, а не на боевой.
_tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp_db.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db.name}"
os.environ["SECRET_KEY"] = "test-secret-key"

import pytest  # noqa: E402

from app import create_app  # noqa: E402


@pytest.fixture(scope="session")
def app():
    application = create_app(with_seed=True)
    yield application


@pytest.fixture()
def client(app):
    """HTTP-клиент Flask (test client) без реального запуска сервера."""
    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture()
def service(app):
    """Сервисный слой поверх тестовой БД (для unit-проверок)."""
    from app.database import get_session
    from app.services.services import LibraryService

    return LibraryService(get_session())


@pytest.fixture()
def cleanup_tmp_db():
    yield
    try:
        os.remove(_tmp_db.name)
    except OSError:
        pass