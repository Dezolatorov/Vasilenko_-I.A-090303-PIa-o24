class ProtocolError(Exception):
    """Ошибка прикладного протокола (некорректный JSON/структура)."""
    pass


class CalculationError(Exception):
    """Некорректное математическое выражение."""
    pass


class CalculationNotFoundError(Exception):
    """Вычисление с заданным id не найдено."""
    pass