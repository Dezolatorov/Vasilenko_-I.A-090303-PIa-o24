"""Unit-тесты бизнес-логики сервисного слоя с изолированной БД и Mock."""
from datetime import date, timedelta
from unittest import mock

import pytest
from sqlalchemy.orm import Session

from src.library.config import settings
from src.library.exceptions import (
    BusinessRuleException,
    ConflictException,
    EntityNotFoundException,
    ValidationException,
)
from src.library.models import Author, Book, Reader
from src.library.services import AuthorService, BookService, LoanService
from tests.conftest import create_reader


# ---------- Сервис книг ----------

def test_book_service_get_missing_raises(db):
    book_service = BookService(db)
    with pytest.raises(EntityNotFoundException):
        book_service.get(9999)


def test_book_service_create_with_missing_author_raises(db):
    from src.library.schemas import BookCreate

    book_service = BookService(db)
    with pytest.raises(EntityNotFoundException):
        book_service.create(BookCreate(title="X", author_id=12345, year=2000))


def test_book_service_create_sets_available_equal_total(db, sample_author):
    from src.library.schemas import BookCreate

    book_service = BookService(db)
    book = book_service.create(
        BookCreate(title="Новая", author_id=sample_author.id,
                   year=2020, total_copies=5)
    )
    assert book.total_copies == 5
    assert book.available_copies == 5


def test_book_service_delete_book_on_loan_raises(db, sample_book, sample_user):
    from src.library.schemas import LoanCreate

    loan_service = LoanService(db)
    loan_service.issue(sample_user, LoanCreate(book_id=sample_book.id))
    db.flush()

    book_service = BookService(db)
    with pytest.raises(ValidationException):
        book_service.delete(sample_book.id)


def test_book_service_delete_available_book_ok(db, sample_book):
    book_service = BookService(db)
    book_service.delete(sample_book.id)
    db.flush()
    with pytest.raises(EntityNotFoundException):
        book_service.get(sample_book.id)


# ---------- Сервис авторов ----------

def test_author_service_delete_with_books_raises(db, sample_author, sample_book):
    author_service = AuthorService(db)
    with pytest.raises(ConflictException):
        author_service.delete(sample_author.id)


# ---------- Сервис выдач: бизнес-правила ----------

def test_issue_book_ok(db, sample_book, sample_user):
    from src.library.schemas import LoanCreate

    loan_service = LoanService(db)
    loan = loan_service.issue(sample_user, LoanCreate(book_id=sample_book.id))
    assert loan.returned is False
    assert loan.issue_date == date.today()
    assert loan.due_date == date.today() + timedelta(days=settings.loan_days)
    db.flush()
    db.refresh(sample_book)
    assert sample_book.available_copies == 2


@pytest.mark.parametrize("available,total", [(0, 1), (0, 0)])
def test_issue_book_unavailable_raises(db, sample_user, available, total):
    from src.library.models import Book
    from src.library.schemas import LoanCreate

    author = Author(name="A", birth_year=1970)
    db.add(author)
    db.flush()
    book = Book(title="Нет в наличии", author_id=author.id, year=1999,
                total_copies=total, available_copies=available)
    db.add(book)
    db.commit()

    loan_service = LoanService(db)
    with pytest.raises(BusinessRuleException):
        loan_service.issue(sample_user, LoanCreate(book_id=book.id))


def test_issue_book_over_max_limit_raises(db, sample_user, sample_author):
    from src.library.models import Book
    from src.library.schemas import LoanCreate

    # Создаём 5 книг и выдаём все до лимита
    loan_service = LoanService(db)
    books = []
    for i in range(settings.max_active_loans):
        b = Book(title=f"Книга{i}", author_id=sample_author.id, year=2000,
                 total_copies=1, available_copies=1)
        db.add(b)
        db.flush()
        books.append(b)
    db.commit()
    for b in books:
        loan_service.issue(sample_user, LoanCreate(book_id=b.id))
    db.commit()

    # Шестая книга уже недоступна из-за лимита
    extra = Book(title="Шестая", author_id=sample_author.id, year=2000,
                 total_copies=1, available_copies=1)
    db.add(extra)
    db.commit()
    with pytest.raises(BusinessRuleException):
        loan_service.issue(sample_user, LoanCreate(book_id=extra.id))


def test_issue_book_with_overdue_raises(db, sample_user, sample_book):
    from src.library.models import Loan
    from src.library.schemas import LoanCreate

    overdue = Loan(
        book_id=sample_book.id, reader_id=sample_user.id,
        issue_date=date.today() - timedelta(days=60),
        due_date=date.today() - timedelta(days=30),
        returned=False,
    )
    db.add(overdue)
    db.commit()

    # Отдельная свободная книга
    author = Author(name="B", birth_year=1980)
    db.add(author)
    db.flush()
    free = Book(title="Свободная", author_id=author.id, year=2010,
                total_copies=1, available_copies=1)
    db.add(free)
    db.commit()

    loan_service = LoanService(db)
    with pytest.raises(BusinessRuleException):
        loan_service.issue(sample_user, LoanCreate(book_id=free.id))


def test_return_loan_ok_increments_copies(db, sample_book, sample_user):
    from src.library.schemas import LoanCreate, LoanReturn

    loan_service = LoanService(db)
    loan = loan_service.issue(sample_user, LoanCreate(book_id=sample_book.id))
    db.flush()
    returned = loan_service.return_loan(loan.id, LoanReturn())
    assert returned.returned is True
    db.refresh(sample_book)
    assert sample_book.available_copies == 3


def test_return_loan_twice_raises(db, sample_book, sample_user):
    from src.library.schemas import LoanCreate, LoanReturn

    loan_service = LoanService(db)
    loan = loan_service.issue(sample_user, LoanCreate(book_id=sample_book.id))
    db.flush()
    loan_service.return_loan(loan.id, LoanReturn())
    with pytest.raises(BusinessRuleException):
        loan_service.return_loan(loan.id, LoanReturn())


def test_return_loan_date_before_issue_raises(db, sample_book, sample_user):
    from src.library.schemas import LoanCreate, LoanReturn

    loan_service = LoanService(db)
    loan = loan_service.issue(sample_user, LoanCreate(book_id=sample_book.id))
    db.flush()
    bad_return = LoanReturn(return_date=date.today() - timedelta(days=1))
    with pytest.raises(ValidationException):
        loan_service.return_loan(loan.id, bad_return)


def test_issue_book_for_inactive_reader_raises(db, sample_book, sample_user):
    from src.library.schemas import LoanCreate

    sample_user.is_active = False
    db.flush()
    loan_service = LoanService(db)
    with pytest.raises(BusinessRuleException):
        loan_service.issue(sample_user, LoanCreate(book_id=sample_book.id))


def test_issue_book_missing_raises(db, sample_user):
    from src.library.schemas import LoanCreate

    loan_service = LoanService(db)
    with pytest.raises(EntityNotFoundException):
        loan_service.issue(sample_user, LoanCreate(book_id=98765))


def test_book_update_reduce_copies_keeps_loan_consistent(db, sample_author, sample_user):
    from src.library.schemas import BookCreate, BookUpdate, LoanCreate

    book_service = BookService(db)
    book = book_service.create(
        BookCreate(title="Книга", author_id=sample_author.id, year=2000, total_copies=3)
    )
    LoanService(db).issue(sample_user, LoanCreate(book_id=book.id))
    db.flush()

    # total=2 при одной выданной копии: доступно должно стать 1
    updated = book_service.update(book.id, BookUpdate(total_copies=2))
    db.flush()
    assert updated.total_copies == 2
    assert updated.available_copies == 1

    # total=1 при одной выданной: доступно 0 - допустимо, экземпляр на руках
    updated2 = book_service.update(book.id, BookUpdate(total_copies=1))
    db.flush()
    assert updated2.total_copies == 1
    assert updated2.available_copies == 0