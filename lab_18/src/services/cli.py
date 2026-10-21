"""Консольный интерфейс интернет-магазина."""
from __future__ import annotations

from errors import ShopError
from services.shop_service import ShopService


class ConsoleUI:
    def __init__(self, service: ShopService) -> None:
        self.service = service

    def run(self) -> None:
        while True:
            self._print_menu()
            choice = input("Выберите действие: ").strip()
            try:
                if choice == "1":
                    self._list_products()
                elif choice == "2":
                    self._add_product()
                elif choice == "3":
                    self._change_quantity()
                elif choice == "4":
                    self._create_order()
                elif choice == "5":
                    self._list_orders()
                elif choice == "0":
                    print("Выход.")
                    return
                else:
                    print("Неизвестная команда.")
            except ShopError as error:
                print(f"Ошибка: {error}")

    @staticmethod
    def _print_menu() -> None:
        print("\n===== ИНТЕРНЕТ-МАГАЗИН =====")
        print("1. Показать товары")
        print("2. Добавить товар")
        print("3. Изменить количество товара")
        print("4. Создать заказ")
        print("5. Показать заказы")
        print("0. Выход")

    def _list_products(self) -> None:
        products = self.service.list_products()
        if not products:
            print("Каталог пуст.")
            return
        for product in products:
            print(
                f"[{product.id}] {product.name} — {product.price:.2f} руб., "
                f"остаток: {product.quantity}"
            )

    def _add_product(self) -> None:
        name = input("Название: ").strip()
        price = float(input("Цена: ").replace(",", "."))
        quantity = int(input("Количество: "))
        product = self.service.create_product(name, price, quantity)
        print(f"Товар добавлен: [{product.id}] {product.name}")

    def _change_quantity(self) -> None:
        product_id = int(input("ID товара: "))
        delta = int(input("Изменение количества (например, -2 или 5): "))
        product = self.service.change_quantity(product_id, delta)
        print(f"Новый остаток «{product.name}»: {product.quantity}")

    def _create_order(self) -> None:
        customer = input("Покупатель: ").strip()
        items: list[tuple[int, int]] = []
        while True:
            raw = input("Товар (ID или пусто для завершения): ").strip()
            if not raw:
                break
            quantity = int(input("Количество: "))
            items.append((int(raw), quantity))
        order = self.service.create_order(customer, items)
        print(f"Заказ #{order.id} создан. Позиций: {len(order.items)}, "
              f"сумма: {order.total:.2f} руб.")

    def _list_orders(self) -> None:
        orders = self.service.list_orders()
        if not orders:
            print("Заказов нет.")
            return
        for order in orders:
            print(f"#{order.id} {order.customer}: {order.items_count} шт., "
                  f"{order.total:.2f} руб.")
