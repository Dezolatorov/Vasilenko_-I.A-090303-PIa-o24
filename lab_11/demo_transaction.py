"""Демонстрация транзакций: успешная выдача книги и откат при ошибке.

Запуск: python demo_transaction.py
"""

from datetime import date

import config
from cache import RedisCache
from db import Database
from exceptions import ApiError
from repository import BookRepository, LoanRepository, ReaderRepository
from service import LoanService


def state(service: LoanService, database: Database, book_id: int) -> tuple[int, int]:
    book = service.books.get_by_id(book_id)
    with database.connection() as connection:
        loans = connection.execute(
            "SELECT COUNT(*) FROM loans WHERE book_id = ? AND returned_at IS NULL",
            (book_id,),
        ).fetchone()[0]
    return (book.available_copies if book else -1), loans


def main() -> None:
    database = Database(config.DB_PATH)
    books = BookRepository(database)
    readers = ReaderRepository(database)
    loans = LoanRepository(database)
    cache = RedisCache()
    service = LoanService(database, books, readers, loans, cache if cache.ping() else None)

    print("=" * 70)
    print("ТРАНЗАКЦИЯ 1. Успешная выдача книги (COMMIT)")
    print("=" * 70)
    available_before, active_before = state(service, database, 2)
    print(f"До операции:  свободных экземпляров = {available_before}, активных выдач = {active_before}")

    loan = service.issue_book({"book_id": 2, "reader_id": 3, "days": 14}, today=date(2026, 10, 19))
    print(f"BEGIN → INSERT INTO loans (id={loan.id}) → UPDATE books.available_copies - 1 → COMMIT")
    print(f"Выдача оформлена: книга {loan.book_id}, читатель {loan.reader_id}, "
          f"срок возврата {loan.due_at}")

    available_after, active_after = state(service, database, 2)
    print(f"После операции: свободных экземпляров = {available_after}, активных выдач = {active_after}")

    print()
    print("=" * 70)
    print("ТРАНЗАКЦИЯ 2. Ошибка внутри транзакции (ROLLBACK)")
    print("=" * 70)
    # Книга 5 полностью выдана: available_copies = 0
    book = books.get_by_id(5)
    print(f"Книга «{book.title}»: свободных экземпляров = {available_before if book is None else book.available_copies}")

    available_before, active_before = state(service, database, 5)
    try:
        service.issue_book({"book_id": 5, "reader_id": 1, "days": 14}, today=date(2026, 10, 19))
    except ApiError as error:
        print(f"Ошибка: {error.status_code} {error.code} — {error.message}")
        print("Транзакция откатана: ROLLBACK")

    available_after, active_after = state(service, database, 5)
    print(f"До операции:  свободных экземпляров = {available_before}, активных выдач = {active_before}")
    print(f"После отката: свободных экземпляров = {available_after}, активных выдач = {active_after}")
    print("Состояние БД не изменилось: запись о выдаче не создана, остаток не уменьшен.")

    print()
    print("=" * 70)
    print("ТРАНЗАКЦИЯ 3. Возврат книги (COMMIT)")
    print("=" * 70)
    available_before, active_before = state(service, database, 2)
    returned = service.return_book(loan.id, today=date(2026, 10, 26))
    print(f"BEGIN → UPDATE loans.returned_at → UPDATE books.available_copies + 1 → COMMIT")
    print(f"Книга возвращена {returned.returned_at}")
    available_after, active_after = state(service, database, 2)
    print(f"До операции:  свободных экземпляров = {available_before}, активных выдач = {active_before}")
    print(f"После операции: свободных экземпляров = {available_after}, активных выдач = {active_after}")
    print("COMMIT выполнен: оба UPDATE применились вместе.")


if __name__ == "__main__":
    main()
