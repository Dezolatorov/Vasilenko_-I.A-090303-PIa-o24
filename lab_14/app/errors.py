from __future__ import annotations


class AppError(Exception):
    code = "APP_ERROR"
    status_code = 500

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    code = "NOT_FOUND"
    status_code = 404

    def __init__(self, book_id: object) -> None:
        super().__init__(f"Книга с идентификатором {book_id} не найдена")


class ConflictError(AppError):
    code = "CONFLICT"
    status_code = 409


class ValidationError(AppError):
    code = "VALIDATION_ERROR"
    status_code = 400
