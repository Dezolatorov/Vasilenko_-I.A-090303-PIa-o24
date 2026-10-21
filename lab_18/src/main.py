"""Точка входа интернет-магазина (ЛР18)."""
from __future__ import annotations

from repositories.sqlite_repository import SQLiteShopRepository
from services.cli import ConsoleUI
from services.shop_service import ShopService


def seed(service: ShopService) -> None:
    service.create_product("Клавиатура", 3500, 10)
    service.create_product("Мышь", 1500, 25)
    service.create_product("Монитор", 25000, 4)


def main() -> None:
    repository = SQLiteShopRepository(":memory:")
    service = ShopService(repository)
    seed(service)
    ConsoleUI(service).run()


if __name__ == "__main__":
    main()
