"""HTTP-слой: контроллеры REST API библиотеки."""

from flask import Blueprint, Response, jsonify, request

from schemas import parse_book_id, parse_filters, parse_sorting
from service import BookService

books_api = Blueprint("books", __name__, url_prefix="/books")


def get_service() -> BookService:
    """Вернуть сервис, привязанный к текущему приложению."""
    from flask import current_app

    return current_app.extensions["book_service"]


@books_api.get("")
def list_books() -> Response:
    filters = parse_filters(request.args)
    sort_by, order = parse_sorting(request.args)
    books = get_service().list_books(filters, sort_by, order)
    return jsonify([book.to_dict() for book in books])


@books_api.get("/search")
def search_books() -> Response:
    author = request.args.get("author", "")
    books = get_service().search_by_author(author)
    return jsonify({"author": author, "count": len(books), "items": [book.to_dict() for book in books]})


@books_api.get("/<book_id>")
def get_book(book_id: str) -> Response:
    book = get_service().get_book(parse_book_id(book_id))
    return jsonify(book.to_dict())


@books_api.post("")
def create_book() -> tuple[Response, int]:
    book = get_service().create_book(request.get_json(silent=True))
    response = jsonify(book.to_dict())
    response.headers["Location"] = f"/books/{book.id}"
    return response, 201


@books_api.put("/<book_id>")
def replace_book(book_id: str) -> Response:
    book = get_service().replace_book(parse_book_id(book_id), request.get_json(silent=True))
    return jsonify(book.to_dict())


@books_api.patch("/<book_id>")
def patch_book(book_id: str) -> Response:
    book = get_service().patch_book(parse_book_id(book_id), request.get_json(silent=True))
    return jsonify(book.to_dict())


@books_api.delete("/<book_id>")
def delete_book(book_id: str) -> Response:
    get_service().delete_book(parse_book_id(book_id))
    return Response(status=204)
