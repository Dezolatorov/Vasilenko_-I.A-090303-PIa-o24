import pytest
from fastapi import HTTPException

from src.repositories import BookRepository
from src.services import LibraryService


@pytest.fixture
def service(db_session):
    return LibraryService(BookRepository(db_session))


def test_get_book_not_found(service):
    with pytest.raises(HTTPException) as exc:
        service.get_book(9999)
    assert exc.value.status_code == 404


def test_create_book_and_stats(service):
    book = service.create_book(
        {
            "title": "Анна Каренина",
            "author_name": "Лев Толстой",
            "year": 1877,
            "isbn": "9785171051359",
            "copies_total": 3,
        }
    )
    assert book.id is not None
    stats = service.get_stats()
    assert stats["total_books"] == 1
    assert stats["authors"] == 1


def test_borrow_decrements_copies(service, seeded):
    book = seeded["book"]
    loan = service.borrow_book(book.id, "Иван Петров", days=14)
    assert loan.reader_name == "Иван Петров"
    refreshed = service.get_book(book.id)
    assert refreshed.copies_available == book.copies_total - 1
    assert service.get_stats()["active_loans"] == 1


def test_borrow_fails_when_no_copies(service):
    book = service.create_book(
        {
            "title": "Единственный экземпляр",
            "author_name": "Автор",
            "year": 2000,
            "isbn": "9780000000001",
            "copies_total": 1,
        }
    )
    service.borrow_book(book.id, "Первый", days=7)
    with pytest.raises(HTTPException) as exc:
        service.borrow_book(book.id, "Второй", days=7)
    assert exc.value.status_code == 409
