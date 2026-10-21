"""Сервисный слой — бизнес-логика предметной области «Библиотека».

Бизнес-правила (проверка доступности, валидация ввода, сроки выдачи,
просрочки) вынесены из Telegram-обработчиков в сервис. Обработчики только
передают данные между Telegram и сервисом (требование методички 16.10, 19).
"""
from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Sequence

from config import LOAN_DAYS

from database import repository as repo
from database.models import Book, BookDraft, NewLoan, Reader

_ISBN_RE = re.compile(r"^\d{10}$|^\d{13}$")


class LibraryError(Exception):
    """Бизнес-ошибка с понятным пользователю сообщением."""


# --------------------------------------------------------------------------
# Валидация пользовательского ввода (методичка 16.5, 19)
# --------------------------------------------------------------------------

def normalize_year(raw: str) -> int:
    """Парсит год из строки. Требует целое число в разумном диапазоне."""
    value = raw.strip()
    if not value.isdigit():
        raise LibraryError("Год должен быть целым числом, например 1999.")
    year = int(value)
    if year < 1450 or year > 2100:
        raise LibraryError("Год издания должен быть в диапазоне 1450–2100.")
    return year


def normalize_copies(raw: str) -> int:
    """Парсит количество экземпляров: целое от 1 до 100."""
    value = raw.strip()
    if not value.isdigit():
        raise LibraryError("Количество экземпляров должно быть целым числом.")
    copies = int(value)
    if copies < 1 or copies > 100:
        raise LibraryError("Количество экземпляров должно быть в диапазоне 1–100.")
    return copies


def normalize_isbn(raw: str) -> str | None:
    """Нормализует ISBN; пустой ввод допустим (None), иначе 10 или 13 цифр."""
    value = raw.replace("-", "").replace(" ", "").strip()
    if not value:
        return None
    if not value.isdigit():
        raise LibraryError("ISBN должен содержать только цифры (10 или 13).")
    if len(value) not in (10, 13):
        raise LibraryError("ISBN должен содержать 10 или 13 цифр.")
    return value


def validate_book_draft(draft: BookDraft) -> None:
    """Проверяет, что черновик книги заполнен и согласован."""
    if not draft.title.strip():
        raise LibraryError("Название книги не может быть пустым.")
    if not draft.author_name.strip():
        raise LibraryError("Имя автора не может быть пустым.")
    if draft.copies_available > draft.copies_total:
        raise LibraryError(
            "Доступных экземпляров не может быть больше, чем всего экземпляров."
        )


# --------------------------------------------------------------------------
# CRUD — создание / просмотр / изменение / удаление (методичка 16.7)
# --------------------------------------------------------------------------

async def add_book(
    title: str,
    author_name: str,
    year: int | None,
    isbn: str | None,
    copies_total: int,
) -> Book:
    draft = BookDraft(
        title=title,
        author_name=author_name,
        year=year,
        isbn=isbn,
        copies_total=copies_total,
        copies_available=copies_total,
    )
    validate_book_draft(draft)
    author = await repo.get_or_create_author(author_name)
    return await repo.create_book(
        title=draft.title,
        author=author,
        year=draft.year,
        isbn=draft.isbn,
        copies_total=draft.copies_total,
        copies_available=draft.copies_total,
    )


async def edit_book(
    book_id: int,
    title: str,
    author_name: str,
    year: int | None,
    isbn: str | None,
    copies_total: int,
    copies_available: int,
) -> Book | None:
    draft = BookDraft(
        title=title,
        author_name=author_name,
        year=year,
        isbn=isbn,
        copies_total=copies_total,
        copies_available=copies_available,
    )
    validate_book_draft(draft)
    author = await repo.get_or_create_author(author_name)
    return await repo.update_book(
        book_id=book_id,
        title=draft.title,
        author=author,
        year=draft.year,
        isbn=draft.isbn,
        copies_total=draft.copies_total,
        copies_available=draft.copies_available,
    )


async def remove_book(book_id: int) -> bool:
    return await repo.delete_book(book_id)


async def get_book(book_id: int) -> Book | None:
    return await repo.get_book(book_id)


async def list_books() -> Sequence[Book]:
    return await repo.list_books()


# --------------------------------------------------------------------------
# Регистрация читателя
# --------------------------------------------------------------------------

async def register_reader(telegram_id: int, full_name: str) -> Reader:
    name = full_name.strip()
    if not name:
        raise LibraryError("Имя не может быть пустым.")
    return await repo.create_reader(telegram_id, name)


async def ensure_reader(telegram_id: int, full_name: str) -> Reader:
    reader = await repo.get_reader_by_telegram(telegram_id)
    if reader is None:
        reader = await register_reader(telegram_id, full_name)
    return reader


async def get_reader_by_telegram_id(telegram_id: int) -> Reader | None:
    return await repo.get_reader_by_telegram(telegram_id)


# --------------------------------------------------------------------------
# Поиск (методичка 16.8)
# --------------------------------------------------------------------------

async def search_books(query: str, author_name: str = "") -> Sequence[Book]:
    return await repo.search_books(query, author_name)


# --------------------------------------------------------------------------
# Выдача и возврат (методичка: функции варианта 2)
# --------------------------------------------------------------------------

async def lend_book(book_id: int, telegraph_id: int, reader_name: str, today: date | None = None) -> Loan:
    today = today or date.today()
    book = await repo.get_book(book_id)
    if book is None:
        raise LibraryError("Книга не найдена.")
    if book.copies_available <= 0:
        raise LibraryError("Нет доступных экземпляров этой книги.")
    reader = await ensure_reader(telegraph_id, reader_name)
    if await repo.is_book_with_reader(book_id, reader.id):
        raise LibraryError("Эта книга уже выдана этому читателю.")
    new = NewLoan(
        book_id=book.id,
        reader_id=reader.id,
        issued_at=today,
        due_date=today + timedelta(days=LOAN_DAYS),
    )
    return await repo.create_loan(new)


async def return_book(loan_id: int) -> bool:
    return await repo.return_loan(loan_id)


async def reader_active_loans(reader_id: int) -> Sequence[Loan]:
    active = await repo.list_loans_by_reader(reader_id)
    return [ln for ln in active if ln.returned_at is None]


async def my_loans(reader_id: int) -> Sequence[Loan]:
    return await repo.list_loans_by_reader(reader_id)


async def overdue_loans(today: date | None = None) -> Sequence[Loan]:
    return await repo.overdue_loans(today or date.today())


async def get_active_loans() -> Sequence[Loan]:
    return await repo.list_active_loans()


# --------------------------------------------------------------------------
# Небольшая статистика для middleware/демо (методичка 18.5 не требуется,
# но использовано в LoggingMiddleware для счётчика сообщений).
# --------------------------------------------------------------------------

async def count_objects() -> dict[str, int]:
    return {
        "books": len(await repo.list_books()),
        "readers": len(await repo.list_readers()),
        "active_loans": len(await repo.list_active_loans()),
        "authors": len(await repo.find_authors("")),
    }