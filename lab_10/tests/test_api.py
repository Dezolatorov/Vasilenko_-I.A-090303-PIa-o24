"""Тесты REST API библиотеки."""

import pytest

from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client


def test_get_books_returns_list(client) -> None:
    response = client.get("/books")

    assert response.status_code == 200
    books = response.get_json()
    assert len(books) == 5
    assert books[0]["title"] == "Мастер и Маргарита"


def test_get_book_by_id(client) -> None:
    response = client.get("/books/2")

    assert response.status_code == 200
    assert response.get_json()["author"] == "Толстой Л.Н."


def test_get_missing_book_returns_404(client) -> None:
    response = client.get("/books/999")

    assert response.status_code == 404
    assert response.get_json() == {"error": "Book with id=999 not found", "code": "BOOK_NOT_FOUND"}


def test_create_book_returns_201(client) -> None:
    payload = {
        "title": "Гарри Поттер и философский камень",
        "author": "Роулинг Дж.К.",
        "genre": "фэнтези",
        "year": 1997,
        "price": 890,
        "available": 5,
    }
    response = client.post("/books", json=payload)

    assert response.status_code == 201
    body = response.get_json()
    assert body["id"] == 6
    assert response.headers["Location"] == "/books/6"
    assert client.get("/books/6").get_json()["title"] == payload["title"]


def test_create_book_with_invalid_data_returns_400(client) -> None:
    response = client.post("/books", json={"title": "", "price": -100})

    assert response.status_code == 400
    assert response.get_json()["code"] == "VALIDATION_ERROR"


def test_put_replaces_book(client) -> None:
    payload = {
        "title": "Война и мир. Том 1",
        "author": "Толстой Л.Н.",
        "genre": "роман-эпопея",
        "year": 1869,
        "price": 1300,
        "available": 1,
    }
    response = client.put("/books/2", json=payload)

    assert response.status_code == 200
    assert response.get_json()["genre"] == "роман-эпопея"


def test_patch_updates_price(client) -> None:
    response = client.patch("/books/1", json={"price": 699})

    assert response.status_code == 200
    body = response.get_json()
    assert body["price"] == 699.0
    assert body["title"] == "Мастер и Маргарита"


def test_delete_book_returns_204(client) -> None:
    assert client.delete("/books/3").status_code == 204
    assert client.get("/books/3").status_code == 404


def test_invalid_identifier_returns_400(client) -> None:
    response = client.get("/books/abc")

    assert response.status_code == 400
    assert response.get_json()["code"] == "INVALID_REQUEST"


def test_filter_and_sort_books(client) -> None:
    filtered = client.get("/books?genre=роман&max_price=900").get_json()
    assert [book["title"] for book in filtered] == ["Мастер и Маргарита", "Преступление и наказание"]

    sorted_books = client.get("/books?sort=year&order=desc").get_json()
    assert sorted_books[0]["year"] == 1972


def test_search_by_author_endpoint(client) -> None:
    response = client.get("/books/search?author=булгаков")

    assert response.status_code == 200
    body = response.get_json()
    assert body["count"] == 2
    assert all("Булгаков" in book["author"] for book in body["items"])


def test_unknown_route_and_method(client) -> None:
    assert client.get("/unknown").status_code == 404
    assert client.delete("/books").status_code == 405
