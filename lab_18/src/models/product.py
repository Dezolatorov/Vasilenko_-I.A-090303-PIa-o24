"""Товар интернет-магазина."""
from __future__ import annotations

from dataclasses import dataclass

from errors import ValidationError


@dataclass
class Product:
    id: int | None
    name: str
    price: float
    quantity: int

    def __post_init__(self) -> None:
        self.name = (self.name or "").strip()
        if not self.name:
            raise ValidationError("Название товара обязательно")
        if self.price < 0:
            raise ValidationError("Цена не может быть отрицательной")
        if self.quantity < 0:
            raise ValidationError("Количество не может быть отрицательным")

    @property
    def total_value(self) -> float:
        """Стоимость остатка на складе."""
        return round(self.price * self.quantity, 2)
