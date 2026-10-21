"""Тесты REST API: все endpoints работают через БД."""


def test_list_books(api):
    response = api.get("/books")
    assert response.status_code == 200
    data = response.get_json()
    assert data["count"] == 12
    assert data["items"][0]["title"]


def test_list_books_with_filters(api):
    response = api.get("/books?genre=фантастика&available=true&sort=price&order=desc")
    data = response.get_json()
    assert data["count"] == 3
    prices = [item["price"] for item in data["items"]]
    assert prices == sorted(prices, reverse=True)


def test_get_book_by_id(api):
    response = api.get("/books/1")
    assert response.status_code == 200
    assert response.get_json()["title"] == "Мастер и Маргарита"


def test_get_book_not_found(api):
    response = api.get("/books/999")
    assert response.status_code == 404
    assert response.get_json()["code"] == "NOT_FOUND"


def test_get_book_invalid_id(api):
    response = api.get("/books/abc")
    assert response.status_code == 400


def test_book_details_join(api):
    response = api.get("/books/1/details")
    data = response.get_json()
    assert data["author"] == "Булгаков М.А."
    assert "мистика" in data["tags"]
    assert data["cover_url"].startswith("http")


def test_create_update_delete_flow(api):
    created = api.post("/books", json={
        "title": "Новая книга",
        "author_id": 5,
        "genre": "фантастика",
        "year": 2020,
        "price": 700.0,
        "total_copies": 2,
    })
    assert created.status_code == 201
    book_id = created.get_json()["id"]

    patched = api.patch(f"/books/{book_id}", json={"price": 750.0})
    assert patched.status_code == 200
    assert patched.get_json()["price"] == 750.0

    replaced = api.put(f"/books/{book_id}", json={
        "title": "Новая книга (2-е издание)",
        "author_id": 5,
        "genre": "фантастика",
        "year": 2021,
        "price": 800.0,
        "total_copies": 3,
    })
    assert replaced.status_code == 200
    assert replaced.get_json()["total_copies"] == 3

    deleted = api.delete(f"/books/{book_id}")
    assert deleted.status_code == 204
    assert api.get(f"/books/{book_id}").status_code == 404


def test_create_book_validation_error(api):
    response = api.post("/books", json={"title": "Без автора"})
    assert response.status_code == 400
    assert response.get_json()["code"] == "VALIDATION_ERROR"


def test_issue_loan_endpoint(api):
    response = api.post("/loans", json={"book_id": 3, "reader_id": 4, "days": 10})
    assert response.status_code == 201
    loan = response.get_json()
    assert loan["book_id"] == 3
    assert api.get("/books/3").get_json()["available_copies"] == 1


def test_issue_loan_conflict(api):
    response = api.post("/loans", json={"book_id": 5, "reader_id": 1})
    assert response.status_code == 409
    assert response.get_json()["code"] == "CONFLICT"


def test_return_loan_endpoint(api):
    created = api.post("/loans", json={"book_id": 4, "reader_id": 5, "days": 7}).get_json()
    response = api.post(f"/loans/{created['id']}/return")
    assert response.status_code == 200
    assert response.get_json()["returned_at"] is not None
    assert api.get("/books/4").get_json()["available_copies"] == 3


def test_search_and_history_endpoints(api):
    first = api.get("/books/search?q=война")
    assert first.status_code == 200
    assert first.get_json()["count"] == 1

    api.get("/books/search?q=война")
    history = api.get("/books/search-history").get_json()
    assert history["source"] == "redis"
    assert history["items"][0]["query"] == "война"
    assert history["items"][0]["count"] == 2


def test_search_query_too_short(api):
    assert api.get("/books/search?q=в").status_code == 400


def test_cache_stats_endpoint(api):
    api.get("/books/1")
    api.get("/books/1")
    stats = api.get("/cache/stats").get_json()
    assert stats["hits"] == 1
    assert stats["misses"] == 1


def test_readers_and_stats(api):
    readers = api.get("/readers").get_json()
    assert readers["count"] == 5

    stats = api.get("/stats").get_json()
    assert stats["books_total"] == 12
    assert stats["by_genre"]

    health = api.get("/health").get_json()
    assert health["status"] == "ok"
