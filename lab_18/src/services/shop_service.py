"""Бизнес-логика интернет-магазина (сервисный уровень)."""
from __future__ import annotations

from typing import Optional, Sequence

from errors import InsufficientStockError, NotFoundError, ValidationError
from models.order import Order, OrderItem
from models.product import Product


class ShopService:
    def __init__(self, repository) -> None:
        self.repository = repository

    # ------------------------------------------------------------------
    # Товары
    # ------------------------------------------------------------------
    def create_product(self, name: str, price: float, quantity: int) -> Product:
        product = Product(id=None, name=name, price=float(price), quantity=int(quantity))
        return self.repository.add_product(product)

    def get_product(self, product_id: int) -> Product:
        product = self.repository.get_product(product_id)
        if product is None:
            raise NotFoundError(f"Товар #{product_id} не найден")
        return product

    def list_products(self) -> Sequence[Product]:
        return self.repository.list_products()

    def update_product(
        self,
        product_id: int,
        name: Optional[str] = None,
        price: Optional[float] = None,
        quantity: Optional[int] = None,
    ) -> Product:
        product = self.get_product(product_id)
        updated = Product(
            id=product.id,
            name=name if name is not None else product.name,
            price=float(price) if price is not None else product.price,
            quantity=int(quantity) if quantity is not None else product.quantity,
        )
        return self.repository.update_product(updated)

    def delete_product(self, product_id: int) -> None:
        self.get_product(product_id)
        if not self.repository.delete_product(product_id):
            raise NotFoundError(f"Товар #{product_id} не найден")

    def change_quantity(self, product_id: int, delta: int) -> Product:
        if delta == 0:
            raise ValidationError("Изменение количества не может быть нулевым")
        return self.repository.change_quantity(product_id, int(delta))

    # ------------------------------------------------------------------
    # Заказы
    # ------------------------------------------------------------------
    def create_order(self, customer: str, raw_items: Sequence[tuple[int, int]]) -> Order:
        customer = (customer or "").strip()
        if not customer:
            raise ValidationError("Имя покупателя обязательно")
        if not raw_items:
            raise ValidationError("Заказ должен содержать хотя бы один товар")

        order_items: list[OrderItem] = []
        for product_id, quantity in raw_items:
            if int(quantity) <= 0:
                raise ValidationError("Количество в заказе должно быть положительным")
            product = self.repository.get_product(product_id)
            if product is None:
                raise NotFoundError(f"Товар #{product_id} не найден")
            if product.quantity < int(quantity):
                raise InsufficientStockError(
                    f"Товара «{product.name}» недостаточно: "
                    f"запрошено {quantity}, доступно {product.quantity}"
                )
            order_items.append(
                OrderItem(
                    product_id=product.id,
                    product_name=product.name,
                    price=product.price,
                    quantity=int(quantity),
                )
            )

        return self.repository.save_order(customer, order_items)

    def calculate_total(self, raw_items: Sequence[tuple[int, int]]) -> float:
        """Стоимость заказа без сохранения (для проверки и предпросмотра)."""
        total = 0.0
        for product_id, quantity in raw_items:
            if int(quantity) <= 0:
                raise ValidationError("Количество в заказе должно быть положительным")
            product = self.get_product(product_id)
            if product.quantity < int(quantity):
                raise InsufficientStockError(
                    f"Товара «{product.name}» недостаточно на складе"
                )
            total += product.price * int(quantity)
        return round(total, 2)

    def get_order(self, order_id: int) -> Order:
        order = self.repository.get_order(order_id)
        if order is None:
            raise NotFoundError(f"Заказ #{order_id} не найден")
        return order

    def list_orders(self) -> Sequence[Order]:
        return self.repository.list_orders()
