def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"
    assert body["database"] == "ok"


def test_list_books_empty(client):
    resp = client.get("/api/books")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_and_list_book(client):
    payload = {
        "title": "Мастер и Маргарита",
        "author_name": "Михаил Булгаков",
        "year": 1967,
        "isbn": "9785170705399",
        "copies_total": 4,
    }
    created = client.post("/api/books", json=payload)
    assert created.status_code == 201
    book = created.json()
    assert book["copies_available"] == 4

    listing = client.get("/api/books").json()
    assert len(listing) == 1
    assert listing[0]["title"] == "Мастер и Маргарита"


def test_search_and_stats(client):
    client.post("/api/books", json={
        "title": "Евгений Онегин", "author_name": "А.С. Пушкин",
        "year": 1833, "isbn": "9780000000002", "copies_total": 1,
    })
    found = client.get("/api/books", params={"q": "Онегин"}).json()
    assert len(found) == 1

    stats = client.get("/api/stats").json()
    assert stats["total_books"] == 1
    assert stats["authors"] == 1


def test_borrow_via_api(client, seeded):
    book_id = seeded["book"].id
    resp = client.post(f"/api/books/{book_id}/borrow", json={"reader_name": "Мария", "days": 14})
    assert resp.status_code == 201
    loan = resp.json()
    assert loan["reader_name"] == "Мария"

    book = client.get(f"/api/books/{book_id}").json()
    assert book["copies_available"] == seeded["book"].copies_total - 1


def test_get_book_404(client):
    assert client.get("/api/books/12345").status_code == 404
