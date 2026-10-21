"""Точка входа REST-приложения «Библиотека»."""

from flask import Flask, jsonify, render_template

from exceptions import ApiError
from models import Book
from repository import BookRepository
from routes import books_api
from service import BookService


def seed_books() -> list[Book]:
    """Начальное содержимое библиотечного фонда."""
    return [
        Book(id=0, title="Мастер и Маргарита", author="Булгаков М.А.", genre="роман", year=1967, price=750.0, available=3),
        Book(id=0, title="Война и мир", author="Толстой Л.Н.", genre="роман", year=1869, price=1200.0, available=2),
        Book(id=0, title="Преступление и наказание", author="Достоевский Ф.М.", genre="роман", year=1866, price=640.0, available=0),
        Book(id=0, title="Собачье сердце", author="Булгаков М.А.", genre="повесть", year=1925, price=410.0, available=4),
        Book(id=0, title="Пикник на обочине", author="Стругацкие А. и Б.", genre="фантастика", year=1972, price=520.0, available=1),
    ]


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

    @app.errorhandler(500)
    def handle_internal_error(error):
        return jsonify({"error": "Internal server error", "code": "INTERNAL_ERROR"}), 500


def create_app(with_seed: bool = True) -> Flask:
    """Собрать приложение: хранилище, сервис, контроллеры, обработчики ошибок."""
    app = Flask(__name__)
    app.json.ensure_ascii = False
    app.json.sort_keys = False

    repository = BookRepository(seed_books() if with_seed else [])
    app.extensions["book_service"] = BookService(repository)

    @app.get("/")
    def index():
        """GET / — страница каталога (витрина поверх REST API)."""
        return render_template("index.html")

    app.register_blueprint(books_api)
    register_error_handlers(app)
    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000)
