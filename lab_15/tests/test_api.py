"""Тесты веб-интерфейса и REST API ЛР 15 (Flask).

Проверяют маршруты (HTML+Jinja2) и JSON API через Flask test client:
CRUD, поиск, фильтрацию, сортировку, обработку ошибок и HTTP-коды.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Веб-интерфейс (HTML)
# ---------------------------------------------------------------------------

def test_index_page(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Библиотека".encode("utf-8") in resp.data


def test_books_list_page(client):
    resp = client.get("/books")
    assert resp.status_code == 200
    assert resp.data


def test_books_list_search(client):
    resp = client.get("/books", query_string={"search": "Пушкин"})
    assert resp.status_code == 200


def test_books_list_filter_genre(client):
    resp = client.get("/books", query_string={"genre": "Роман"})
    assert resp.status_code == 200


def test_books_list_sort(client):
    resp = client.get("/books", query_string={"sort": "year", "order": "desc"})
    assert resp.status_code == 200


def test_book_detail_page(client):
    # id=1 всегда есть в сиде
    resp = client.get("/books/1")
    assert resp.status_code == 200


def test_book_detail_404(client):
    resp = client.get("/books/99999")
    assert resp.status_code == 404


def test_create_page_get(client):
    resp = client.get("/books/create")
    assert resp.status_code == 200


def test_readers_page(client):
    resp = client.get("/readers")
    assert resp.status_code == 200


def test_stats_via_api(client):
    # В веб-приложении ЛР 15 нет HTML-страницы /statistics — статистика доступна
    # только через REST API.
    resp = client.get("/api/statistics")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# REST API (JSON)
# ---------------------------------------------------------------------------

def test_api_list_books(client):
    resp = client.get("/api/books")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["total"] > 0
    assert isinstance(body["items"], list)


def test_api_get_book(client):
    resp = client.get("/api/books/1")
    assert resp.status_code == 200
    assert resp.get_json()["id"] == 1


def test_api_get_missing_book(client):
    resp = client.get("/api/books/99999")
    assert resp.status_code == 404


def test_api_create_book(client):
    payload = {
        "title": "API Книга",
        "author_id": 1,
        "genre": "Роман",
        "year": 2023,
        "isbn": "9785000000777",
        "price": "250.00",
        "copies_total": 2,
    }
    resp = client.post("/api/books", json=payload)
    assert resp.status_code == 201
    assert resp.get_json()["title"] == "API Книга"


def test_api_create_book_invalid(client):
    resp = client.post("/api/books", json={"title": ""})
    assert resp.status_code == 400


def test_api_put_book(client):
    payload = {
        "title": "PUT Книга",
        "author_id": 1,
        "genre": "Поэма",
        "year": 2000,
        "isbn": "9785000000666",
        "price": "100.00",
        "copies_total": 1,
    }
    resp = client.put("/api/books/1", json=payload)
    assert resp.status_code == 200
    assert resp.get_json()["title"] == "PUT Книга"


def test_api_patch_book(client):
    resp = client.patch("/api/books/1", json={"price": "777.00"})
    assert resp.status_code == 200
    assert resp.get_json()["price"] == 777.00


def test_api_delete_book(client):
    # Удаляем книгу без выдач: создадим новую через API и удалим её
    payload = {
        "title": "Книга для удаления",
        "author_id": 1,
        "genre": "Повесть",
        "year": 2015,
        "isbn": "9785000000555",
        "price": "50.00",
        "copies_total": 1,
    }
    created = client.post("/api/books", json=payload)
    book_id = created.get_json()["id"]
    resp = client.delete(f"/api/books/{book_id}")
    assert resp.status_code == 204
    assert client.get(f"/api/books/{book_id}").status_code == 404


def test_api_search(client):
    resp = client.get("/api/books/search", query_string={"q": "Пушкин"})
    assert resp.status_code == 200
    assert resp.get_json()["count"] > 0


def test_api_search_empty_query(client):
    resp = client.get("/api/books/search", query_string={"q": ""})
    assert resp.status_code == 400


def test_api_statistics(client):
    resp = client.get("/api/statistics")
    assert resp.status_code == 200
    assert resp.get_json()["books"] > 0