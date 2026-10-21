"""Бизнес-логика библиотеки.

Слой сервисов не знает, как устроен SQL: он обращается к репозиториям,
а кэш используется по паттерну cache-aside.
"""

import json
from datetime import date, timedelta
from typing import Any

import config
from cache import RedisCache
from db import Database
from exceptions import ApiError, ConflictError, NotFoundError, ValidationError
from models import Book, BookDetails, Loan, Reader
from repository import BookRepository, LoanRepository, ReaderRepository
from schemas import validate_book, validate_loan, validate_reader


class BookService:
    """Операции над книгами: выборка, поиск, изменение, кэширование."""

    def __init__(
        self,
        books: BookRepository,
        cache: RedisCache | None = None,
        cover_base_url: str = config.CDN_BASE_URL,
        cache_ttl: int = config.CACHE_TTL,
    ) -> None:
        self.books = books
        self.cache = cache
        self.cover_base_url = cover_base_url.rstrip("/")
        self.cache_ttl = cache_ttl

    # --- чтение -------------------------------------------------------------
    def list_books(self, filters: dict, sort_by: str | None, order: str) -> list[Book]:
        return self.books.get_all(filters, sort_by, order)

    def get_book(self, book_id: int) -> Book:
        """Cache-aside: сначала Redis, при промахе — SELECT из БД и запись в кэш."""
        key = f"book:{book_id}"
        if self.cache is not None:
            cached = self.cache.get_product_json(key)
            if cached is not None:
                return Book(**json.loads(cached))

        book = self.books.get_by_id(book_id)
        if book is None:
            raise NotFoundError(f"Book with id={book_id} not found")

        if self.cache is not None:
            self.cache.set(key, json.dumps(book.to_dict(), ensure_ascii=False))
        return book

    def get_details(self, book_id: int) -> BookDetails:
        details = self.books.get_details(book_id)
        if details is None:
            raise NotFoundError(f"Book with id={book_id} not found")
        if details.cover_url and not details.cover_url.startswith("http"):
            details.cover_url = f"{self.cover_base_url}/{details.cover_url}"
        return details

    def search(self, query: str) -> list[Book]:
        """Поиск по названию: в PostgreSQL/SQLite — фильтр, в Redis — счётчик запроса."""
        books = self.books.get_all({"q": query}, "title", "asc")
        if not books:
            raise NotFoundError(f"No books found for query '{query}'")
        if self.cache is not None:
            self.cache.record_search(query)
        return books

    def search_history(self, limit: int = 5) -> list[dict[str, Any]]:
        if self.cache is None:
            return []
        return self.cache.search_history(limit)

    def catalog(self, filters: dict, sort_by: str | None, order: str) -> list[dict[str, Any]]:
        """Данные для витрины каталога: книги вместе с ФИО автора и ссылкой на обложку."""
        books = self.books.get_all(filters, sort_by, order)
        authors = {author.id: author.full_name for author in self.books.get_authors()}

        items: list[dict[str, Any]] = []
        for book in books:
            cover = f"{self.cover_base_url}/{book.cover_path}" if book.cover_path else None
            items.append({
                "id": book.id,
                "title": book.title,
                "author": authors.get(book.author_id, "—"),
                "genre": book.genre,
                "year": book.year,
                "price": round(book.price, 2),
                "available_copies": book.available_copies,
                "total_copies": book.total_copies,
                "cover_url": cover,
            })
        return items

    # --- изменение ----------------------------------------------------------
    def create_book(self, payload: dict) -> Book:
        data = validate_book(payload)
        if not self.books.author_exists(data["author_id"]):
            raise ValidationError(f"Author with id={data['author_id']} not found")
        book = self.books.create(data)
        return book

    def replace_book(self, book_id: int, payload: dict) -> Book:
        current = self._require(book_id)
        data = validate_book(payload)
        if not self.books.author_exists(data["author_id"]):
            raise ValidationError(f"Author with id={data['author_id']} not found")
        book = Book(
            id=current.id,
            title=data["title"],
            author_id=data["author_id"],
            genre=data["genre"],
            year=data["year"],
            price=data["price"],
            total_copies=data["total_copies"],
            available_copies=data.get("available_copies", data["total_copies"]),
            cover_path=data.get("cover_path", current.cover_path),
        )
        self.books.update(book)
        self._invalidate(book_id)
        return book

    def patch_book(self, book_id: int, payload: dict) -> Book:
        current = self._require(book_id)
        changes = validate_book(payload, partial=True)
        if "author_id" in changes and not self.books.author_exists(changes["author_id"]):
            raise ValidationError(f"Author with id={changes['author_id']} not found")

        updated = Book(
            id=current.id,
            title=changes.get("title", current.title),
            author_id=changes.get("author_id", current.author_id),
            genre=changes.get("genre", current.genre),
            year=changes.get("year", current.year),
            price=changes.get("price", current.price),
            total_copies=changes.get("total_copies", current.total_copies),
            available_copies=changes.get("available_copies", current.available_copies),
            cover_path=current.cover_path,
        )
        if updated.available_copies > updated.total_copies:
            raise ValidationError("Field 'available_copies' must not exceed 'total_copies'")

        self.books.update(updated)
        self._invalidate(book_id)
        return updated

    def delete_book(self, book_id: int) -> None:
        if not self.books.delete(book_id):
            raise NotFoundError(f"Book with id={book_id} not found")
        self._invalidate(book_id)

    def set_tags(self, book_id: int, tag_names: list[str]) -> list[str]:
        self._require(book_id)
        cleaned = [name.strip().lower() for name in tag_names if name.strip()]
        self.books.set_tags(book_id, cleaned)
        self._invalidate(book_id)
        return self.books.get_tags(book_id)

    # --- статистика ---------------------------------------------------------
    def stats(self) -> dict[str, Any]:
        return {
            "books_total": self.books.count(),
            "by_genre": self.books.genre_stats(),
            "by_author": self.books.author_stats(),
            "by_tag": self.books.tag_stats(),
        }

    # --- вспомогательные ----------------------------------------------------
    def _require(self, book_id: int) -> Book:
        book = self.books.get_by_id(book_id)
        if book is None:
            raise NotFoundError(f"Book with id={book_id} not found")
        return book

    def _invalidate(self, book_id: int) -> None:
        """Инвалидация кэша после изменения данных."""
        if self.cache is not None:
            self.cache.delete(f"book:{book_id}")


class ReaderService:
    """Операции над читателями."""

    def __init__(self, readers: ReaderRepository, loans: LoanRepository) -> None:
        self.readers = readers
        self.loans = loans

    def list_readers(self) -> list[Reader]:
        return self.readers.get_all()

    def get_reader(self, reader_id: int) -> Reader:
        reader = self.readers.get_by_id(reader_id)
        if reader is None:
            raise NotFoundError(f"Reader with id={reader_id} not found")
        return reader

    def create_reader(self, payload: dict) -> Reader:
        data = validate_reader(payload)
        if self.readers.get_by_email(data["email"]) is not None:
            raise ConflictError(f"Reader with email '{data['email']}' already exists")
        data["registered_at"] = date.today().isoformat()
        return self.readers.create(data)

    def reader_loans(self, reader_id: int) -> list[Loan]:
        self.get_reader(reader_id)
        return self.loans.get_by_reader(reader_id)


class LoanService:
    """Выдача и возврат книг. Каждая операция — транзакция."""

    def __init__(
        self,
        database: Database,
        books: BookRepository,
        readers: ReaderRepository,
        loans: LoanRepository,
        cache: RedisCache | None = None,
    ) -> None:
        self.database = database
        self.books = books
        self.readers = readers
        self.loans = loans
        self.cache = cache

    def issue_book(self, payload: dict, today: date | None = None) -> Loan:
        """Оформить выдачу: INSERT в loans + UPDATE остатков — одна транзакция.

        Если на любом шаге возникает ошибка (нет экземпляров, нет читателя),
        выполняется ROLLBACK и в БД не остаётся ни выдачи, ни изменения остатка.
        """
        data = validate_loan(payload)
        taken_at = (today or date.today()).isoformat()
        due_at = ((today or date.today()) + timedelta(days=data["days"])).isoformat()

        if self.readers.get_by_id(data["reader_id"]) is None:
            raise NotFoundError(f"Reader with id={data['reader_id']} not found")

        try:
            with self.database.transaction() as connection:
                row = connection.execute(
                    "SELECT available_copies FROM books WHERE id = ?",
                    (data["book_id"],),
                ).fetchone()
                if row is None:
                    raise NotFoundError(f"Book with id={data['book_id']} not found")
                if row["available_copies"] <= 0:
                    raise ConflictError(f"Book with id={data['book_id']} has no available copies")

                loan_id = self.loans.create(connection, data["book_id"], data["reader_id"], taken_at, due_at)
                cursor = connection.execute(
                    "UPDATE books SET available_copies = available_copies - 1"
                    " WHERE id = ? AND available_copies > 0",
                    (data["book_id"],),
                )
                if cursor.rowcount != 1:
                    raise ConflictError("Book copy was taken by another reader")
        except ApiError:
            raise
        except Exception as error:  # noqa: BLE001 — откат уже выполнен в transaction()
            raise ConflictError(f"Loan transaction rolled back: {error}") from error

        self._invalidate(data["book_id"])
        loan = self.loans.get_by_id(loan_id)
        assert loan is not None
        return loan

    def return_book(self, loan_id: int, today: date | None = None) -> Loan:
        """Вернуть книгу: UPDATE loans + UPDATE остатков в одной транзакции."""
        returned_at = (today or date.today()).isoformat()

        with self.database.transaction() as connection:
            loan = self.loans.get_by_id(loan_id, connection)
            if loan is None:
                raise NotFoundError(f"Loan with id={loan_id} not found")
            if loan.returned_at is not None:
                raise ConflictError(f"Loan with id={loan_id} is already returned")

            updated = self.loans.mark_returned(connection, loan_id, returned_at)
            if updated != 1:
                raise ConflictError(f"Loan with id={loan_id} was changed by another process")

            connection.execute(
                "UPDATE books SET available_copies = MIN(available_copies + 1, total_copies)"
                " WHERE id = ?",
                (loan.book_id,),
            )

        self._invalidate(loan.book_id)
        result = self.loans.get_by_id(loan_id)
        assert result is not None
        return result

    def list_active(self) -> list[dict]:
        return self.loans.get_active()

    def list_overdue(self, today: date | None = None) -> list[dict]:
        return self.loans.get_overdue((today or date.today()).isoformat())

    def _invalidate(self, book_id: int) -> None:
        if self.cache is not None:
            self.cache.delete(f"book:{book_id}")
