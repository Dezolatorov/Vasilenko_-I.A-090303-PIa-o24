"""Интеграционные тесты: сервис + реальный SQLite-репозиторий."""
from __future__ import annotations

import pytest

from errors import InsufficientStockError, NotFoundError
from repositories.sqlite_repository import SQLiteShopRepository
from services.shop_service import ShopService


@pytest.fixture()
def real_service() -> ShopService:
    repository = SQLiteShopRepository(":memory:")
    return ShopService(repository)


def test_product_crud_with_real_database(real_service: ShopService):
    created = real_service.create_product("Клавиатура", 3500, 5)
    assert created.id == 1

    fetched = real_service.get_product(created.id)
    assert fetched.name == "Клавиатура"
    assert fetched.quantity == 5

    updated = real_service.update_product(created.id, price=3200)
    assert updated.price == 3200

    real_service.delete_product(created.id)
    with pytest.raises(NotFoundError):
        real_service.get_product(created.id)


def test_change_quantity_persists(real_service: ShopService):
    product = real_service.create_product("Мышь", 1500, 5)

    increased = real_service.change_quantity(product.id, 3)
    decreased = real_service.change_quantity(product.id, -4)

    assert increased.quantity == 8
    assert decreased.quantity == 4
    assert real_service.get_product(product.id).quantity == 4


def test_create_order_decrements_stock(real_service: ShopService):
    keyboard = real_service.create_product("Клавиатура", 3500, 5)
    mouse = real_service.create_product("Мышь", 1500, 10)

    order = real_service.create_order("Иванов", [(keyboard.id, 2), (mouse.id, 1)])

    assert order.total == 8500
    assert real_service.get_product(keyboard.id).quantity == 3
    assert real_service.get_product(mouse.id).quantity == 9
    stored = real_service.get_order(order.id)
    assert stored.total == 8500
    assert len(stored.items) == 2


def test_order_cannot_exceed_stock_and_rolls_back(real_service: ShopService):
    product = real_service.create_product("Монитор", 25000, 1)

    with pytest.raises(InsufficientStockError):
        real_service.create_order("Петров", [(product.id, 2)])

    assert real_service.get_product(product.id).quantity == 1
    assert list(real_service.list_orders()) == []
