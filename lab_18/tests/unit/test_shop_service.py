"""Unit-тесты сервисного слоя c Mock-репозиторием."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from errors import InsufficientStockError, NotFoundError, ValidationError
from models.order import Order
from models.product import Product
from services.shop_service import ShopService


def test_create_product_calls_repository(mock_repo: MagicMock):
    mock_repo.add_product.side_effect = lambda product: product
    service = ShopService(mock_repo)

    product = service.create_product("Мышь", 1500, 5)

    assert product.name == "Мышь"
    mock_repo.add_product.assert_called_once()
    sent = mock_repo.add_product.call_args.args[0]
    assert sent.price == 1500 and sent.quantity == 5


def test_get_product_not_found(mock_repo: MagicMock):
    mock_repo.get_product.return_value = None
    service = ShopService(mock_repo)

    with pytest.raises(NotFoundError):
        service.get_product(999)

    mock_repo.get_product.assert_called_once_with(999)


def test_update_product_keeps_unspecified_fields(mock_repo: MagicMock):
    mock_repo.get_product.return_value = Product(id=1, name="Мышь", price=1500, quantity=5)
    mock_repo.update_product.side_effect = lambda product: product
    service = ShopService(mock_repo)

    updated = service.update_product(1, price=1700)

    assert updated.name == "Мышь"
    assert updated.price == 1700
    assert updated.quantity == 5
    mock_repo.update_product.assert_called_once()


def test_delete_missing_product_raises(mock_repo: MagicMock):
    mock_repo.get_product.return_value = None
    service = ShopService(mock_repo)

    with pytest.raises(NotFoundError):
        service.delete_product(42)

    mock_repo.delete_product.assert_not_called()


def test_delete_product_calls_repository(mock_repo: MagicMock):
    mock_repo.get_product.return_value = Product(id=1, name="Мышь", price=10, quantity=1)
    mock_repo.delete_product.return_value = True
    service = ShopService(mock_repo)

    service.delete_product(1)

    mock_repo.delete_product.assert_called_once_with(1)


def test_change_quantity_zero_is_rejected(mock_repo: MagicMock):
    service = ShopService(mock_repo)

    with pytest.raises(ValidationError):
        service.change_quantity(1, 0)

    mock_repo.change_quantity.assert_not_called()


def test_create_order_empty_customer(mock_repo: MagicMock):
    service = ShopService(mock_repo)

    with pytest.raises(ValidationError):
        service.create_order("  ", [(1, 1)])


def test_create_order_without_items(mock_repo: MagicMock):
    service = ShopService(mock_repo)

    with pytest.raises(ValidationError):
        service.create_order("Иванов", [])


def test_create_order_missing_product(mock_repo: MagicMock):
    mock_repo.get_product.return_value = None
    service = ShopService(mock_repo)

    with pytest.raises(NotFoundError):
        service.create_order("Иванов", [(10, 1)])


def test_create_order_insufficient_stock(mock_repo: MagicMock):
    mock_repo.get_product.return_value = Product(id=1, name="Мышь", price=10, quantity=1)
    service = ShopService(mock_repo)

    with pytest.raises(InsufficientStockError):
        service.create_order("Иванов", [(1, 2)])

    mock_repo.save_order.assert_not_called()


def test_create_order_success(mock_repo: MagicMock):
    mock_repo.get_product.return_value = Product(id=1, name="Мышь", price=1500, quantity=5)
    mock_repo.save_order.side_effect = lambda customer, items: Order(
        id=1, customer=customer, items=list(items)
    )
    service = ShopService(mock_repo)

    order = service.create_order("Иванов", [(1, 2)])

    assert order.total == 3000
    mock_repo.save_order.assert_called_once()
    customer, items = mock_repo.save_order.call_args.args
    assert customer == "Иванов"
    assert items[0].quantity == 2


@pytest.mark.parametrize("quantity", [0, -1, -5])
def test_create_order_rejects_non_positive_quantity(mock_repo: MagicMock, quantity):
    service = ShopService(mock_repo)

    with pytest.raises(ValidationError):
        service.create_order("Иванов", [(1, quantity)])


def test_calculate_total(mock_repo: MagicMock):
    mock_repo.get_product.side_effect = lambda product_id: Product(
        id=product_id, name="Товар", price=100, quantity=10
    )
    service = ShopService(mock_repo)

    total = service.calculate_total([(1, 2), (2, 3)])

    assert total == 500


def test_calculate_total_insufficient_stock(mock_repo: MagicMock):
    mock_repo.get_product.return_value = Product(id=1, name="Товар", price=100, quantity=1)
    service = ShopService(mock_repo)

    with pytest.raises(InsufficientStockError):
        service.calculate_total([(1, 2)])


def test_get_order_not_found(mock_repo: MagicMock):
    mock_repo.get_order.return_value = None
    service = ShopService(mock_repo)

    with pytest.raises(NotFoundError):
        service.get_order(7)
