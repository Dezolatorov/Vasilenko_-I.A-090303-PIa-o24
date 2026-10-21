"""Сервис выдач и возвратов книг.

Здесь сосредоточены БИЗНЕС-ПРАВИЛА системы:
  1. Нельзя выдать книгу, если нет свободных экземпляров (available_copies <= 0).
  2. Нельзя выдать книгу читателю с просроченными выдачами.
  3. Нельзя превысить максимальное число одновременных выдач (MAX_ACTIVE_LOANS).
  4. Возвратить можно только активную (не возвращённую) выдачу.
  5. Дата возврата не может быть раньше даты выдачи.
  6. Нельзя выдать книгу, которой не существует / неактивному читателю
     (проверка нескольких сущностей).
"""
from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from ..config import settings
from ..exceptions import BusinessRuleException, EntityNotFoundException, ValidationException
from ..models import Book, Loan, Reader
from ..repositories import BookRepository, LoanRepository, ReaderRepository
from ..schemas import LoanCreate, LoanReturn


class LoanService:
    def __init__(self, db: Session):
        self.db = db
        self.loans = LoanRepository(db)
        self.books = BookRepository(db)
        self.readers = ReaderRepository(db)

    def issue(self, reader: Reader, data: LoanCreate) -> Loan:
        book = self.books.get(data.book_id)
        if not reader.is_active:
            raise BusinessRuleException("Читатель деактивирован, выдача невозможна")

        # Правило 1: нет свободных экземпляров
        if book.available_copies <= 0:
            raise BusinessRuleException(
                f"Книга {book.title!r} временно недоступна: нет свободных экземпляров"
            )

        today = data.issue_date or date.today()
        # Правило 2: просроченные выдачи
        if self.loans.has_overdue(reader.id, today):
            raise BusinessRuleException(
                "У читателя есть просроченные выдачи; сначала верните их"
            )

        # Правило 3: лимит одновременных выдач
        active = self.loans.count_active_for_reader(reader.id)
        if active >= settings.max_active_loans:
            raise BusinessRuleException(
                f"Читатель достиг лимита одновременных выдач ({settings.max_active_loans})"
            )

        loan_days = data.loan_days or settings.loan_days
        due = today + timedelta(days=loan_days)

        loan = Loan(
            book_id=book.id,
            reader_id=reader.id,
            issue_date=today,
            due_date=due,
            returned=False,
        )
        book.available_copies -= 1
        self.loans.add(loan)
        return loan

    def return_loan(self, loan_id: int, data: LoanReturn) -> Loan:
        loan = self.loans.get(loan_id)
        # Правило 4: возврат только активной выдачи
        if loan.returned:
            raise BusinessRuleException("Выдача уже возвращена")

        return_at = data.return_date or date.today()
        # Правило 5: дата возврата не раньше даты выдачи
        if return_at < loan.issue_date:
            raise ValidationException(
                "Дата возврата не может быть раньше даты выдачи"
            )

        loan.return_date = return_at
        loan.returned = True
        book = self.books.get(loan.book_id)
        book.available_copies += 1
        self.db.flush()
        return loan

    def get(self, loan_id: int) -> Loan:
        return self.loans.get(loan_id)

    def filter(
        self, reader_id: int | None = None, book_id: int | None = None,
        returned: bool | None = None
    ) -> list[Loan]:
        return self.loans.filter(reader_id=reader_id, book_id=book_id, returned=returned)