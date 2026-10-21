"""Интеграционные тесты репозиториев ЛР 12 (SQLAlchemy ORM).

Проверяют CRUD, поиск, фильтрацию, сортировку, статистику и связи
между сущностями на реальной (тестовой) SQLite-базе.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from app.models import Book, Loan, Reader
from app.repositories.repositories import BookRepository, LoanRepository, ReaderRepository


def test_add_and_get_book(database):
    session = database.session()
    reader_repo = ReaderRepository(session)
    reader = reader_repo.add(Reader(full_name="Иван Иванов", email="ivan@example.com"))
    session.commit()
    with database.session() as s:
        fetched = s.get(Reader, reader.id)
        assert fetched.full_name == "Иван Иванов"


def test_add_book_with_relations(database, book_data):
    with database.session() as session:
        repo = BookRepository(session)
        book = repo.add(Book(**book_data))
        session.commit()
        fetched = repo.get(book.id)
        assert fetched.title == "Тестовая книга"
        assert fetched.price == Decimal("450.50")


def test_list_books_filter_and_sort(database, seeded_database):
    with seeded_database.session() as session:
        repo = BookRepository(session)
        books = repo.list()
        assert len(books) > 0
        # Сортировка по убыванию цены
        by_price = repo.list(sort="price", descending=True)
        prices = [b.price for b in by_price]
        assert prices == sorted(prices, reverse=True)
        # Фильтр только доступных
        available = repo.list(available_only=True)
        assert all(b.copies_available > 0 for b in available)


def test_search_book(database, seeded_database):
    with seeded_database.session() as session:
        repo = BookRepository(session)
        found = repo.search("Пушкин")
        assert any("Пушкин" in b.author for b in found)
        by_author = repo.by_author("Толстой")
        assert all("Толстой" in b.author for b in by_author)


def test_delete_book(database, book_data):
    with database.session() as session:
        repo = BookRepository(session)
        book = repo.add(Book(**book_data))
        session.commit()
        repo.delete(book)
        session.commit()
        assert repo.get(book.id) is None


def test_statistics(database, seeded_database):
    with seeded_database.session() as session:
        stats = BookRepository(session).statistics()
        assert stats["books"] > 0
        assert stats["copies_total"] > 0
        assert stats["avg_price"] > 0
        assert stats["min_price"] <= stats["max_price"]


def test_reader_unique_email(database):
    with database.session() as session:
        repo = ReaderRepository(session)
        repo.add(Reader(full_name="Первый", email="dup@example.com"))
        session.commit()
        with pytest.raises(Exception):
            repo.add(Reader(full_name="Второй", email="dup@example.com"))
            session.commit()


def test_loan_relations(database, seeded_database):
    with seeded_database.session() as session:
        loans = LoanRepository(session).active()
        assert len(loans) > 0
        # Связанные объекты книги и читателя доступны
        assert all(l.book is not None and l.reader is not None for l in loans)


def test_loan_by_reader(database, seeded_database):
    with seeded_database.session() as session:
        reader = ReaderRepository(session).list()[0]
        loans = LoanRepository(session).by_reader(reader.id)
        assert all(l.reader_id == reader.id for l in loans)


def test_loan_overdue(database, seeded_database):
    with seeded_database.session() as session:
        overdue = LoanRepository(session).overdue()
        assert overdue  # в сиде есть просроченная выдача
        assert all(l.return_date is None for l in overdue)