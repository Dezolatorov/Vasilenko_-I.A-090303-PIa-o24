"""Тесты сервисного слоя ЛР 12 (SQLAlchemy ORM).

Проверяют бизнес-логику: валидацию, CRUD, транзакционную выдачу/возврат
и обработку ошибок на изолированной тестовой базе.
"""
from __future__ import annotations

import pytest

from app.database import Database
from app.errors import (
    DuplicateError,
    NotFoundError,
    TransactionError,
    ValidationError,
)
from app.services.services import LibraryService


# ---------------------------------------------------------------------------
# CRUD книг
# ---------------------------------------------------------------------------

def test_add_book(database, book_data):
    service = LibraryService(database)
    book = service.add_book(**book_data)
    assert book.id is not None
    assert book.title == "Тестовая книга"
    assert book.copies_available == book.copies_total


def test_add_book_validation_empty_title(database, book_data):
    service = LibraryService(database)
    with pytest.raises(ValidationError):
        service.add_book(title="", author="Автор", genre="Роман",
                         year=2000, price="100.00", copies_total=1)


def test_add_book_validation_bad_year(database, book_data):
    service = LibraryService(database)
    with pytest.raises(ValidationError):
        service.add_book(title="Книга", author="Автор", genre="Роман",
                         year=100, price="100.00", copies_total=1)


def test_add_book_negative_price(database, book_data):
    service = LibraryService(database)
    with pytest.raises(ValidationError):
        service.add_book(title="Книга", author="Автор", genre="Роман",
                         year=2000, price="-1.00", copies_total=1)


def test_get_book(database, book_data):
    service = LibraryService(database)
    book = service.add_book(**book_data)
    fetched = service.get_book(book.id)
    assert fetched.id == book.id


def test_get_book_not_found(database):
    service = LibraryService(database)
    with pytest.raises(NotFoundError):
        service.get_book(99999)


def test_list_and_search(database, book_data):
    service = LibraryService(database)
    service.add_book(**book_data)
    books = service.list_books()
    assert any(b.title == "Тестовая книга" for b in books)
    found = service.search_books("Тестовый Автор")
    assert any("Тестовый Автор" in b.author for b in found)


def test_search_empty_query_raises(database):
    service = LibraryService(database)
    with pytest.raises(ValidationError):
        service.search_books("   ")


def test_update_book(database, book_data):
    service = LibraryService(database)
    # Для чистоты проверки создаём отдельную книгу, чтобы не конфликтовать
    # с book_data при повторном использовании фикстуры.
    b2 = service.add_book(title="Вторая книга", author="Автор2", genre="Повесть",
                          year=2005, price="300.00", copies_total=2)
    updated = service.update_book(b2.id, price="999.99")
    # Цена хранится в колонке Numeric; из свежевыбранного объекта она отдаётся
    # типизированно (Decimal/float), даже если в кэшированном объекте была строкой.
    fresh = service.get_book(b2.id)
    assert updated.id == b2.id
    assert float(fresh.price) == 999.99


def test_delete_book(database, book_data):
    service = LibraryService(database)
    book = service.add_book(**book_data)
    service.delete_book(book.id)
    with pytest.raises(NotFoundError):
        service.get_book(book.id)


# ---------------------------------------------------------------------------
# Читатели
# ---------------------------------------------------------------------------

def test_add_reader(database):
    service = LibraryService(database)
    reader = service.add_reader("Иван Иванов", "ivan@example.com")
    assert reader.id is not None


def test_add_reader_duplicate_email(database):
    service = LibraryService(database)
    service.add_reader("Иван Иванов", "dup@example.com")
    with pytest.raises(DuplicateError):
        service.add_reader("Пётр Петров", "dup@example.com")


def test_add_reader_invalid_email(database):
    service = LibraryService(database)
    with pytest.raises(ValidationError):
        service.add_reader("Иван Иванов", "не-email")


# ---------------------------------------------------------------------------
# Транзакционная выдача / возврат
# ---------------------------------------------------------------------------

def test_issue_and_return_book(seeded_database):
    service = LibraryService(seeded_database)
    book = service.list_books()[0]
    reader = service.list_readers()[0]
    before = service.get_book(book.id).copies_available

    loan = service.issue_book(book.id, reader.id, days=14)
    assert service.get_book(book.id).copies_available == before - 1

    returned = service.return_loan(loan.id)
    assert returned.return_date is not None
    assert service.get_book(book.id).copies_available == before


def test_issue_book_not_found(seeded_database):
    service = LibraryService(seeded_database)
    reader = service.list_readers()[0]
    with pytest.raises(NotFoundError):
        service.issue_book(99999, reader.id, days=14)


def test_issue_book_no_copies(seeded_database):
    # Книга «Идиот» в сиде имеет 0 доступных экземпляров
    service = LibraryService(seeded_database)
    book = next(b for b in service.list_books() if b.copies_available == 0)
    reader = service.list_readers()[0]
    with pytest.raises(ValidationError):
        service.issue_book(book.id, reader.id, days=14)


def test_issue_book_invalid_days(seeded_database):
    service = LibraryService(seeded_database)
    book = service.list_books()[0]
    reader = service.list_readers()[0]
    with pytest.raises(ValidationError):
        service.issue_book(book.id, reader.id, days=0)


def test_return_book_twice_raises(seeded_database):
    service = LibraryService(seeded_database)
    book = service.list_books()[0]
    reader = service.list_readers()[0]
    loan = service.issue_book(book.id, reader.id, days=14)
    service.return_loan(loan.id)
    with pytest.raises(ValidationError):
        service.return_loan(loan.id)


def test_overdue_loans(seeded_database):
    service = LibraryService(seeded_database)
    overdue = service.overdue_loans()
    assert overdue  # в сиде есть просроченная выдача


def test_statistics(seeded_database):
    service = LibraryService(seeded_database)
    stats = service.statistics()
    assert stats["books"] > 0
    assert stats["readers"] > 0
    assert "avg_price" in stats