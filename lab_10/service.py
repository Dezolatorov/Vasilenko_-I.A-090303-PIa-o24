"""Бизнес-логика библиотечного фонда."""

from exceptions import NotFoundError
from models import Book
from repository import BookRepository
from schemas import validate_book


class BookService:
    """Операции над книгами: выборка, поиск, создание, изменение, удаление."""

    def __init__(self, repository: BookRepository) -> None:
        self.repository = repository

    def list_books(self, filters: dict, sort_by: str | None, order: str) -> list[Book]:
        books = [book for book in self.repository.get_all() if self._matches(book, filters)]
        if sort_by:
            books.sort(key=lambda book: getattr(book, sort_by), reverse=order == "desc")
        return books

    def get_book(self, book_id: int) -> Book:
        book = self.repository.get_by_id(book_id)
        if book is None:
            raise NotFoundError(f"Book with id={book_id} not found")
        return book

    def create_book(self, payload: dict) -> Book:
        data = validate_book(payload)
        return self.repository.create(Book(id=0, **data))

    def replace_book(self, book_id: int, payload: dict) -> Book:
        self.get_book(book_id)
        data = validate_book(payload)
        return self.repository.update(Book(id=book_id, **data))

    def patch_book(self, book_id: int, payload: dict) -> Book:
        book = self.get_book(book_id)
        changes = validate_book(payload, partial=True)
        updated = Book(
            id=book.id,
            title=changes.get("title", book.title),
            author=changes.get("author", book.author),
            genre=changes.get("genre", book.genre),
            year=changes.get("year", book.year),
            price=changes.get("price", book.price),
            available=changes.get("available", book.available),
        )
        return self.repository.update(updated)

    def delete_book(self, book_id: int) -> None:
        if not self.repository.delete(book_id):
            raise NotFoundError(f"Book with id={book_id} not found")

    def search_by_author(self, author: str) -> list[Book]:
        query = author.strip().lower()
        if not query:
            raise NotFoundError("Author is not specified")
        books = [
            book
            for book in self.repository.get_all()
            if query in book.author.lower()
        ]
        books.sort(key=lambda book: (book.author.lower(), book.title.lower()))
        return books

    @staticmethod
    def _matches(book: Book, filters: dict) -> bool:
        if "author" in filters and filters["author"] not in book.author.lower():
            return False
        if "genre" in filters and filters["genre"] != book.genre.lower():
            return False
        if "available" in filters:
            has_copies = book.available > 0
            if has_copies != filters["available"]:
                return False
        if "min_price" in filters and book.price < filters["min_price"]:
            return False
        if "max_price" in filters and book.price > filters["max_price"]:
            return False
        if "year_from" in filters and book.year < filters["year_from"]:
            return False
        if "year_to" in filters and book.year > filters["year_to"]:
            return False
        return True
