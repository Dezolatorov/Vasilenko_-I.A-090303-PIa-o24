"""Тесты с Mock: изоляция сервисного слоя от внешних зависимостей."""
from datetime import date, timedelta
from unittest import mock

import pytest

from src.library.exceptions import EntityNotFoundException
from src.library.services.loans import LoanService


def test_loan_service_issue_uses_repository_mocks(db, sample_user):
    """Мочим репозитории: сервис должен обращаться к ним через интерфейс,
    а не выполнять SQL напрямую."""
    from src.library.schemas import LoanCreate

    book = mock.Mock()
    book.id = 42
    book.title = "Книга"
    book.available_copies = 1

    svc = LoanService(db)
    sample_user.is_active = True

    with mock.patch.object(svc.loans, "has_overdue", return_value=False), \
         mock.patch.object(svc.loans, "count_active_for_reader", return_value=0), \
         mock.patch.object(svc.loans, "add", side_effect=lambda x: x), \
         mock.patch.object(svc.books, "get", return_value=book) as m_get:
        loan = svc.issue(sample_user, LoanCreate(book_id=42, issue_date=date.today()))
        m_get.assert_called_once_with(42)
        assert loan.book_id == 42
        assert loan.reader_id == sample_user.id


def test_loan_service_return_delegates_to_repository(db):
    from src.library.schemas import LoanReturn

    svc = LoanService(db)
    loan = mock.Mock()
    loan.returned = False
    loan.issue_date = date.today() - timedelta(days=5)
    book = mock.Mock()
    book.available_copies = 1

    with mock.patch.object(svc.loans, "get", return_value=loan), \
         mock.patch.object(svc.books, "get", return_value=book):
        result = svc.return_loan(1, LoanReturn(return_date=date.today()))
        assert result.returned is True
        assert result.return_date == date.today()
        # свободные экземпляры книги увеличены
        assert book.available_copies == 2


def test_loan_service_get_not_found_raises(db):
    svc = LoanService(db)
    with mock.patch.object(svc.loans, "get", side_effect=EntityNotFoundException("x")):
        with pytest.raises(EntityNotFoundException):
            svc.get(999)