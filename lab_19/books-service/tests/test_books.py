"""Тесты books-service: 5 unit + 2 интеграционных + 1 недоступность/взаимодействие."""

import pytest

from app.models import Book
from app.repositories import BookRepository
from app.schemas.schemas import BookCreate
from app.services import BooksService
from shared.storage import JsonStorage


@pytest.fixture()
def service(tmp_path):
    storage = JsonStorage(str(tmp_path / "books.json"))
    repo = BookRepository(storage)
    return BooksService(repo)


def _book():
    return BookCreate(title="Война и мир", author="Л. Толстой", total_copies=3)


# ---------- 5 unit-тестов ----------
def test_unit_create_book(service):
    book = service.create_book(_book())
    assert book.available_copies == book.total_copies == 3


def test_unit_get_book(service):
    book = service.create_book(_book())
    got = service.get_book(book.id)
    assert got is not None and got.title == "Война и мир"


def test_unit_availability_positive(service):
    book = service.create_book(_book())
    info = service.check_availability(book.id)
    assert info["exists"] is True and info["available"] is True


def test_unit_availability_negative(service):
    assert service.check_availability("nonexistent")["exists"] is False


def test_unit_decrement_stock(service):
    book = service.create_book(_book())
    assert service.decrement_stock(book.id) is True
    assert service.get_book(book.id).available_copies == 2


def test_unit_decrement_exhausted(service):
    book = service.create_book(BookCreate(title="X", author="Y", total_copies=1))
    service.decrement_stock(book.id)
    assert service.decrement_stock(book.id) is False


# ---------- 2 интеграционных теста ----------
@pytest.fixture()
def client(tmp_path):
    from app.api import routes
    routes.init_service(str(tmp_path / "books.json"))
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)


def test_integration_create_and_check(client):
    r = client.post("/books", json={"title": "Евгений Онегин", "author": "А. Пушкин", "total_copies": 2})
    assert r.status_code == 201
    bid = r.json()["id"]
    chk = client.get(f"/books/check/{bid}")
    assert chk.status_code == 200 and chk.json()["available"] is True


def test_integration_decrement_conflict(client):
    r = client.post("/books", json={"title": "Один", "author": "А", "total_copies": 1})
    bid = r.json()["id"]
    assert client.post(f"/books/{bid}/decrement").status_code == 200
    assert client.post(f"/books/{bid}/decrement").status_code == 409


# ---------- 1 тест недоступности/взаимодействия ----------
def test_interaction_health(client):
    assert client.get("/health").json()["status"] == "healthy"


def test_unavailability_not_found(client):
    r = client.get("/books/zzz")
    assert r.status_code == 404