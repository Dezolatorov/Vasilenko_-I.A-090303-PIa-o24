"""Сервисный слой books-service: бизнес-логика каталога и доступности книг."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.models import Book
from app.schemas.schemas import BookCreate, BookUpdate

if TYPE_CHECKING:
    from app.repositories import BookRepository


class BooksService:
    def __init__(self, repository: "BookRepository"):
        self._repository = repository

    def list_books(self) -> list[Book]:
        return self._repository.all()

    def get_book(self, book_id: str) -> Book | None:
        return self._repository.get(book_id)

    def create_book(self, payload: BookCreate) -> Book:
        book = Book(
            title=payload.title,
            author=payload.author,
            total_copies=payload.total_copies,
            available_copies=payload.total_copies,
        )
        return self._repository.create(book)

    def update_book(self, book_id: str, payload: BookUpdate) -> Book | None:
        fields = payload.model_dump(exclude_none=True)
        if "total_copies" in fields and "available_copies" not in fields:
            current = self._repository.get(book_id)
            if current is not None:
                diff = fields["total_copies"] - current.total_copies
                fields["available_copies"] = max(0, current.available_copies + diff)
        if not fields:
            return None
        return self._repository.update(book_id, fields)

    def delete_book(self, book_id: str) -> bool:
        return self._repository.delete(book_id)

    def check_availability(self, book_id: str) -> dict:
        """Проверка доступности - реальный запрос из loans-service (межсервисное взаимодействие)."""
        book = self._repository.get(book_id)
        if book is None:
            return {"exists": False, "available": False}
        return {"exists": True, "available": book.available_copies > 0, "available_copies": book.available_copies}

    def decrement_stock(self, book_id: str) -> bool:
        """Атомарно уменьшить доступный фонд при выдаче. False если нет экземпляров."""
        book = self._repository.get(book_id)
        if book is None or book.available_copies <= 0:
            return False
        updated = self._repository.update(book_id, {"available_copies": book.available_copies - 1})
        return updated is not None

    def increment_stock(self, book_id: str) -> bool:
        book = self._repository.get(book_id)
        if book is None or book.available_copies >= book.total_copies:
            return False
        updated = self._repository.update(book_id, {"available_copies": book.available_copies + 1})
        return updated is not None