"""Общие фикстуры для тестов: изолированная БД в памяти, TestClient."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.library import models  # noqa: E402,F401
from src.library.database import Base, get_session  # noqa: E402
from src.library.main import app  # noqa: E402


@pytest.fixture()
def db_engine(tmp_path):
    """SQLite в файле tmp_path - изолирован для каждого теста."""
    db_path = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture()
def db_session_factory(db_engine):
    yield sessionmaker(bind=db_engine, autoflush=False, expire_on_commit=False)


@pytest.fixture()
def client(db_session_factory):
    """TestClient с переопределённой сессией БД (изолированная БД)."""

    def _override():
        db = db_session_factory()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    app.dependency_overrides[get_session] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def db(db_session_factory):
    session = db_session_factory()
    yield session
    session.close()


# Фикстуры для удобного создании сущностей в тестах
@pytest.fixture()
def sample_author(db):
    from src.library.models import Author

    a = Author(name="Тестов Автор", birth_year=1950)
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


@pytest.fixture()
def sample_book(db, sample_author):
    from src.library.models import Book

    b = Book(title="Тестовая книга", author_id=sample_author.id,
             year=2000, total_copies=3, available_copies=3)
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


def create_reader(db, username="user1", email="user1@test.ru",
                  full_name="Первый", password="secret1", role="USER"):
    from src.library.auth import hash_password
    from src.library.models import Reader

    r = Reader(username=username, email=email, full_name=full_name,
               hashed_password=hash_password(password), role=role)
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


@pytest.fixture()
def sample_user(db):
    return create_reader(db)


def api_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def register_and_token(client, username="u", email="u@test.ru",
                       full_name="Юзер", password="secret1"):
    r = client.post("/auth/register", json={
        "username": username, "email": email,
        "full_name": full_name, "password": password,
    })
    assert r.status_code == 201
    return r.json()["access_token"]


def create_admin(db, username="admin", password="adminpass",
                 email="admin@test.ru"):
    from src.library.auth import hash_password
    from src.library.models import Reader

    r = Reader(username=username, email=email, full_name="Администратор",
               hashed_password=hash_password(password), role="ADMIN")
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def admin_token(client, db):
    """Создаёт админа в изолированной БД и логинится, возвращая токен."""
    create_admin(db, username="boss", password="boss128",
                 email="boss@test.ru")
    r = client.post("/auth/login",
                    json={"username": "boss", "password": "boss128"})
    assert r.status_code == 200
    return r.json()["access_token"]