"""Исключения приложения и единый формат ошибок API."""


class ApiError(Exception):
    """Базовое исключение приложения, преобразуемое в JSON-ответ с ошибкой."""

    status_code: int = 500
    code: str = "INTERNAL_ERROR"
    message: str = "Internal server error"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.message)
        self.message = message or self.message

    def to_dict(self) -> dict:
        return {"error": self.message, "code": self.code}


class NotFoundError(ApiError):
    """Запрошенный ресурс отсутствует в хранилище."""

    status_code = 404
    code = "BOOK_NOT_FOUND"
    message = "Book not found"


class ValidationError(ApiError):
    """Данные запроса не прошли проверку."""

    status_code = 400
    code = "VALIDATION_ERROR"
    message = "Invalid request data"


class BadRequestError(ApiError):
    """Запрос сформирован некорректно: тело, идентификатор или параметры."""

    status_code = 400
    code = "INVALID_REQUEST"
    message = "Malformed request"
