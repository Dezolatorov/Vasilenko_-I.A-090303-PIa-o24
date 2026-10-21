from __future__ import annotations


class AppError(Exception):
    """Базовая ошибка приложения."""

    code = "APP_ERROR"


class NotFoundError(AppError):
    code = "NOT_FOUND"

    def __init__(self, entity: str, entity_id: object) -> None:
        super().__init__(f"{entity} с идентификатором {entity_id} не найден(а)")
        self.entity = entity
        self.entity_id = entity_id


class ValidationError(AppError):
    code = "VALIDATION_ERROR"


class DuplicateError(AppError):
    code = "DUPLICATE"


class ForeignKeyError(AppError):
    code = "FOREIGN_KEY_ERROR"


class TransactionError(AppError):
    code = "TRANSACTION_ERROR"
