"""HTTP-слой (эндпоинты) loans-service: REST API выдач и возвратов."""

from __future__ import annotations

import logging
import os

from fastapi import APIRouter, HTTPException, status

from app.repositories import LoanRepository
from app.schemas.schemas import LoanCreate, LoanOut
from app.services import LoansService, ServiceUnavailableError
from shared.event_bus import make_event_bus
from shared.resilient_client import CircuitBreaker, ResilientClient
from shared.storage import make_storage

logger = logging.getLogger("loans-service")

router = APIRouter()

_service = None


def init_service(
    storage_source: str,
    readers_url: str,
    books_url: str,
    events_dir: str,
    breaker_failures: int,
    breaker_timeout: float,
    broker_url: str | None = None,
) -> LoansService:
    global _service
    repo = LoanRepository(make_storage(storage_source))
    event_bus = make_event_bus(events_dir, broker_url)
    readers_client = ResilientClient(readers_url, breaker=CircuitBreaker(failure_threshold=breaker_failures, recovery_timeout=breaker_timeout, name="readers"))
    books_client = ResilientClient(books_url, breaker=CircuitBreaker(failure_threshold=breaker_failures, recovery_timeout=breaker_timeout, name="books"))
    _service = LoansService(repo, readers_client, books_client, event_bus)
    return _service


def get_service() -> LoansService:
    if _service is None:
        init_service(
            os.environ.get("DATABASE_URL", os.environ.get("LOANS_DB", "./data/loans.json")),
            os.environ.get("READERS_URL", "http://127.0.0.1:8001"),
            os.environ.get("BOOKS_URL", "http://127.0.0.1:8002"),
            os.environ.get("EVENTS_DIR", "./events"),
            int(os.environ.get("CIRCUIT_FAILURES", "2")),
            float(os.environ.get("CIRCUIT_TIMEOUT", "2.0")),
            os.environ.get("BROKER_URL"),
        )
    return _service


def _out(loan) -> LoanOut:
    return LoanOut(**loan.to_dict())


def _handle_unavailable(exc: ServiceUnavailableError):
    logger.error("недоступность зависимого сервиса: %s", exc)
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))


@router.get("/health")
def health():
    loans = get_service()
    # Health check показывает состояние зависимостей (агрегированно)
    deps = {
        "readers": loans._readers.breaker.state.value,
        "books": loans._books.breaker.state.value,
    }
    return {"status": "healthy", "service": "loans-service", "circuit_breakers": deps}


@router.get("/loans", response_model=list[LoanOut])
def list_loans():
    return [_out(l) for l in get_service().list_loans()]


@router.post("/loans", response_model=LoanOut, status_code=status.HTTP_201_CREATED)
def issue_loan(payload: LoanCreate):
    try:
        loan = get_service().issue_loan(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except ServiceUnavailableError as exc:
        _handle_unavailable(exc)
    return _out(loan)


@router.post("/loans/{loan_id}/return", response_model=LoanOut)
def return_loan(loan_id: str):
    try:
        loan = get_service().return_loan(loan_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if loan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="выдача не найдена")
    return _out(loan)


@router.get("/loans/{loan_id}", response_model=LoanOut)
def get_loan(loan_id: str):
    loan = get_service().get_loan(loan_id)
    if loan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="выдача не найдена")
    return _out(loan)


@router.get("/events")
def events():
    """События шины для проверки асинхронного взаимодействия."""
    return get_service()._event_bus.poll()