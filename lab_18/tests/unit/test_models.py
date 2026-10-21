"""Тесты моделей товара и заказа."""
from __future__ import annotations

import pytest

from errors import ValidationError
from models.order import Order, OrderItem
from models.product import Product


def test_product_total_value():
    product = Product(id=1, name="Мышь", price=1500, quantity=3)
    assert product.total_value == 4500


@pytest.mark.parametrize(
    "price,quantity,expected",
    [
        (0, 0, 0),
        (100, 2, 200),
        (99.9, 3, 299.7),
    ],
)
def test_product_total_value_parametrized(price, quantity, expected):
    product = Product(id=1, name="Товар", price=price, quantity=quantity)
    assert product.total_value == expected


def test_product_rejects_empty_name():
    with pytest.raises(ValidationError):
        Product(id=None, name="   ", price=10, quantity=1)


def test_product_rejects_negative_price():
    with pytest.raises(ValidationError):
        Product(id=None, name="Товар", price=-1, quantity=1)


def test_product_rejects_negative_quantity():
    with pytest.raises(ValidationError):
        Product(id=None, name="Товар", price=10, quantity=-5)


@pytest.mark.parametrize("quantity", [0, 1, -1])
def test_product_quantity_boundaries(quantity):
    if quantity < 0:
        with pytest.raises(ValidationError):
            Product(id=None, name="Товар", price=10, quantity=quantity)
    else:
        assert Product(id=None, name="Товар", price=10, quantity=quantity).quantity == quantity


def test_order_total_and_items_count():
    order = Order(
        id=1,
        customer="Иванов",
        items=[
            OrderItem(product_id=1, product_name="Мышь", price=1500, quantity=2),
            OrderItem(product_id=2, product_name="Клавиатура", price=3500, quantity=1),
        ],
    )
    assert order.total == 6500
    assert order.items_count == 3


def test_empty_order_total_is_zero():
    order = Order(id=None, customer="Иванов")
    assert order.total == 0
    assert order.items_count == 0
