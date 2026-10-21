"""Сервис книг: CRUD, фильтрация, сортировка."""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..exceptions import EntityNotFoundException, ValidationException
from ..models import Author, Book
from ..repositories import AuthorRepository, BookRepository
from ..schemas import BookCreate, BookUpdate


class BookService:
    def __init__(self, db: Session):
        self.db = db
        self.books = BookRepository(db)
        self.authors = AuthorRepository(db)

    def _resolve_author(self, author_id: int) -> Author:
        author = self.authors.get_or_none(author_id)
        if author is None:
            raise EntityNotFoundException(f"Автор с id {author_id} не найден")
        return author

    def create(self, data: BookCreate) -> Book:
        self._resolve_author(data.author_id)
        book = Book(
            title=data.title,
            author_id=data.author_id,
            year=data.year,
            total_copies=data.total_copies,
            available_copies=data.total_copies,
        )
        return self.books.add(book)

    def get(self, book_id: int) -> Book:
        return self.books.get(book_id)

    def search(
        self,
        title: str | None = None,
        author_id: int | None = None,
        year_from: int | None = None,
        available_only: bool = False,
        sort_by: str = "title",
        descending: bool = False,
    ) -> list[Book]:
        return self.books.search(
            title=title,
            author_id=author_id,
            year_from=year_from,
            available_only=available_only,
            sort_by=sort_by,
            descending=descending,
        )

    def update(self, book_id: int, data: BookUpdate) -> Book:
        book = self.books.get(book_id)
        if data.author_id is not None:
            self._resolve_author(data.author_id)
            book.author_id = data.author_id
        if data.title is not None:
            book.title = data.title
        if data.year is not None:
            book.year = data.year
        if data.total_copies is not None:
            currently_on_loan = book.total_copies - book.available_copies
            if data.total_copies < currently_on_loan:
                raise ValidationException(
                    "Нельзя уменьшить общий тираж ниже числа выданных экземпляров"
                )
            delta = data.total_copies - book.total_copies
            book.total_copies = data.total_copies
            book.available_copies = book.available_copies + delta
        self.db.flush()
        return book

    def delete(self, book_id: int) -> None:
        book = self.books.get(book_id)
        if not book.available_copies == book.total_copies:
            raise ValidationException(
                "Нельзя удалить книгу, пока экземпляры находятся на руках"
            )
        self.books.delete(book)