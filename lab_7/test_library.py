# test_library.py
import pytest
from datetime import datetime, timedelta
from models import Book, Reader, Loan, Reservation
from services import LibraryService

class FakeRepository:
    def __init__(self):
        self.book = Book(id=1, title="Test Book", author="Author", is_borrowed=False)
        self.reader = Reader(id=101, name="Test Reader", email="test@test.com", phone="123")
        self._loans = []
        self._reservations = []

    def get_book_by_id(self, book_id: int):
        return self.book if book_id == 1 else None

    def get_reader_by_id(self, reader_id: int):
        return self.reader if reader_id == 101 else None

    def add_loan(self, loan: Loan):
        self._loans.append(loan)

    def get_all_loans(self):
        return self._loans

    def remove_loan(self, book_id: int, reader_id: int) -> bool:
        return True

    def add_reservation(self, reservation: Reservation):
        self._reservations.append(reservation)

    def remove_reservation(self, book_id: int, reader_id: int) -> bool:
        initial_len = len(self._reservations)
        self._reservations = [
            res for res in self._reservations
            if not (res.book_id == book_id and res.reader_id == reader_id)
        ]
        return len(self._reservations) < initial_len

    def is_reserved_by(self, book_id: int, reader_id: int) -> bool:
        return any(res.book_id == book_id and res.reader_id == reader_id for res in self._reservations)

class FakeNotifier:
    def __init__(self):
        self.notifications = []

    def send_notification(self, reader: Reader, message: str):
        self.notifications.append((reader.id, message))

def test_successful_borrow_book():
    repo = FakeRepository()
    notifier = FakeNotifier()
    service = LibraryService(repo, notifier)
    result = service.borrow_book(book_id=1, reader_id=101)
    assert result is True
    assert repo.book.is_borrowed is True

def test_borrow_already_borrowed_book():
    repo = FakeRepository()
    repo.book.is_borrowed = True
    notifier = FakeNotifier()
    service = LibraryService(repo, notifier)
    result = service.borrow_book(book_id=1, reader_id=101)
    assert result is False

def test_check_overdue_loans():
    repo = FakeRepository()
    repo.add_loan(Loan(book_id=1, reader_id=101, due_date=datetime.now() - timedelta(days=2)))
    notifier = FakeNotifier()
    service = LibraryService(repo, notifier)
    overdues = service.check_overdue_loans()
    assert len(overdues) == 1


def test_reserve_book_creates_reservation_and_blocks_foreign_borrow():
    repo = FakeRepository()
    notifier = FakeNotifier()
    service = LibraryService(repo, notifier)

    assert service.reserve_book(book_id=1, reader_id=101) is True
    assert repo.book.is_reserved is True
    assert repo.is_reserved_by(1, 101) is True
    assert notifier.notifications

    repo.reader = Reader(id=102, name="Other", email="other@test.com", phone="456")
    assert service.borrow_book(book_id=1, reader_id=102) is False


def test_reserve_already_reserved_book():
    repo = FakeRepository()
    notifier = FakeNotifier()
    service = LibraryService(repo, notifier)

    assert service.reserve_book(book_id=1, reader_id=101) is True
    assert service.reserve_book(book_id=1, reader_id=101) is False


def test_cancel_reservation_returns_book_to_available():
    repo = FakeRepository()
    notifier = FakeNotifier()
    service = LibraryService(repo, notifier)

    service.reserve_book(book_id=1, reader_id=101)
    assert service.cancel_reservation(book_id=1, reader_id=101) is True
    assert repo.book.is_reserved is False
    assert repo.is_reserved_by(1, 101) is False
