"""Доменные модели предметной области «Библиотека» (вариант 2).

Сущности (связанные, минимум 3): книга (Book), автор (Author),
читатель (Reader), выдача (Loan). Книга связано с автором (N:1), выдача
связывает книгу и читателя (N:M через Loan).
"""
from dataclasses import dataclass, field
from datetime import date


@dataclass
class Author:
    id: int | None
    full_name: str


@dataclass
class Reader:
    id: int | None
    telegram_id: int
    full_name: str


@dataclass
class Book:
    id: int | None
    title: str
    author_id: int
    author_name: str = ""
    year: int | None = None
    isbn: str | None = None
    copies_total: int = 1
    copies_available: int = 1


@dataclass
class Loan:
    id: int | None
    book_id: int
    reader_id: int
    issued_at: date
    due_date: date
    returned_at: date | None = None
    book_title: str = ""  # для удобства вывода (join в репозитории)
    reader_name: str = ""


@dataclass
class NewLoan:
    """Несохранённая выдача, полученная из FSM-сценария."""
    book_id: int
    reader_id: int
    issued_at: date
    due_date: date


@dataclass
class BookDraft:
    """Черновик новой книги, заполняемый в FSM-диалоге."""
    title: str = ""
    author_name: str = ""
    year: int | None = None
    isbn: str | None = None
    copies_total: int = 1
    copies_available: int = 1