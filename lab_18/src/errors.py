"""Доменные исключения интернет-магазина."""


class ShopError(Exception):
    """Базовая ошибка предметной области."""


class ValidationError(ShopError):
    """Некорректные входные данные."""


class NotFoundError(ShopError):
    """Объект не найден."""


class InsufficientStockError(ShopError):
    """На складе недостаточно товара для заказа."""
