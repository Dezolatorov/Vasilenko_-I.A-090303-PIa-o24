from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.database import get_session
from app.services.services import ConflictError, LibraryService, NotFoundError, ValidationError

api = Blueprint("api", __name__, url_prefix="/api")


def service() -> LibraryService:
    return LibraryService(get_session())


def book_to_dict(book) -> dict:
    return {
        "id": book.id,
        "title": book.title,
        "author_id": book.author_id,
        "author": book.author.full_name,
        "genre": book.genre,
        "year": book.year,
        "isbn": book.isbn,
        "price": float(book.price),
        "copies_total": book.copies_total,
        "copies_available": book.copies_available,
    }


@api.get("/books")
def list_books():
    library = service()
    items = library.list_books(
        search=request.args.get("search") or None,
        genre=request.args.get("genre") or None,
        available_only=request.args.get("available") == "1",
        sort=request.args.get("sort", "title"),
        order=request.args.get("order", "asc"),
    )
    limit = min(int(request.args.get("limit", 20)), 100)
    offset = max(int(request.args.get("offset", 0)), 0)
    return jsonify(
        {
            "total": len(items),
            "limit": limit,
            "offset": offset,
            "items": [book_to_dict(book) for book in items[offset : offset + limit]],
        }
    )


@api.get("/books/<int:book_id>")
def get_book(book_id: int):
    return jsonify(book_to_dict(service().get_book(book_id)))


@api.post("/books")
def create_book():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationError("Тело запроса должно быть JSON-объектом")
    book = service().create_book(payload)
    return jsonify(book_to_dict(book)), 201


@api.put("/books/<int:book_id>")
def replace_book(book_id: int):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationError("Тело запроса должно быть JSON-объектом")
    book = service().update_book(book_id, payload)
    return jsonify(book_to_dict(book))


@api.patch("/books/<int:book_id>")
def patch_book(book_id: int):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationError("Тело запроса должно быть JSON-объектом")

    library = service()
    book = library.get_book(book_id)
    merged = {
        "title": book.title,
        "author_id": book.author_id,
        "genre": book.genre,
        "year": book.year,
        "isbn": book.isbn,
        "price": book.price,
        "copies_total": book.copies_total,
        "copies_available": book.copies_available,
    }
    merged.update({key: value for key, value in payload.items() if value is not None})
    updated = library.update_book(book_id, merged)
    return jsonify(book_to_dict(updated))


@api.delete("/books/<int:book_id>")
def delete_book(book_id: int):
    service().delete_book(book_id)
    return "", 204


@api.get("/books/search")
def search_books():
    query = request.args.get("q", "").strip()
    if not query:
        raise ValidationError("Параметр q обязателен")
    items = service().list_books(search=query)
    return jsonify({"query": query, "count": len(items), "items": [book_to_dict(b) for b in items]})


@api.get("/statistics")
def statistics():
    stats = service().statistics()
    return jsonify(
        {
            "books": stats["books"],
            "copies_total": stats["copies_total"],
            "copies_available": stats["copies_available"],
            "average_price": float(stats["avg_price"]),
            "by_genre": stats["by_genre"],
            "readers": stats["readers"],
            "active_loans": stats["active_loans"],
        }
    )
