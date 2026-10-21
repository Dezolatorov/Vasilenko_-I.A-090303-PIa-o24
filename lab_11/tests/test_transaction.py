"""Тесты транзакций: выдача и возврат книги, откат при ошибке."""

from datetime import date

import pytest

from exceptions import ConflictError, NotFoundError

TODAY = date(2026, 10, 19)


def loans_count(database, book_id: int) -> int:
    with database.connection() as connection:
        return connection.execute(
            "SELECT COUNT(*) FROM loans WHERE book_id = ? AND returned_at IS NULL",
            (book_id,),
        ).fetchone()[0]


def test_issue_book_decrements_available(services, repositories, database):
    loan = services["loans"].issue_book({"book_id": 2, "reader_id": 3, "days": 14}, today=TODAY)

    assert loan.book_id == 2
    assert loan.due_at == "2026-11-02"
    assert repositories["books"].get_by_id(2).available_copies == 3
    assert loans_count(database, 2) == 1


def test_issue_book_rolls_back_without_copies(services, repositories, database):
    book = repositories["books"].get_by_id(5)
    assert book.available_copies == 0
    before = loans_count(database, 5)

    with pytest.raises(ConflictError):
        services["loans"].issue_book({"book_id": 5, "reader_id": 1, "days": 14}, today=TODAY)

    assert repositories["books"].get_by_id(5).available_copies == 0
    assert loans_count(database, 5) == before


def test_issue_book_unknown_reader(services, database):
    before = loans_count(database, 2)
    with pytest.raises(NotFoundError):
        services["loans"].issue_book({"book_id": 2, "reader_id": 99, "days": 14}, today=TODAY)
    assert loans_count(database, 2) == before


def test_issue_book_unknown_book(services):
    with pytest.raises(NotFoundError):
        services["loans"].issue_book({"book_id": 999, "reader_id": 1, "days": 14}, today=TODAY)


def test_return_book_increments_available(services, repositories, database):
    loan = services["loans"].issue_book({"book_id": 6, "reader_id": 2, "days": 7}, today=TODAY)
    assert repositories["books"].get_by_id(6).available_copies == 1

    returned = services["loans"].return_book(loan.id, today=date(2026, 10, 22))
    assert returned.returned_at == "2026-10-22"
    assert repositories["books"].get_by_id(6).available_copies == 2
    assert loans_count(database, 6) == 0


def test_return_book_twice_raises_conflict(services):
    loan = services["loans"].issue_book({"book_id": 9, "reader_id": 4, "days": 7}, today=TODAY)
    services["loans"].return_book(loan.id, today=TODAY)
    with pytest.raises(ConflictError):
        services["loans"].return_book(loan.id, today=TODAY)


def test_return_unknown_loan(services):
    with pytest.raises(NotFoundError):
        services["loans"].return_book(999)


def test_issue_book_invalidates_cache(services, fake_cache):
    services["books"].get_book(10)
    assert "book:10" in fake_cache.store

    services["loans"].issue_book({"book_id": 10, "reader_id": 2, "days": 14}, today=TODAY)
    assert "book:10" not in fake_cache.store


def test_active_and_overdue_loans(services):
    active = services["loans"].list_active()
    assert len(active) >= 6
    assert all(item["due_at"] for item in active)

    overdue = services["loans"].list_overdue(today=date(2026, 10, 19))
    assert all(item["due_at"] < "2026-10-19" for item in overdue)
