"""Общие средства межсервисного взаимодействия: HTTP-клиент с Retry и Circuit Breaker.

Паттерны Retry и Circuit Breaker реализованы в классе ResilientClient.
Распределённая система без общего брокера использует упрощённую файловую
шину событий (см. event_bus.py), так как в учебной среде отсутствуют Docker,
Kafka и RabbitMQ.
"""

from .resilient_client import ResilientClient, CircuitBreakerError, CircuitBreakerState  # noqa: F401
from .storage import JsonStorage  # noqa: F401
from .event_bus import FileEventBus  # noqa: F401