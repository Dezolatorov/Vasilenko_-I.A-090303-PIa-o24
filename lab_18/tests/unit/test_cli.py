"""Тесты консольного интерфейса с подменой ввода и сервиса."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from errors import NotFoundError
from services.cli import ConsoleUI


def test_cli_prints_products(capsys):
    service = MagicMock()
    service.list_products.return_value = []
    ui = ConsoleUI(service)

    ui._list_products()

    assert "Каталог пуст" in capsys.readouterr().out


def test_cli_add_product_uses_service(monkeypatch):
    service = MagicMock()
    service.create_product.return_value = MagicMock(id=1, name="Мышь")
    ui = ConsoleUI(service)
    inputs = iter(["Мышь", "1500", "3"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))

    ui._add_product()

    service.create_product.assert_called_once_with("Мышь", 1500.0, 3)


def test_cli_reports_service_error(monkeypatch, capsys):
    service = MagicMock()
    service.change_quantity.side_effect = NotFoundError("Товар #5 не найден")
    ui = ConsoleUI(service)
    inputs = iter(["5", "1"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))

    with pytest.raises(NotFoundError):
        ui._change_quantity()

    service.change_quantity.assert_called_once_with(5, 1)
    assert "Товар #5 не найден" in str(service.change_quantity.side_effect)


def test_cli_create_order_collects_items(monkeypatch):
    service = MagicMock()
    service.create_order.return_value = MagicMock(
        id=1, items=[MagicMock()], total=3000
    )
    ui = ConsoleUI(service)
    inputs = iter(["Иванов", "1", "2", ""])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))

    ui._create_order()

    service.create_order.assert_called_once_with("Иванов", [(1, 2)])


def test_cli_add_product_with_patch():
    service = MagicMock()
    service.create_product.return_value = MagicMock(id=1, name="Мышь")
    ui = ConsoleUI(service)

    with patch("builtins.input", side_effect=["Мышь", "1500", "3"]):
        ui._add_product()

    service.create_product.assert_called_once_with("Мышь", 1500.0, 3)
