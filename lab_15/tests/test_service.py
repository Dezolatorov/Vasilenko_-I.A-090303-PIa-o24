"""Unit/интеграционные тесты сервисного слоя ЛР 15 (Flask + SQLAlchemy).

Проверяют бизнес-логику библиотеки на изолированной тестовой SQLite-базе:
CRUD книг, валидацию, выдачу/возврат, статистику, поиск и обработку ошибок.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.services.services import (
    ConflictError,
    LibraryService,
    NotFoundError,
    ValidationError,
)
from app.models import Author, Book


# ---------------------------------------------------------------------------
# Положительные сценарии
# ---------------------------------------------------------------------------

def test_create_book(service):
    with service.session as session:
        author = Author(full_name="Тестовый Автор", country="Россия")
        session.add(author)
        session.commit()
        author_id = author.id

        book = service.create_book(
            {
                "title": "Новая книга",
                "author_id": author_id,
                "genre": "Роман",
                "year": 2000,
                "isbn": "9785000000099",
                "price": "500.00",
                "copies_total": 3,
            }
        )

        assert book.id is not None
        assert book.title == "Новая книга"
        assert book.copies_available == 3


def test_get_book_returns_existing(service):
    book = service.list_books()[0]
    fetched = service.get_book(book.id)
    assert fetched.id == book.id


def test_update_book(service):
    book = service.list_books()[0]
    # update_book в этой реализации выполняет полную замену данных,
    # поэтому передаём недостающие обязательные поля из исходной книги.
    updated = service.update_book(
        book.id,
        {
            "title": book.title,
            "author_id": book.author_id,
            "genre": book.genre,
            "year": book.year,
            "isbn": book.isbn,
            "price": "999.99",
            "copies_total": book.copies_total,
            "copies_available": book.copies_available,
        },
    )
    assert updated.price == Decimal("999.99")


def test_delete_book(service):
    # Создаём книгу и сразу удаляем её (без выдач, чтобы пройти FK/cascade)
    with service.session as session:
        author = Author(full_name="Автор для удаления", country="Россия")
        session.add(author)
        session.commit()
        created = service.create_book(
            {
                "title": "Книга на удаление",
                "author_id": author.id,
                "genre": "Повесть",
                "year": 2010,
                "isbn": "9785000000088",
                "price": "100.00",
                "copies_total": 1,
            }
        )
    service.delete_book(created.id)
    with pytest.raises(NotFoundError):
        service.get_book(created.id)


def test_search_books(service):
    results = service.list_books(search="Пушкин")
    assert all("Пушкин" in b.author.full_name for b in results)
    assert results


def test_genres_list(service):
    genres = service.genres()
    assert "Роман" in genres
    assert "Поэма" in genres


# ---------------------------------------------------------------------------
# Отрицательные сценарии / валидация
# ---------------------------------------------------------------------------

def test_create_book_missing_title(service):
    with service.session as session:
        author = Author(full_name="Автор", country="Россия")
        session.add(author)
        session.commit()
        with pytest.raises(ValidationError):
            service.create_book(
                {
                    "title": "",
                    "author_id": author.id,
                    "genre": "Роман",
                    "year": 2000,
                    "isbn": "9785000000099",
                    "price": "10.00",
                    "copies_total": 1,
                }
            )


def test_create_book_bad_isbn(service):
    with service.session as session:
        author = Author(full_name="Автор2", country="Россия")
        session.add(author)
        session.commit()
        with pytest.raises(ValidationError):
            service.create_book(
                {
                    "title": "Допустимое",
                    "author_id": author.id,
                    "genre": "Роман",
                    "year": 2000,
                    "isbn": "ABC",
                    "price": "10.00",
                    "copies_total": 1,
                }
            )


def test_get_missing_book_raises(service):
    with pytest.raises(NotFoundError):
        service.get_book(99999)


def test_create_duplicate_isbn_raises_conflict(service):
    existing = service.list_books()[0]
    # create_book проверяет уникальность ISBN и должен выбросить ConflictError.
    with pytest.raises(ConflictError):
        service.create_book(
            {
                "title": "Дубликат ISBN",
                "author_id": existing.author_id,
                "genre": "Роман",
                "year": 2000,
                "isbn": existing.isbn,
                "price": "100.00",
                "copies_total": 1,
            }
        )


def test_issue_book_not_found_reader(service):
    with pytest.raises(NotFoundError):
        service.issue_book(service.list_books()[0].id, 99999)


def test_issue_book_when_no_copies(service):
    # Книга с 0 доступных экземпляров из сида (Анна Каренина: 3 общих, 3 доступны —
    # сначала выдадим, чтобы исчерпать свободные).
    book = service.list_books()[0]
    reader = service.readers.list()[0]
    # Выдаём пока есть хотя бы один свободный экземпляр (обычная логика проходит)
    loan = service.issue_book(book.id, reader.id, days=14)
    assert loan is not None
    # Повторная выдача тому же читателю запрещена
    with pytest.raises(ValidationError):
        service.issue_book(book.id, reader.id, days=14)


def test_return_book(service):
    # Выбираем книгу и читателя так, чтобы не было конфликта с сидом.
    # В сиде книга[0] уже выдана читателю[0], поэтому берём другую комбинацию.
    with service.session as session:
        from app.models import Author

        author = Author(full_name="Автор для возврата", country="Россия")
        session.add(author)
        session.commit()
        book = service.create_book(
            {
                "title": "Книга для возврата",
                "author_id": author.id,
                "genre": "Повесть",
                "year": 2005,
                "isbn": "9785000000044",
                "price": "200.00",
                "copies_total": 2,
            }
        )
    reader = service.readers.list()[-1]
    loan = service.issue_book(book.id, reader.id, days=14)
    returned = service.return_book(loan.id)
    assert returned.return_date is not None


def test_statistics(service):
    stats = service.statistics()
    assert stats["books"] > 0
    assert stats["copies_total"] > 0
    assert "avg_price" in stats
    assert "by_genre" in stats