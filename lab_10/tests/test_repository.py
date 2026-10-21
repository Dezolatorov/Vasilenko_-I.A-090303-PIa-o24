"""Тесты слоя хранения."""

from models import Book
from repository import BookRepository


def make_book(title: str = "Книга") -> Book:
    return Book(id=0, title=title, author="Автор", genre="роман", year=2020, price=500.0, available=1)


def test_create_assigns_incremental_ids() -> None:
    repository = BookRepository()
    first = repository.create(make_book("Первая"))
    second = repository.create(make_book("Вторая"))

    assert first.id == 1
    assert second.id == 2
    assert repository.count() == 2
    assert repository.get_by_id(2).title == "Вторая"


def test_delete_removes_book_and_reports_missing() -> None:
    repository = BookRepository([make_book("Книга")])

    assert repository.delete(1) is True
    assert repository.get_by_id(1) is None
    assert repository.delete(1) is False
    assert repository.get_all() == []
