from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from app.models import Book, Loan, Reader
from app.repositories.repositories import (
    AuthorRepository,
    BookRepository,
    LoanRepository,
    ReaderRepository,
)

logger = logging.getLogger("library.service")


class ValidationError(Exception):
    code = "VALIDATION_ERROR"


class NotFoundError(Exception):
    code = "NOT_FOUND"

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ConflictError(Exception):
    code = "CONFLICT"


class LibraryService:
    def __init__(self, session) -> None:
        self.session = session
        self.books = BookRepository(session)
        self.authors = AuthorRepository(session)
        self.readers = ReaderRepository(session)
        self.loans = LoanRepository(session)

    def list_books(
        self,
        search: Optional[str] = None,
        genre: Optional[str] = None,
        available_only: bool = False,
        sort: str = "title",
        order: str = "asc",
    ) -> List[Book]:
        return list(
            self.books.list(
                search=search,
                genre=genre,
                available_only=available_only,
                sort=sort,
                order=order,
            )
        )

    def get_book(self, book_id: int) -> Book:
        book = self.books.get(book_id)
        if book is None:
            raise NotFoundError(f"Книга #{book_id} не найдена")
        return book

    def create_book(self, data: Dict[str, Any]) -> Book:
        fields = self._validate_book(data)
        try:
            book = self.books.create(fields)
            logger.info("Создана книга #%s «%s»", book.id, book.title)
            return book
        except Exception as error:
            self.session.rollback()
            if "UNIQUE" in str(error).upper() or "unique" in str(error):
                raise ConflictError("Книга с таким ISBN уже существует") from error
            raise

    def update_book(self, book_id: int, data: Dict[str, Any]) -> Book:
        book = self.get_book(book_id)
        fields = self._validate_book(data, book=book)
        updated = self.books.update(book, fields)
        logger.info("Изменена книга #%s", book_id)
        return updated

    def delete_book(self, book_id: int) -> None:
        book = self.get_book(book_id)
        self.books.delete(book)
        logger.info("Удалена книга #%s «%s»", book_id, book.title)

    def genres(self) -> List[str]:
        return list(self.books.genres())

    def statistics(self) -> Dict[str, Any]:
        stats = self.books.statistics()
        stats["readers"] = len(self.readers.list())
        stats["active_loans"] = len(self.loans.active())
        return stats

    def issue_book(self, book_id: int, reader_id: int, days: int = 14) -> Loan:
        book = self.get_book(book_id)
        reader = self.readers.get(reader_id)
        if reader is None:
            raise NotFoundError(f"Читатель #{reader_id} не найден")
        if not 1 <= days <= 90:
            raise ValidationError("Срок выдачи должен быть от 1 до 90 дней")

        try:
            if book.copies_available <= 0:
                raise ValidationError("Свободных экземпляров нет")
            if self.loans.active_for(book, reader) is not None:
                raise ValidationError("Эта книга уже выдана данному читателю")

            book.copies_available -= 1
            loan = self.loans.create(book, reader, days)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        logger.info(
            "Выдана книга #%s читателю #%s, срок %s дн.",
            book_id,
            reader_id,
            days,
        )
        return loan

    def return_book(self, loan_id: int) -> Loan:
        loan = self.loans.get(loan_id)
        if loan is None:
            raise NotFoundError(f"Выдача #{loan_id} не найдена")
        if loan.return_date is not None:
            raise ValidationError("Книга уже возвращена")

        try:
            loan.return_date = date.today()
            book = self.books.get(loan.book_id)
            if book is not None and book.copies_available < book.copies_total:
                book.copies_available += 1
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        logger.info("Возврат по выдаче #%s (книга #%s)", loan.id, loan.book_id)
        return loan

    def reader_loans(self, reader_id: int) -> List[Loan]:
        reader = self.readers.get(reader_id)
        if reader is None:
            raise NotFoundError(f"Читатель #{reader_id} не найден")
        return list(self.loans.by_reader(reader_id))

    def _validate_book(self, data: Dict[str, Any], book: Optional[Book] = None) -> Dict[str, Any]:
        title = str(data.get("title") or "").strip()
        if not title:
            raise ValidationError("Название книги обязательно")

        author_id = data.get("author_id")
        if author_id is None or not str(author_id).isdigit():
            raise ValidationError("Выберите автора")
        if self.authors.get(int(author_id)) is None:
            raise ValidationError("Автор не найден")

        genre = str(data.get("genre") or "").strip()
        if not genre:
            raise ValidationError("Жанр обязателен")

        try:
            year = int(data.get("year"))
        except (TypeError, ValueError) as error:
            raise ValidationError("Год должен быть числом") from error
        if not 1400 <= year <= 2100:
            raise ValidationError("Год должен быть в диапазоне 1400-2100")

        isbn = str(data.get("isbn") or "").strip()
        if not isbn.isdigit() or len(isbn) not in (10, 13):
            raise ValidationError("ISBN должен содержать 10 или 13 цифр")

        try:
            price = Decimal(str(data.get("price") or "0").replace(",", "."))
        except InvalidOperation as error:
            raise ValidationError("Цена должна быть числом") from error
        if price < 0:
            raise ValidationError("Цена не может быть отрицательной")

        try:
            total = int(data.get("copies_total") or 1)
            available = data.get("copies_available")
            available = total if available in (None, "") else int(available)
        except (TypeError, ValueError) as error:
            raise ValidationError("Количество экземпляров должно быть целым") from error
        if total < 0 or not 0 <= available <= total:
            raise ValidationError("Некорректное количество экземпляров")

        return {
            "title": title,
            "author_id": int(author_id),
            "genre": genre,
            "year": year,
            "isbn": isbn,
            "price": price,
            "copies_total": total,
            "copies_available": available,
        }
