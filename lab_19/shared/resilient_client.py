"""HTTP-клиент с паттернами Retry и Circuit Breaker.

Retry:
  - ограниченное число попыток;
  - timeout на запрос;
  - задержка между попытками (exponential backoff);
  - окончательная обработка ошибки.
Circuit Breaker:
  - состояния CLOSED -> OPEN -> HALF-OPEN -> CLOSED;
  - порог числа ошибок для открытия;
  - период ожидания перед тестовым запросом (HALF-OPEN).
"""

from __future__ import annotations

import logging
import time
from enum import Enum

import httpx

logger = logging.getLogger(__name__)


class CircuitBreakerState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreakerError(RuntimeError):
    """Возникает, когда Circuit Breaker в состоянии OPEN без обращения к сервису."""


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 5.0, name: str = "service"):
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._name = name
        self._failures = 0
        self._opened_at: float | None = None
        self._state = CircuitBreakerState.CLOSED

    @property
    def state(self) -> CircuitBreakerState:
        self._maybe_half_open()
        return self._state

    def _maybe_half_open(self):
        if self._state is CircuitBreakerState.OPEN and self._opened_at is not None:
            if time.monotonic() - self._opened_at >= self._recovery_timeout:
                self._state = CircuitBreakerState.HALF_OPEN
                logger.warning("[cb %s] -> HALF-OPEN (пробный запрос)", self._name)

    def before_request(self):
        self._maybe_half_open()
        if self._state is CircuitBreakerState.OPEN:
            raise CircuitBreakerError(f"[cb {self._name}] сбросник открыт (OPEN), запрос отклонён без обращения к сервису")

    def on_success(self):
        if self._state is not CircuitBreakerState.CLOSED:
            logger.info("[cb %s] успех -> CLOSED", self._name)
        self._state = CircuitBreakerState.CLOSED
        self._failures = 0
        self._opened_at = None

    def on_error(self):
        self._failures += 1
        if self._state is CircuitBreakerState.HALF_OPEN or self._failures >= self._failure_threshold:
            self._state = CircuitBreakerState.OPEN
            self._opened_at = time.monotonic()
            self._failures = 0
            logger.warning("[cb %s] ошибка -> OPEN (ошибок накоплено)", self._name)


class ResilientClient:
    """Обёртка над httpx с паттернами Retry и Circuit Breaker."""

    def __init__(
        self,
        base_url: str,
        *,
        max_retries: int = 3,
        timeout: float = 2.0,
        base_backoff: float = 0.3,
        breaker: CircuitBreaker | None = None,
    ):
        self._base_url = base_url.rstrip("/")
        self._max_retries = max_retries
        self._timeout = timeout
        self._base_backoff = base_backoff
        self._breaker = breaker or CircuitBreaker(name=self._base_url)
        self._client = httpx.Client(timeout=timeout)

    @property
    def breaker(self) -> CircuitBreaker:
        return self._breaker

    def _url(self, path: str) -> str:
        return f"{self._base_url}/{path.lstrip('/')}"

    def _is_retryable(self, status: int | None) -> bool:
        # временные ошибки и "сервис недоступен" подлежат повтору
        return status in (502, 503, 504) or status is None

    def _request(self, method: str, path: str, **kwargs):
        last_exc: Exception | None = None
        for attempt in range(1, self._max_retries + 1):
            self._breaker.before_request()
            try:
                resp = self._client.request(method, self._url(path), **kwargs)
                if resp.status_code < 500:
                    self._breaker.on_success()
                    return resp
                # 5xx -> возможно retry
                if not self._is_retryable(resp.status_code):
                    self._breaker.on_error()
                    return resp
                if attempt < self._max_retries:
                    delay = self._base_backoff * (2 ** (attempt - 1))
                    logger.warning("retry %d/%d для %s %s (status=%s), жду %.2fs", attempt, self._max_retries, method, path, resp.status_code, delay)
                    time.sleep(delay)
                last_exc = httpx.HTTPStatusError(f"{method} {path} -> {resp.status_code}", request=resp.request, response=resp)
            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
                if attempt < self._max_retries:
                    delay = self._base_backoff * (2 ** (attempt - 1))
                    logger.warning("retry %d/%d для %s %s (network), жду %.2fs", attempt, self._max_retries, method, path, delay)
                    time.sleep(delay)
                last_exc = exc
        self._breaker.on_error()
        raise last_exc if last_exc else ConnectionError("не удалось выполнить запрос")

    def get(self, path: str, **kwargs) -> httpx.Response:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> httpx.Response:
        return self._request("POST", path, **kwargs)

    def put(self, path: str, **kwargs) -> httpx.Response:
        return self._request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs) -> httpx.Response:
        return self._request("DELETE", path, **kwargs)