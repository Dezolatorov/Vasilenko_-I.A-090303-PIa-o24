# services.py
from datetime import datetime, timedelta
from typing import List, Tuple
from models import Loan, Book, Reader, Reservation
from interfaces import LibraryRepository, NotificationSender

class LibraryService:
    def __init__(self, repository: LibraryRepository, notifier: NotificationSender):
        self.repository = repository  
        self.notifier = notifier      

    def borrow_book(self, book_id: int, reader_id: int) -> bool:
        book = self.repository.get_book_by_id(book_id)
        reader = self.repository.get_reader_by_id(reader_id)

        if not book or book.is_borrowed or not reader:
            return False

        if book.is_reserved and not self.repository.is_reserved_by(book_id, reader_id):
            return False

        book.is_borrowed = True
        book.is_reserved = False
        if self.repository.is_reserved_by(book_id, reader_id):
            self.repository.remove_reservation(book_id, reader_id)
        due_date = datetime.now() + timedelta(days=14)
        new_loan = Loan(book_id=book_id, reader_id=reader_id, due_date=due_date)
        
        self.repository.add_loan(new_loan)
        self.notifier.send_notification(reader, f"Вы успешно арендовали книгу '{book.title}'.")
        return True

    def return_book(self, book_id: int, reader_id: int) -> bool:
        """Операция: ВОЗВРАТ КНИГИ"""
        book = self.repository.get_book_by_id(book_id)
        reader = self.repository.get_reader_by_id(reader_id)
        
        if not book or not reader or not book.is_borrowed:
            return False
            
        removed = self.repository.remove_loan(book_id, reader_id)
        if removed:
            book.is_borrowed = False
            self.notifier.send_notification(reader, f"Книга '{book.title}' успешно возвращена в библиотеку.")
            return True
        return False

    def reserve_book(self, book_id: int, reader_id: int) -> bool:
        """Операция: БРОНИРОВАНИЕ КНИГИ"""
        book = self.repository.get_book_by_id(book_id)
        reader = self.repository.get_reader_by_id(reader_id)
        
        if not book or not reader or book.is_reserved:
            return False

        book.is_reserved = True
        self.repository.add_reservation(
            Reservation(book_id=book_id, reader_id=reader_id, created_at=datetime.now())
        )
        self.notifier.send_notification(reader, f"Книга '{book.title}' забронирована за вами.")
        return True

    def cancel_reservation(self, book_id: int, reader_id: int) -> bool:
        """Операция: ОТМЕНА БРОНИРОВАНИЯ"""
        book = self.repository.get_book_by_id(book_id)
        reader = self.repository.get_reader_by_id(reader_id)

        if not book or not reader or not book.is_reserved:
            return False

        if not self.repository.remove_reservation(book_id, reader_id):
            return False

        book.is_reserved = False
        self.notifier.send_notification(reader, f"Бронирование книги '{book.title}' отменено.")
        return True

    def check_overdue_loans(self) -> List[Tuple[Reader, Book]]:
        overdue_list = []
        all_loans = self.repository.get_all_loans()
        now = datetime.now()

        for loan in all_loans:
            if loan.due_date < now:
                reader = self.repository.get_reader_by_id(loan.reader_id)
                book = self.repository.get_book_by_id(loan.book_id)
                if reader and book:
                    overdue_list.append((reader, book))
                    self.notifier.send_notification(
                        reader, 
                        f"ВНИМАНИЕ! Срок возврата книги '{book.title}' просрочен!"
                    )
        return overdue_list
