"""Репозиторий книг - доступ к собственному хранилищу (Database per Service)."""

from __future__ import annotations

from app.models import Book
from shared.storage import JsonStorage


class BookRepository:
    def __init__(self, storage: JsonStorage):
        self._storage = storage

    def all(self) -> list[Book]:
        return [Book.from_dict(d) for d in self._storage.all()]

    def get(self, book_id: str) -> Book | None:
        data = self._storage.get(book_id)
        return Book.from_dict(data) if data else None

    def create(self, book: Book) -> Book:
        saved = self._storage.insert(book.to_dict())
        return Book.from_dict(saved)

    def update(self, book_id: str, fields: dict) -> Book | None:
        return self._storage.update(book_id, fields)

    def delete(self, book_id: str) -> bool:
        return self._storage.delete(book_id)