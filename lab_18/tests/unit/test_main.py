"""Тест демонстрационного заполнения каталога."""
from __future__ import annotations

from unittest.mock import MagicMock

import main
from services.shop_service import ShopService


def test_seed_creates_three_products():
    repository = MagicMock()
    repository.add_product.side_effect = lambda product: product
    service = ShopService(repository)

    main.seed(service)

    assert repository.add_product.call_count == 3
