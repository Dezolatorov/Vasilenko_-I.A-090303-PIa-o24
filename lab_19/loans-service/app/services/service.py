"""Сервисный слой loans-service: распределённый бизнес-процесс выдачи книги.

Это оркестратор, который связывает три сервиса предметной области:
  loans-service  -> readers-service (проверка читателя)
                  -> books-service  (проверка доступности и резервирование)

Синхронное взаимодействие выполняется через ResilientClient, реализующий
паттерны Retry и Circuit Breaker (см. shared/resilient_client.py).
После успешной выдачи публикуется асинхронное событие LoanCreated через
файловую шину FileEventBus (Transactional Outbox) - получатель опрашивает
каталог событий.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from app.models import Loan, LoanStatus
from app.schemas.schemas import LoanCreate
from shared.resilient_client import ResilientClient

if TYPE_CHECKING:
    from app.repositories import LoanRepository
    from shared.event_bus import FileEventBus

logger = logging.getLogger("loans-service")


class ServiceUnavailableError(RuntimeError):
    """Зависимый сервис недоступен (после исчерпания Retry / Circuit Breaker OPEN)."""


class LoansService:
    def __init__(
        self,
        repository: "LoanRepository",
        readers_client: ResilientClient,
        books_client: ResilientClient,
        event_bus: "FileEventBus",
    ):
        self._repository = repository
        self._readers = readers_client
        self._books = books_client
        self._event_bus = event_bus

    def list_loans(self) -> list[Loan]:
        return self._repository.all()

    def get_loan(self, loan_id: str) -> Loan | None:
        return self._repository.get(loan_id)

    def _check_reader(self, reader_id: str) -> dict:
        try:
            resp = self._readers.get(f"/readers/check/{reader_id}")
        except Exception as exc:  # include CircuitBreakerError
            raise ServiceUnavailableError(f"сервис читателей недоступен: {exc}")
        resp.raise_for_status()
        data = resp.json()
        if not data.get("exists"):
            raise ValueError("читатель не найден")
        if not data.get("active"):
            raise ValueError("читатель заблокирован, выдача невозможна")
        return data

    def _check_book(self, book_id: str) -> dict:
        try:
            resp = self._books.get(f"/books/check/{book_id}")
        except Exception as exc:
            raise ServiceUnavailableError(f"сервис книг недоступен: {exc}")
        resp.raise_for_status()
        data = resp.json()
        if not data.get("exists"):
            raise ValueError("книга не найдена")
        if not data.get("available"):
            raise ValueError("все экземпляры книги выданы, доступных нет")
        return data

    def _reserve_book(self, book_id: str) -> None:
        try:
            resp = self._books.post(f"/books/{book_id}/decrement")
        except Exception as exc:
            raise ServiceUnavailableError(f"не удалось зарезервировать книгу: {exc}")
        if resp.status_code == 409:
            raise ValueError("книга стала недоступна на момент резервирования")
        resp.raise_for_status()

    def _release_book(self, book_id: str) -> None:
        """Компенсирующее действие (мини-Saga): вернуть экземпляр при сбое публикации."""
        try:
            resp = self._books.post(f"/books/{book_id}/increment")
            resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            logger.error("не удалось выполнить компенсацию для книги %s: %s", book_id, exc)

    def issue_loan(self, payload: LoanCreate) -> Loan:
        """Сценарий выдачи: проверка читателя -> доступность -> резервирование -> событие.

        Это распределённая транзакция; при сбое после резервирования выполняется
        компенсирующее действие (парадигма Saga).
        """
        # 1. синхронная проверка читателя
        try:
            self._check_reader(payload.reader_id)
        except ValueError as exc:
            raise
        except ServiceUnavailableError as exc:
            raise
        # 2. синхронная проверка доступности книги
        try:
            self._check_book(payload.book_id)
        except ValueError as exc:
            raise
        except ServiceUnavailableError as exc:
            raise
        # 3. резервирование экземпляра в books-service
        try:
            self._reserve_book(payload.book_id)
        except (ValueError, ServiceUnavailableError):
            raise

        issued_at = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
        loan = Loan(
            reader_id=payload.reader_id,
            book_id=payload.book_id,
            status=LoanStatus.ISSUED,
            issued_at=issued_at,
        )
        saved = self._repository.create(loan)

        # 4. асинхронное событие выдачи (Transactional Outbox через файловую шину)
        try:
            self._event_bus.publish("LoanCreated", saved.to_dict())
        except Exception as exc:  # noqa: BLE001
            logger.error("ошибка публикации события LoanCreated: %s", exc)
            # компенсация (Saga): возврат экземпляра, т.к. событие не гарантировано
            self._release_book(payload.book_id)
            raise ServiceUnavailableError(f"не удалось доставить событие выдачи: {exc}")

        return saved

    def return_loan(self, loan_id: str) -> Loan | None:
        loan = self._repository.get(loan_id)
        if loan is None:
            return None
        if loan.status == LoanStatus.RETURNED:
            raise ValueError("книга уже возвращена")
        updated = self._repository.update(loan_id, {"status": LoanStatus.RETURNED})
        updated = Loan.from_dict(updated) if updated else None
        if updated is None:
            return None
        # возврат экземпляра в фонд books-service
        try:
            self._books.post(f"/books/{loan.book_id}/increment").raise_for_status()
        except Exception as exc:  # noqa: BLE001
            logger.error("возврат: не удалось увеличить фонд книги %s: %s", loan.book_id, exc)
        try:
            self._event_bus.publish("LoanReturned", updated.to_dict())
        except Exception as exc:  # noqa: BLE001
            logger.error("ошибка публикации события LoanReturned: %s", exc)
        return updated