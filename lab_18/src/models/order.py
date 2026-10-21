"""Заказ интернет-магазина и его позиции."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class OrderItem:
    product_id: int
    product_name: str
    price: float
    quantity: int

    @property
    def total(self) -> float:
        return round(self.price * self.quantity, 2)


@dataclass
class Order:
    id: int | None
    customer: str
    items: list[OrderItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "created"

    @property
    def total(self) -> float:
        """Стоимость заказа: сумма по всем позициям."""
        return round(sum(item.total for item in self.items), 2)

    @property
    def items_count(self) -> int:
        return sum(item.quantity for item in self.items)
