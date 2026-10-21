"""API-тесты каталога книг: CRUD, фильтрация, сортировка."""
from tests.conftest import admin_token, api_headers, register_and_token


def _admin_token(client, db):
    return admin_token(client, db)


def _user_token(client):
    return register_and_token(client, username="uservobooks", email="ub@test.ru")


def _create_author(client, token, name="Автор Тест"):
    r = client.post("/authors", headers=api_headers(token),
                    json={"name": name, "birth_year": 1980})
    assert r.status_code == 201
    return r.json()["id"]


def _create_book(client, token, author_id, title="Книга", year=2000, copies=2):
    r = client.post("/books", headers=api_headers(token),
                    json={"title": title, "author_id": author_id,
                          "year": year, "total_copies": copies})
    assert r.status_code == 201
    return r.json()


def test_books_crud_flow(client, db):
    admin = _admin_token(client, db)
    author_id = _create_author(client, admin)
    book = _create_book(client, admin, author_id, title="Поток", year=2001, copies=3)
    bid = book["id"]

    # GET по id
    r = client.get(f"/books/{bid}", headers=api_headers(admin))
    assert r.status_code == 200
    assert r.json()["title"] == "Поток"
    assert r.json()["available_copies"] == 3

    # PUT update
    r = client.put(f"/books/{bid}", headers=api_headers(admin),
                   json={"total_copies": 4})
    assert r.status_code == 200
    assert r.json()["total_copies"] == 4
    assert r.json()["available_copies"] == 4

    # DELETE
    r = client.delete(f"/books/{bid}", headers=api_headers(admin))
    assert r.status_code == 204


def test_get_missing_book_404(client, db):
    admin = _admin_token(client, db)
    r = client.get("/books/999999", headers=api_headers(admin))
    assert r.status_code == 404


def test_create_book_missing_author_404(client, db):
    admin = _admin_token(client, db)
    r = client.post("/books", headers=api_headers(admin),
                    json={"title": "X", "author_id": 99999, "year": 2000})
    assert r.status_code == 404


def test_books_search_filter_sort(client, db):
    admin = _admin_token(client, db)
    user = _user_token(client)
    a1 = _create_author(client, admin, "Первый Автор")
    a2 = _create_author(client, admin, "Второй Автор")
    _create_book(client, admin, a1, "Альфа-книга", year=2010)
    _create_book(client, admin, a2, "Бета сборник", year=2020)
    _create_book(client, admin, a1, "Гамма", year=2005)

    # Поиск по подстроке
    r = client.get("/books", params={"title": "книга"}, headers=api_headers(user))
    data = r.json()
    assert len(data) == 1
    assert all("книга" in b["title"] for b in data)

    # Сортировка по убыванию года
    r = client.get("/books", params={"sort_by": "year", "descending": True},
                   headers=api_headers(user))
    years = [b["year"] for b in r.json()]
    assert years == sorted(years, reverse=True)

    # Фильтр по автору
    r = client.get("/books", params={"author_id": a2}, headers=api_headers(user))
    assert len(r.json()) == 1
    assert r.json()[0]["title"] == "Бета сборник"

    # available_only
    r = client.get("/books", params={"available_only": True}, headers=api_headers(user))
    assert len(r.json()) == 3


def test_create_book_invalid_data_422(client, db):
    admin = _admin_token(client, db)
    a = _create_author(client, admin)
    r = client.post("/books", headers=api_headers(admin),
                    json={"title": "X", "author_id": a, "year": -5})
    assert r.status_code == 422


def test_delete_book_on_loan_conflict(client, db):
    admin = _admin_token(client, db)
    user = _user_token(client)
    a = _create_author(client, admin)
    book = _create_book(client, admin, a, title="Должна остаться", copies=1)

    # Пользователь берёт книгу
    r = client.post("/loans", headers=api_headers(user), json={"book_id": book["id"]})
    assert r.status_code == 201

    # Админ не может удалить книгу на руках
    r = client.delete(f"/books/{book['id']}", headers=api_headers(admin))
    assert r.status_code == 422