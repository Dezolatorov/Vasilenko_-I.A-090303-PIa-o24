# infrastructure.py
from typing import Optional, List
from models import Book, Reader, Loan, Reservation
from interfaces import LibraryRepository, NotificationSender

class InMemoryLibraryRepository(LibraryRepository):
    def __init__(self):
        self._books = [
            Book(id=1, title="1984", author="George Orwell", is_borrowed=False),
            Book(id=2, title="Brave New World", author="Aldous Huxley", is_borrowed=True),
            Book(id=3, title="Fahrenheit 451", author="Ray Bradbury", is_borrowed=False)
        ]
        self._readers = [
            Reader(id=101, name="Ivanov", email="ivanov@mail.ru", phone="+79991112233"),
            Reader(id=102, name="Petrov", email="petrov@mail.ru", phone="+79994445566")
        ]
        from datetime import datetime, timedelta
        self._loans = [
            Loan(book_id=2, reader_id=102, due_date=datetime.now() - timedelta(days=1))
        ]
        self._reservations: List[Reservation] = []

    def get_book_by_id(self, book_id: int) -> Optional[Book]:
        return next((b for b in self._books if b.id == book_id), None)

    def get_reader_by_id(self, reader_id: int) -> Optional[Reader]:
        return next((r for r in self._readers if r.id == reader_id), None)

    def add_loan(self, loan: Loan) -> None:
        self._loans.append(loan)

    def get_all_loans(self) -> List[Loan]:
        return self._loans

    def remove_loan(self, book_id: int, reader_id: int) -> bool:
        initial_len = len(self._loans)
        self._loans = [loan for loan in self._loans if not (loan.book_id == book_id and loan.reader_id == reader_id)]
        return len(self._loans) < initial_len

    def add_reservation(self, reservation: Reservation) -> None:
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

class EmailSender(NotificationSender):
    def send_notification(self, reader: Reader, message: str) -> None:
        print(f"[EMAIL] Уважаемый {reader.name}! На адрес {reader.email} отправлено: {message}")

class SmsSender(NotificationSender):
    def send_notification(self, reader: Reader, message: str) -> None:
        print(f"[SMS] Читателю {reader.name} на номер {reader.phone} отправлено: {message}")

# Совместимые псевдонимы для прежних названий классов
EmailNotificationSender = EmailSender
SmsNotificationSender = SmsSender
