from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.cache import BookCache
from app.errors import ConflictError, NotFoundError, ValidationError
from app.models import Book
from app.repositories.book import BookRepository


class BookService:
    def __init__(self, repository: BookRepository, cache: BookCache) -> None:
        self.repository = repository
        self.cache = cache

    def list_books(
        self,
        genre: Optional[str] = None,
        author: Optional[str] = None,
        min_rating: Optional[float] = None,
        sort: str = "title",
        order: str = "asc",
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        books, total = self.repository.list(
            genre=genre,
            author=author,
            min_rating=min_rating,
            sort=sort,
            order=order,
            limit=limit,
            offset=offset,
        )
        return [self._to_dict(book) for book in books], total

    def get_book(self, book_id: int) -> Dict[str, Any]:
        cached = self.cache.get(book_id)
        if cached is not None:
            return cached

        book = self.repository.get(book_id)
        if book is None:
            raise NotFoundError(book_id)

        payload = self._to_dict(book)
        self.cache.set(book_id, payload)
        return payload

    def create_book(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if self.repository.get_by_isbn(data["isbn"]) is not None:
            raise ConflictError(f"Книга с ISBN {data['isbn']} уже существует")

        book = Book(**self._normalize(data))
        return self._to_dict(self.repository.add(book))

    def replace_book(self, book_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        book = self.repository.get(book_id)
        if book is None:
            raise NotFoundError(book_id)

        other = self.repository.get_by_isbn(data["isbn"])
        if other is not None and other.id != book_id:
            raise ConflictError(f"Книга с ISBN {data['isbn']} уже существует")

        updated = self.repository.update(book, self._normalize(data))
        self.cache.delete(book_id)
        return self._to_dict(updated)

    def patch_book(self, book_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        book = self.repository.get(book_id)
        if book is None:
            raise NotFoundError(book_id)

        changes = {name: value for name, value in data.items() if value is not None}

        if "isbn" in changes:
            other = self.repository.get_by_isbn(changes["isbn"])
            if other is not None and other.id != book_id:
                raise ConflictError(f"Книга с ISBN {changes['isbn']} уже существует")

        total = changes.get("copies_total", book.copies_total)
        available = changes.get("copies_available", book.copies_available)
        if available > total:
            raise ValidationError("copies_available не может превышать copies_total")

        updated = self.repository.update(book, changes)
        self.cache.delete(book_id)
        return self._to_dict(updated)

    def delete_book(self, book_id: int) -> None:
        book = self.repository.get(book_id)
        if book is None:
            raise NotFoundError(book_id)
        self.repository.delete(book)
        self.cache.delete(book_id)

    def search_books(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        if not query or not query.strip():
            raise ValidationError("Параметр q не может быть пустым")
        books = self.repository.search(query.strip(), limit=limit)
        return [self._to_dict(book) for book in books]

    def statistics(self) -> Dict[str, Any]:
        return self.repository.statistics()

    @staticmethod
    def _normalize(data: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(data)
        if payload.get("copies_available") is None:
            payload["copies_available"] = payload["copies_total"]
        return payload

    @staticmethod
    def _to_dict(book: Book) -> Dict[str, Any]:
        return {
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "genre": book.genre,
            "year": book.year,
            "isbn": book.isbn,
            "publisher": book.publisher,
            "copies_total": book.copies_total,
            "copies_available": book.copies_available,
            "rating": float(book.rating),
        }
