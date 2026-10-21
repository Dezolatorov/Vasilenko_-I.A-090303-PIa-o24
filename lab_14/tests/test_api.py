from app.deps import cache

PAYLOAD = {
    "title": "Тестовая книга",
    "author": "Тестовый автор",
    "genre": "Роман",
    "year": 2024,
    "isbn": "9785000000099",
    "publisher": "Питер",
    "copies_total": 2,
    "rating": 4.2,
}


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_list_books(client):
    response = client.get("/books")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 8
    assert len(body["items"]) == 8
    assert body["limit"] == 20 and body["offset"] == 0


def test_get_existing_book(client):
    response = client.get("/books/1")
    assert response.status_code == 200
    assert response.json()["title"] == "Евгений Онегин"


def test_get_missing_book(client):
    response = client.get("/books/9999")
    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


def test_invalid_path_parameter(client):
    response = client.get("/books/abc")
    assert response.status_code == 422


def test_create_book(client):
    response = client.post("/books", json=PAYLOAD)
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 9
    assert body["title"] == "Тестовая книга"
    assert body["copies_available"] == 2


def test_create_invalid_book(client):
    payload = dict(PAYLOAD, rating=6)
    response = client.post("/books", json=payload)
    assert response.status_code == 422


def test_create_duplicate_isbn(client):
    payload = dict(PAYLOAD, isbn="9785000000001")
    response = client.post("/books", json=payload)
    assert response.status_code == 409


def test_replace_book(client):
    payload = dict(PAYLOAD, title="Заменённая книга", year=2020)
    response = client.put("/books/1", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Заменённая книга"
    assert body["year"] == 2020
    assert body["author"] == "Тестовый автор"


def test_replace_missing_book(client):
    response = client.put("/books/9999", json=PAYLOAD)
    assert response.status_code == 404


def test_patch_book(client):
    response = client.patch("/books/1", json={"rating": 3.5})
    assert response.status_code == 200
    body = response.json()
    assert body["rating"] == 3.5
    assert body["title"] == "Евгений Онегин"
    assert body["author"] == "Пушкин А.С."


def test_patch_validation_error(client):
    response = client.patch("/books/1", json={"rating": 10})
    assert response.status_code == 422


def test_delete_book_then_not_found(client):
    assert client.delete("/books/1").status_code == 204
    assert client.get("/books/1").status_code == 404


def test_delete_twice(client):
    assert client.delete("/books/1").status_code == 204
    response = client.delete("/books/1")
    assert response.status_code == 404


def test_filter_by_genre(client):
    response = client.get("/books", params={"genre": "Роман"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 4
    assert all(item["genre"] == "Роман" for item in body["items"])


def test_filter_by_min_rating(client):
    response = client.get("/books", params={"min_rating": 4.8})
    assert response.status_code == 200
    assert all(item["rating"] >= 4.8 for item in response.json()["items"])


def test_sorting(client):
    response = client.get("/books", params={"sort": "year", "order": "desc"})
    years = [item["year"] for item in response.json()["items"]]
    assert years == sorted(years, reverse=True)

    response = client.get("/books", params={"sort": "rating", "order": "asc"})
    ratings = [item["rating"] for item in response.json()["items"]]
    assert ratings == sorted(ratings)


def test_pagination(client):
    response = client.get("/books", params={"limit": 3, "offset": 6})
    body = response.json()
    assert body["total"] == 8
    assert body["limit"] == 3
    assert body["offset"] == 6
    assert len(body["items"]) == 2


def test_search(client):
    response = client.get("/books/search", params={"q": "Пушкин"})
    assert response.status_code == 200
    assert len(response.json()) == 2

    empty = client.get("/books/search", params={"q": ""})
    assert empty.status_code == 422


def test_statistics(client):
    response = client.get("/books/statistics")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 8
    assert body["total_copies"] == 26
    assert body["by_genre"]["Роман"] == 4
    assert body["max_rating"] == 5.0


def test_cache_aside_and_invalidation(client):
    first = client.get("/books/3")
    assert first.status_code == 200
    assert cache.get(3) is not None

    second = client.get("/books/3")
    assert second.json() == first.json()

    patched = client.patch("/books/3", json={"rating": 3.0})
    assert patched.status_code == 200
    assert cache.get(3) is None

    fresh = client.get("/books/3")
    assert fresh.json()["rating"] == 3.0
    assert cache.get(3)["rating"] == 3.0


def test_openapi_schema(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/books" in paths
    assert "/books/{book_id}" in paths
    assert "get" in paths["/books"] and "post" in paths["/books"]
