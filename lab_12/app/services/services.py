from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Optional, Sequence

from sqlalchemy.exc import IntegrityError, StatementError
from sqlalchemy.orm import selectinload

from app.database import Database
from app.errors import (
    DuplicateError,
    ForeignKeyError,
    NotFoundError,
    TransactionError,
    ValidationError,
)
from app.models import Book, Loan, Reader
from app.repositories.repositories import BookRepository, LoanRepository, ReaderRepository

MAX_LOAN_DAYS = 90


class LibraryService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def add_book(
        self,
        title: str,
        author: str,
        genre: str,
        year: int,
        price: Any,
        copies_total: int,
        copies_available: Optional[int] = None,
    ) -> Book:
        data = self._validate_book(
            {
                "title": title,
                "author": author,
                "genre": genre,
                "year": year,
                "price": price,
                "copies_total": copies_total,
                "copies_available": copies_available,
            }
        )
        with self.database.session() as session:
            try:
                book = Book(**data)
                BookRepository(session).add(book)
                session.commit()
            except IntegrityError as error:
                session.rollback()
                raise ValidationError(f"Нарушение ограничений целостности: {error.orig}") from error
        return book

    def get_book(self, book_id: int) -> Book:
        with self.database.session() as session:
            book = BookRepository(session).get(book_id)
        if book is None:
            raise NotFoundError("Книга", book_id)
        return book

    def list_books(
        self,
        sort: str = "title",
        descending: bool = False,
        min_price: Any = None,
        max_price: Any = None,
        available_only: bool = False,
        offset: int = 0,
        limit: int = 50,
    ) -> Sequence[Book]:
        with self.database.session() as session:
            books = BookRepository(session).list(
                sort=sort,
                descending=descending,
                offset=offset,
                limit=limit,
                min_price=Decimal(str(min_price)) if min_price is not None else None,
                max_price=Decimal(str(max_price)) if max_price is not None else None,
                available_only=available_only,
            )
        return books

    def search_books(self, query: str) -> Sequence[Book]:
        if not query or not query.strip():
            raise ValidationError("Строка поиска не может быть пустой")
        with self.database.session() as session:
            return BookRepository(session).search(query.strip())

    def books_by_author(self, author: str) -> Sequence[Book]:
        with self.database.session() as session:
            return BookRepository(session).by_author(author)

    def update_book(self, book_id: int, **fields: Any) -> Book:
        allowed = {"title", "author", "genre", "year", "price", "copies_total", "copies_available"}
        unknown = set(fields) - allowed
        if unknown:
            raise ValidationError(f"Неизвестные поля: {', '.join(sorted(unknown))}")

        with self.database.session() as session:
            book = BookRepository(session).get(book_id)
            if book is None:
                raise NotFoundError("Книга", book_id)

            for name, value in fields.items():
                setattr(book, name, value)

            try:
                self._validate_book(
                    {
                        "title": book.title,
                        "author": book.author,
                        "genre": book.genre,
                        "year": book.year,
                        "price": book.price,
                        "copies_total": book.copies_total,
                        "copies_available": book.copies_available,
                    }
                )
                session.commit()
            except (IntegrityError, StatementError) as error:
                session.rollback()
                raise ValidationError(f"Некорректные данные: {error}") from error
        return book

    def delete_book(self, book_id: int) -> None:
        with self.database.session() as session:
            repository = BookRepository(session)
            book = repository.get(book_id)
            if book is None:
                raise NotFoundError("Книга", book_id)
            try:
                repository.delete(book)
                session.commit()
            except IntegrityError as error:
                session.rollback()
                raise ForeignKeyError("Книгу нельзя удалить: на неё ссылаются выдачи") from error

    def add_reader(self, full_name: str, email: str, phone: Optional[str] = None) -> Reader:
        if not full_name or not full_name.strip():
            raise ValidationError("ФИО читателя не может быть пустым")
        if not email or "@" not in email:
            raise ValidationError("E-mail должен содержать символ @")

        with self.database.session() as session:
            repository = ReaderRepository(session)
            if repository.get_by_email(email) is not None:
                raise DuplicateError(f"Читатель с e-mail {email} уже существует")
            reader = Reader(full_name=full_name.strip(), email=email.strip(), phone=phone)
            try:
                repository.add(reader)
                session.commit()
            except IntegrityError as error:
                session.rollback()
                raise DuplicateError(f"Нарушено уникальное ограничение: {error.orig}") from error
        return reader

    def get_reader(self, reader_id: int) -> Reader:
        with self.database.session() as session:
            reader = ReaderRepository(session).get(reader_id)
        if reader is None:
            raise NotFoundError("Читатель", reader_id)
        return reader

    def list_readers(self) -> Sequence[Reader]:
        with self.database.session() as session:
            return ReaderRepository(session).list()

    def delete_reader(self, reader_id: int) -> None:
        with self.database.session() as session:
            repository = ReaderRepository(session)
            reader = repository.get(reader_id)
            if reader is None:
                raise NotFoundError("Читатель", reader_id)
            repository.delete(reader)
            session.commit()

    def issue_book(self, book_id: int, reader_id: int, days: int = 14) -> Loan:
        if not isinstance(days, int) or not 1 <= days <= MAX_LOAN_DAYS:
            raise ValidationError(f"Срок выдачи должен быть от 1 до {MAX_LOAN_DAYS} дней")

        with self.database.session() as session:
            books = BookRepository(session)
            readers = ReaderRepository(session)
            loans = LoanRepository(session)

            book = books.get(book_id)
            if book is None:
                raise NotFoundError("Книга", book_id)
            reader = readers.get(reader_id)
            if reader is None:
                raise NotFoundError("Читатель", reader_id)

            try:
                if book.copies_available <= 0:
                    raise ValidationError("Свободных экземпляров нет")
                if loans.active_for(book, reader) is not None:
                    raise ValidationError("Эта книга уже выдана данному читателю")

                book.copies_available -= 1
                loan = loans.add(book, reader, days)
                session.commit()
            except Exception:
                session.rollback()
                raise
        return loan

    def return_loan(self, loan_id: int) -> Loan:
        with self.database.session() as session:
            loans = LoanRepository(session)
            books = BookRepository(session)
            loan = loans.get(loan_id)
            if loan is None:
                raise NotFoundError("Выдача", loan_id)
            if loan.return_date is not None:
                raise ValidationError("Книга уже возвращена")

            try:
                loan.return_date = date.today()
                book = books.get(loan.book_id)
                if book.copies_available < book.copies_total:
                    book.copies_available += 1
                session.commit()
            except Exception:
                session.rollback()
                raise TransactionError("Не удалось выполнить возврат книги") from None
        return loan

    def reader_loans(self, reader_id: int) -> list[dict]:
        with self.database.session() as session:
            reader = ReaderRepository(session).get(reader_id)
            if reader is None:
                raise NotFoundError("Читатель", reader_id)
            rows = LoanRepository(session).by_reader(reader_id)
            return [self._loan_row(loan) for loan in rows]

    def active_loans(self) -> list[dict]:
        with self.database.session() as session:
            return [self._loan_row(loan) for loan in LoanRepository(session).active()]

    def overdue_loans(self) -> list[dict]:
        with self.database.session() as session:
            return [self._loan_row(loan) for loan in LoanRepository(session).overdue()]

    def statistics(self) -> dict:
        with self.database.session() as session:
            stats = BookRepository(session).statistics()
            stats["readers"] = len(ReaderRepository(session).list(limit=10_000))
            stats["active_loans"] = len(LoanRepository(session).active())
            stats["overdue_loans"] = len(LoanRepository(session).overdue())
        return stats

    @staticmethod
    def _loan_row(loan: Loan) -> dict:
        return {
            "id": loan.id,
            "book": loan.book.title,
            "reader": loan.reader.full_name,
            "loan_date": loan.loan_date,
            "due_date": loan.due_date,
            "return_date": loan.return_date,
        }

    @staticmethod
    def _validate_book(data: dict) -> dict:
        title = str(data.get("title") or "").strip()
        author = str(data.get("author") or "").strip()
        genre = str(data.get("genre") or "").strip()
        if not title:
            raise ValidationError("Название книги не может быть пустым")
        if not author:
            raise ValidationError("Автор книги не может быть пустым")
        if not genre:
            raise ValidationError("Жанр не может быть пустым")

        try:
            year = int(data["year"])
        except (TypeError, ValueError) as error:
            raise ValidationError("Год издания должен быть целым числом") from error
        if not 1400 <= year <= 2100:
            raise ValidationError("Год издания должен быть в диапазоне 1400-2100")

        try:
            price = Decimal(str(data["price"]))
        except Exception as error:
            raise ValidationError("Цена должна быть числом") from error
        if price < 0:
            raise ValidationError("Цена не может быть отрицательной")

        try:
            copies_total = int(data["copies_total"])
        except (TypeError, ValueError) as error:
            raise ValidationError("Количество экземпляров должно быть целым") from error
        if copies_total < 0:
            raise ValidationError("Количество экземпляров не может быть отрицательным")

        available = data.get("copies_available")
        copies_available = copies_total if available is None else int(available)
        if not 0 <= copies_available <= copies_total:
            raise ValidationError("Доступных экземпляров не может быть больше общего количества")

        return {
            "title": title,
            "author": author,
            "genre": genre,
            "year": year,
            "price": price,
            "copies_total": copies_total,
            "copies_available": copies_available,
        }
