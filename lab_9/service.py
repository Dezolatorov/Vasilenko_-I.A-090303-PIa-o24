import re
import logging
from models import Calculation
from repository import CalculationRepository
from exceptions import CalculationError, CalculationNotFoundError

logger = logging.getLogger(__name__)

# Разрешены: цифры, пробелы, + - * / ( ) . , % ^
_SAFE_PATTERN = re.compile(r"^[\d\s+\-*/().,%^]+$")


class CalculatorService:
    """Бизнес-логика калькулятора и работа с историей вычислений."""

    def __init__(self, repository: CalculationRepository) -> None:
        self.repository = repository

    # ---------- Валидация ----------
    def _validate_expression(self, expression: str) -> None:
        if not expression or not expression.strip():
            raise CalculationError("Выражение пустое")
        if not _SAFE_PATTERN.match(expression):
            raise CalculationError("Выражение содержит недопустимые символы")
        # Нельзя два оператора подряд (кроме **)
        normalized = expression.replace("**", "*")
        if re.search(r"[+\-*/^%]{2,}", normalized):
            raise CalculationError("Недопустимая последовательность операторов")

    # ---------- Вычисление ----------
    def _evaluate(self, expression: str) -> float:
        expr = expression.replace("^", "**")
        try:
            result = eval(expr, {"__builtins__": {}}, {})
        except ZeroDivisionError:
            raise CalculationError("Деление на ноль")
        except Exception as e:
            raise CalculationError(f"Некорректное выражение: {e}")

        if isinstance(result, bool) or not isinstance(result, (int, float)):
            raise CalculationError("Выражение не даёт числовой результат")
        return float(result)

    # ---------- Операции ----------
    def calculate(self, expression: str) -> Calculation:
        logger.info("calculate: %s", expression)
        self._validate_expression(expression)
        result = self._evaluate(expression)
        calc = self.repository.add(expression, result)
        logger.info("result=%.4f id=%d", calc.result, calc.id)
        return calc

    def get(self, calc_id: int) -> Calculation:
        calc = self.repository.get(calc_id)
        if calc is None:
            raise CalculationNotFoundError(f"Вычисление с id={calc_id} не найдено")
        return calc

    def get_all(self) -> list[Calculation]:
        return self.repository.get_all()

    def update(self, calc_id: int, expression: str) -> Calculation:
        self._validate_expression(expression)
        result = self._evaluate(expression)
        calc = self.repository.update(calc_id, expression, result)
        if calc is None:
            raise CalculationNotFoundError(f"Вычисление с id={calc_id} не найдено")
        return calc

    def delete(self, calc_id: int) -> None:
        if not self.repository.delete(calc_id):
            raise CalculationNotFoundError(f"Вычисление с id={calc_id} не найдено")

    def clear(self) -> int:
        return self.repository.clear()

    def history(self, limit: int = 10) -> list[Calculation]:
        if limit <= 0:
            raise CalculationError("limit должен быть > 0")
        items = self.repository.get_all()
        items.sort(key=lambda c: c.id, reverse=True)
        return items[:limit]