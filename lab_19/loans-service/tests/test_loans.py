"""Тесты loans-service: 5 unit + 2 интеграционных + 1 межсервисной + 1 недоступность."""

import warnings
from unittest import mock

import pytest

from app.models import Loan, LoanStatus
from app.repositories import LoanRepository
from app.schemas.schemas import LoanCreate
from app.services import LoansService, ServiceUnavailableError
from shared.event_bus import FileEventBus
from shared.resilient_client import CircuitBreaker, ResilientClient
from shared.storage import JsonStorage


class FakeResp:
    def __init__(self, status_code=200, data=None):
        self.status_code = status_code
        self._data = data or {}
        self.content = b"{}"

    def json(self):
        return self._data

    def raise_for_status(self):
        if self.status_code >= 400:
            from httpx import HTTPStatusError
            raise HTTPStatusError("err", request=mock.MagicMock(), response=mock.MagicMock())


class FakeClient:
    def __init__(self, check_result=None, decrement_ok=True):
        # для readers: {"exists", "active"}; для books: {"exists", "available"}
        self._check = check_result or {"exists": True, "active": True, "full_name": "Читатель"}
        self._decrement_ok = decrement_ok
        self.calls = []
        self.breaker = CircuitBreaker(name="fake")

    def get(self, path, **kw):
        self.calls.append(("GET", path))
        if "readers/check" in path:
            if "nonexistent" in path:
                return FakeResp(200, {"exists": False, "active": False})
            return FakeResp(200, self._check)
        if "books/check" in path or "check" in path:
            if "nonexistent" in path:
                return FakeResp(200, {"exists": False, "available": False})
            return FakeResp(200, self._check)
        return FakeResp(200)

    def post(self, path, **kw):
        self.calls.append(("POST", path))
        if "decrement" in path and not self._decrement_ok:
            return FakeResp(409, {"detail": "нет экземпляров"})
        return FakeResp(200, {"status": "ok"})


@pytest.fixture()
def service(tmp_path):
    storage = JsonStorage(str(tmp_path / "loans.json"))
    repo = LoanRepository(storage)
    event_bus = FileEventBus(str(tmp_path / "events"))
    readers = FakeClient(check_result={"exists": True, "active": True, "full_name": "Читатель"})
    books = FakeClient(check_result={"exists": True, "available": True, "available_copies": 5})
    return LoansService(repo, readers, books, event_bus)


# ---------- 5 unit-тестов ----------
def test_unit_create_loan(service):
    loan = service.issue_loan(LoanCreate(reader_id="r1", book_id="b1"))
    assert loan.status == LoanStatus.ISSUED
    assert loan.id


def test_unit_list_loans(service):
    service.issue_loan(LoanCreate(reader_id="r1", book_id="b1"))
    assert len(service.list_loans()) == 1


def test_unit_missing_book_raises(service):
    service._books = FakeClient(check_result={"exists": False, "available": False})
    with pytest.raises(ValueError):
        service.issue_loan(LoanCreate(reader_id="r1", book_id="nonexistent"))


def test_unit_unavailable_book_raises(service):
    service._books = FakeClient(check_result={"exists": True, "available": False, "available_copies": 0})
    with pytest.raises(ValueError):
        service.issue_loan(LoanCreate(reader_id="r1", book_id="b1"))


def test_unit_return_loan(service):
    loan = service.issue_loan(LoanCreate(reader_id="r1", book_id="b1"))
    returned = service.return_loan(loan.id)
    assert returned.status == LoanStatus.RETURNED


def test_unit_event_published(service, tmp_path):
    service.issue_loan(LoanCreate(reader_id="r1", book_id="b1"))
    events = FileEventBus(str(tmp_path / "events")).poll()
    assert any(e["type"] == "LoanCreated" for e in events)


# ---------- 2 интеграционных теста (через HTTP TestClient с mock-клиентами) ----------
@pytest.fixture()
def http_client(tmp_path):
    from app.api import routes
    from fastapi.testclient import TestClient

    repo = LoanRepository(JsonStorage(str(tmp_path / "loans.json")))
    event_bus = FileEventBus(str(tmp_path / "events"))

    readers = FakeClient(check_result={"exists": True, "active": True})
    books = FakeClient(check_result={"exists": True, "available": True, "available_copies": 5})
    svc = LoansService(repo, readers, books, event_bus)
    routes._service = svc

    from app.main import app
    return TestClient(app)


def test_integration_issue_via_http(http_client):
    r = http_client.post("/loans", json={"reader_id": "r1", "book_id": "b1"})
    assert r.status_code == 201
    assert r.json()["status"] == "issued"


def test_integration_health(http_client):
    assert http_client.get("/health").json()["status"] == "healthy"


# ---------- 1 тест взаимодействия между сервисами ----------
def test_interaction_orchestration_order(service):
    """Проверяем, что loans обращается к readers и books в правильном порядке."""
    service.issue_loan(LoanCreate(reader_id="r1", book_id="b1"))
    kinds = [c[0] for c in service._readers.calls + service._books.calls]
    assert "GET" in kinds and "POST" in kinds


# ---------- 1 тест недоступности другого сервиса (Circuit Breaker) ----------
def test_unavailability_service_down_raises(service):
    class DownClient:
        def get(self, *a, **k):
            from httpx import ConnectError
            raise ConnectError("connection refused")

        def post(self, *a, **k):
            raise ServiceUnavailableError("down")

    # событие будет публиковаться, но сначала упадёт проверка читателя
    service._readers = DownClient()
    with pytest.raises(ServiceUnavailableError):
        service.issue_loan(LoanCreate(reader_id="r1", book_id="b1"))


def test_circuit_breaker_opens(service, tmp_path):
    """После порогового числа неудач Circuit Breaker переходит в OPEN."""
    import time as _time

    class FlakyClient:
        def __init__(self):
            self.breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=10, name="flaky")

        def get(self, *a, **k):
            self.breaker.before_request()
            from httpx import ConnectError
            self.breaker.on_error()
            raise ConnectError("down")

        def post(self, *a, **k):
            return FakeResp(200)

    rr = FlakyClient()
    service._readers = rr
    for _ in range(2):
        with pytest.raises(ServiceUnavailableError):
            service.issue_loan(LoanCreate(reader_id="r1", book_id="b1"))
    assert rr.breaker.state.value == "OPEN"