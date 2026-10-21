"""Доменные исключения и формат ошибок API."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class DomainError(Exception):
    """Базовое доменное исключение."""

    code: str = "DOMAIN_ERROR"
    status_code: int = 400

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class EntityNotFoundException(DomainError):
    code = "ENTITY_NOT_FOUND"
    status_code = 404


class ValidationException(DomainError):
    code = "VALIDATION_ERROR"
    status_code = 422


class BusinessRuleException(DomainError):
    code = "BUSINESS_RULE_VIOLATION"
    status_code = 409


class AuthenticationException(DomainError):
    code = "AUTHENTICATION_FAILED"
    status_code = 401


class AuthorizationException(DomainError):
    code = "FORBIDDEN"
    status_code = 403


class ConflictException(DomainError):
    code = "CONFLICT"
    status_code = 409


class ExternalServiceException(DomainError):
    code = "EXTERNAL_SERVICE_ERROR"
    status_code = 503


@dataclass
class ErrorResponse:
    """Стандартный ответ об ошибке API."""

    error: str
    message: str
    status: int

    def to_dict(self) -> dict[str, Any]:
        return {"error": self.error, "message": self.message}