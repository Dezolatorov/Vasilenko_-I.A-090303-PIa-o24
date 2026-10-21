"""Исключения приложения и единый формат ошибок API."""


class ApiError(Exception):
    """Базовое исключение приложения, превращаемое в JSON-ответ с ошибкой."""

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
    code = "NOT_FOUND"
    message = "Resource not found"


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


class ConflictError(ApiError):
    """Операция противоречит состоянию данных (нет свободных экземпляров и т. п.)."""

    status_code = 409
    code = "CONFLICT"
    message = "Operation conflicts with current state"


class DatabaseError(ApiError):
    """Ошибка уровня хранения, транзакция откатана."""

    status_code = 500
    code = "DATABASE_ERROR"
    message = "Database error"
