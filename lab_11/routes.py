"""HTTP-слой: контроллеры REST API библиотеки."""

from flask import Blueprint, Response, current_app, jsonify, render_template, request

from schemas import (
    parse_filters,
    parse_limit,
    parse_positive_id,
    parse_search_query,
    parse_sorting,
)
from service import BookService, LoanService, ReaderService

books_api = Blueprint("books", __name__, url_prefix="/books")
loans_api = Blueprint("loans", __name__, url_prefix="/loans")
readers_api = Blueprint("readers", __name__, url_prefix="/readers")
system_api = Blueprint("system", __name__)


def book_service() -> BookService:
    return current_app.extensions["book_service"]


def loan_service() -> LoanService:
    return current_app.extensions["loan_service"]


def reader_service() -> ReaderService:
    return current_app.extensions["reader_service"]


@books_api.get("")
def list_books() -> Response:
    """GET /books — список книг с фильтрацией и сортировкой (SELECT)."""
    filters = parse_filters(request.args)
    sort_by, order = parse_sorting(request.args)
    books = book_service().list_books(filters, sort_by, order)
    return jsonify({"count": len(books), "items": [book.to_dict() for book in books]})


@books_api.get("/search")
def search_books() -> Response:
    """GET /books/search?q= — поиск по названию, запрос учитывается в Redis."""
    query = parse_search_query(request.args)
    books = book_service().search(query)
    return jsonify({"query": query, "count": len(books), "items": [book.to_dict() for book in books]})


@books_api.get("/search-history")
def search_history() -> Response:
    """GET /books/search-history — история поиска из Redis."""
    limit = parse_limit(request.args, default=5, maximum=20)
    return jsonify({"source": "redis", "items": book_service().search_history(limit)})


@books_api.get("/<book_id>")
def get_book(book_id: str) -> Response:
    """GET /books/{id} — cache-aside: Redis → SQLite → Redis."""
    book = book_service().get_book(parse_positive_id(book_id, "book"))
    return jsonify(book.to_dict())


@books_api.get("/<book_id>/details")
def get_book_details(book_id: str) -> Response:
    """GET /books/{id}/details — JOIN автора и тегов (связь N:M)."""
    details = book_service().get_details(parse_positive_id(book_id, "book"))
    return jsonify(details.to_dict())


@books_api.post("")
def create_book() -> tuple[Response, int]:
    book = book_service().create_book(request.get_json(silent=True))
    response = jsonify(book.to_dict())
    response.headers["Location"] = f"/books/{book.id}"
    return response, 201


@books_api.put("/<book_id>")
def replace_book(book_id: str) -> Response:
    book = book_service().replace_book(parse_positive_id(book_id, "book"), request.get_json(silent=True))
    return jsonify(book.to_dict())


@books_api.patch("/<book_id>")
def patch_book(book_id: str) -> Response:
    book = book_service().patch_book(parse_positive_id(book_id, "book"), request.get_json(silent=True))
    return jsonify(book.to_dict())


@books_api.delete("/<book_id>")
def delete_book(book_id: str) -> Response:
    book_service().delete_book(parse_positive_id(book_id, "book"))
    return Response(status=204)


@books_api.put("/<book_id>/tags")
def set_tags(book_id: str) -> Response:
    """PUT /books/{id}/tags — переписать набор тегов (INSERT в book_tags)."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not isinstance(payload.get("tags"), list):
        raise ValueError("Request body must be {'tags': [...]}")
    tags = book_service().set_tags(parse_positive_id(book_id, "book"), payload["tags"])
    return jsonify({"book_id": int(book_id), "tags": tags})


@loans_api.get("")
def list_loans() -> Response:
    """GET /loans — активные выдачи (JOIN books + readers)."""
    return jsonify({"count": len(loan_service().list_active()), "items": loan_service().list_active()})


@loans_api.get("/overdue")
def list_overdue() -> Response:
    """GET /loans/overdue — просроченные выдачи."""
    items = loan_service().list_overdue()
    return jsonify({"count": len(items), "items": items})


@loans_api.post("")
def issue_book() -> tuple[Response, int]:
    """POST /loans — выдача книги, транзакция INSERT + UPDATE."""
    loan = loan_service().issue_book(request.get_json(silent=True))
    return jsonify(loan.to_dict()), 201


@loans_api.post("/<loan_id>/return")
def return_book(loan_id: str) -> Response:
    loan = loan_service().return_book(parse_positive_id(loan_id, "loan"))
    return jsonify(loan.to_dict())


@readers_api.get("")
def list_readers() -> Response:
    items = reader_service().list_readers()
    return jsonify({"count": len(items), "items": [reader.to_dict() for reader in items]})


@readers_api.get("/<reader_id>")
def get_reader(reader_id: str) -> Response:
    reader = reader_service().get_reader(parse_positive_id(reader_id, "reader"))
    return jsonify(reader.to_dict())


@readers_api.get("/<reader_id>/loans")
def reader_loans(reader_id: str) -> Response:
    loans = reader_service().reader_loans(parse_positive_id(reader_id, "reader"))
    return jsonify({"count": len(loans), "items": [loan.to_dict() for loan in loans]})


@readers_api.post("")
def create_reader() -> tuple[Response, int]:
    reader = reader_service().create_reader(request.get_json(silent=True))
    response = jsonify(reader.to_dict())
    response.headers["Location"] = f"/readers/{reader.id}"
    return response, 201


@system_api.get("/catalog")
def catalog() -> Response:
    """GET /catalog — данные витрины: книги с автором и ссылкой на обложку в CDN."""
    filters = parse_filters(request.args)
    sort_by, order = parse_sorting(request.args)
    items = book_service().catalog(filters, sort_by, order)
    return jsonify({"count": len(items), "items": items})


@system_api.get("/")
def index():
    """GET / — страница каталога библиотеки (REST API + CDN)."""
    return render_template("index.html", cdn_url=book_service().cover_base_url)


@system_api.get("/stats")
def stats() -> Response:
    """GET /stats — агрегаты SQL: GROUP BY, HAVING, COUNT, AVG."""
    return jsonify(book_service().stats())


@system_api.get("/stats/authors")
def author_stats() -> Response:
    return jsonify({"items": book_service().books.author_stats()})


@system_api.get("/cache/stats")
def cache_stats() -> Response:
    return jsonify(book_service().cache.stats() if book_service().cache else {"backend": "disabled"})


@system_api.get("/cache/keys")
def cache_keys() -> Response:
    cache = book_service().cache
    pattern = request.args.get("pattern", "*")
    return jsonify({"keys": cache.keys(pattern) if cache else []})


@system_api.get("/health")
def health() -> Response:
    cache = book_service().cache
    return jsonify({
        "status": "ok",
        "database": "sqlite",
        "cache": "redis" if cache and cache.ping() else "unavailable",
        "cache_ttl": cache.ttl if cache else None,
    })
