"""Тесты бизнес-логики."""

import pytest

from exceptions import NotFoundError, ValidationError
from models import Book
from repository import BookRepository
from service import BookService


@pytest.fixture
def service() -> BookService:
    repository = BookRepository([
        Book(id=0, title="Война и мир", author="Толстой Л.Н.", genre="роман", year=1869, price=1200.0, available=2),
        Book(id=0, title="Собачье сердце", author="Булгаков М.А.", genre="повесть", year=1925, price=410.0, available=4),
        Book(id=0, title="Мастер и Маргарита", author="Булгаков М.А.", genre="роман", year=1967, price=750.0, available=0),
    ])
    return BookService(repository)


def test_create_book_validates_and_stores(service: BookService) -> None:
    book = service.create_book({
        "title": "Пикник на обочине",
        "author": "Стругацкие А. и Б.",
        "genre": "фантастика",
        "year": 1972,
        "price": 520,
        "available": 1,
    })

    assert book.id == 4
    assert book.price == 520.0
    assert service.get_book(book.id).title == "Пикник на обочине"


def test_create_book_rejects_invalid_data(service: BookService) -> None:
    with pytest.raises(ValidationError):
        service.create_book({
            "title": "",
            "author": "Автор",
            "genre": "роман",
            "year": 2000,
            "price": -100,
            "available": 1,
        })


def test_get_missing_book_raises_not_found(service: BookService) -> None:
    with pytest.raises(NotFoundError):
        service.get_book(999)


def test_patch_changes_only_given_fields(service: BookService) -> None:
    book = service.patch_book(1, {"price": 1100, "available": 5})

    assert book.price == 1100.0
    assert book.available == 5
    assert book.title == "Война и мир"


def test_list_books_filters_and_sorts(service: BookService) -> None:
    filtered = service.list_books({"genre": "роман", "available": True}, None, "asc")
    assert [book.title for book in filtered] == ["Война и мир"]

    sorted_books = service.list_books({}, "price", "desc")
    assert [book.price for book in sorted_books] == [1200.0, 750.0, 410.0]
