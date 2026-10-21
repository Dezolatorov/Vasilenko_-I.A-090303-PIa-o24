"""Общие фикстуры для тестов ЛР18."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from repositories.sqlite_repository import SQLiteShopRepository  # noqa: E402
from services.shop_service import ShopService  # noqa: E402


@pytest.fixture()
def repo() -> SQLiteShopRepository:
    return SQLiteShopRepository(":memory:")


@pytest.fixture()
def service(repo: SQLiteShopRepository) -> ShopService:
    return ShopService(repo)


@pytest.fixture()
def mock_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def mock_service(mock_repo: MagicMock) -> ShopService:
    return ShopService(mock_repo)
