"""Точка входа REST-приложения «Библиотека»."""

import sys

from flask import Flask, jsonify

import config
from cache import RedisCache
from db import Database
from exceptions import ApiError
from repository import BookRepository, LoanRepository, ReaderRepository
from routes import books_api, loans_api, readers_api, system_api
from service import BookService, LoanService, ReaderService


def register_error_handlers(app: Flask) -> None:
    """Единый формат ответа для всех ошибок API."""

    @app.errorhandler(ApiError)
    def handle_api_error(error: ApiError):
        return jsonify(error.to_dict()), error.status_code

    @app.errorhandler(404)
    def handle_not_found(error):
        return jsonify({"error": "Resource not found", "code": "NOT_FOUND"}), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        return jsonify({"error": "Method not allowed", "code": "METHOD_NOT_ALLOWED"}), 405

    @app.errorhandler(ValueError)
    def handle_value_error(error: ValueError):
        return jsonify({"error": str(error), "code": "VALIDATION_ERROR"}), 400

    @app.errorhandler(500)
    def handle_internal_error(error):
        return jsonify({"error": "Internal server error", "code": "INTERNAL_ERROR"}), 500


def create_app(database: Database | None = None, cache: RedisCache | None = None, init_db: bool = False) -> Flask:
    """Собрать приложение: БД, кэш, репозитории, сервисы, контроллеры."""
    app = Flask(__name__)
    app.json.ensure_ascii = False
    app.json.sort_keys = False

    database = database or Database(config.DB_PATH)
    if init_db:
        database.reset()

    cache = cache if cache is not None else RedisCache()

    books = BookRepository(database)
    readers = ReaderRepository(database)
    loans = LoanRepository(database)

    book_service = BookService(books, cache if cache.ping() else None)
    app.extensions["database"] = database
    app.extensions["book_service"] = book_service
    app.extensions["reader_service"] = ReaderService(readers, loans)
    app.extensions["loan_service"] = LoanService(database, books, readers, loans, cache if cache.ping() else None)

    app.register_blueprint(books_api)
    app.register_blueprint(loans_api)
    app.register_blueprint(readers_api)
    app.register_blueprint(system_api)

    register_error_handlers(app)
    return app


def main() -> None:
    init_db = "--init-db" in sys.argv
    app = create_app(init_db=init_db)
    print(f"REST API: http://{config.API_HOST}:{config.API_PORT}  (БД: {config.DB_PATH})")
    app.run(host=config.API_HOST, port=config.API_PORT)


if __name__ == "__main__":
    main()
