from typing import Optional
from models import Calculation


class CalculationRepository:
    """Хранилище вычислений в памяти процесса."""

    def __init__(self) -> None:
        self._items: dict[int, Calculation] = {}
        self._next_id: int = 1

    def add(self, expression: str, result: float) -> Calculation:
        calc = Calculation(id=self._next_id, expression=expression, result=result)
        self._items[calc.id] = calc
        self._next_id += 1
        return calc

    def get(self, calc_id: int) -> Optional[Calculation]:
        return self._items.get(calc_id)

    def get_all(self) -> list[Calculation]:
        return list(self._items.values())

    def update(self, calc_id: int, expression: str, result: float) -> Optional[Calculation]:
        calc = self._items.get(calc_id)
        if calc is None:
            return None
        calc.expression = expression
        calc.result = result
        return calc

    def delete(self, calc_id: int) -> bool:
        return self._items.pop(calc_id, None) is not None

    def clear(self) -> int:
        count = len(self._items)
        self._items.clear()
        self._next_id = 1
        return count