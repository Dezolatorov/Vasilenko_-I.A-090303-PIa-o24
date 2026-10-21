"""Репозиторий интернет-магазина на SQLite (уровень доступа к данным)."""
from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Optional, Sequence

from errors import NotFoundError, ValidationError
from models.order import Order, OrderItem
from models.product import Product


class SQLiteShopRepository:
    """Хранит товары и заказы; бизнес-логики не содержит."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_schema()

    def _create_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL CHECK (price >= 0),
                quantity INTEGER NOT NULL CHECK (quantity >= 0)
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'created'
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
                product_name TEXT NOT NULL,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity > 0)
            );
            """
        )
        self.conn.commit()

    # ------------------------------------------------------------------
    # Товары
    # ------------------------------------------------------------------
    def add_product(self, product: Product) -> Product:
        cursor = self.conn.execute(
            "INSERT INTO products (name, price, quantity) VALUES (?, ?, ?)",
            (product.name, product.price, product.quantity),
        )
        self.conn.commit()
        product.id = int(cursor.lastrowid)
        return product

    def get_product(self, product_id: int) -> Optional[Product]:
        row = self.conn.execute(
            "SELECT id, name, price, quantity FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()
        if row is None:
            return None
        return Product(
            id=row["id"],
            name=row["name"],
            price=float(row["price"]),
            quantity=int(row["quantity"]),
        )

    def list_products(self) -> Sequence[Product]:
        rows = self.conn.execute(
            "SELECT id, name, price, quantity FROM products ORDER BY id"
        ).fetchall()
        return [
            Product(
                id=row["id"],
                name=row["name"],
                price=float(row["price"]),
                quantity=int(row["quantity"]),
            )
            for row in rows
        ]

    def update_product(self, product: Product) -> Product:
        cursor = self.conn.execute(
            "UPDATE products SET name = ?, price = ?, quantity = ? WHERE id = ?",
            (product.name, product.price, product.quantity, product.id),
        )
        self.conn.commit()
        if cursor.rowcount == 0:
            raise NotFoundError(f"Товар #{product.id} не найден")
        return product

    def delete_product(self, product_id: int) -> bool:
        cursor = self.conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def change_quantity(self, product_id: int, delta: int) -> Product:
        product = self.get_product(product_id)
        if product is None:
            raise NotFoundError(f"Товар #{product_id} не найден")
        new_quantity = product.quantity + delta
        if new_quantity < 0:
            raise ValidationError("Количество не может стать отрицательным")
        self.conn.execute(
            "UPDATE products SET quantity = ? WHERE id = ?",
            (new_quantity, product_id),
        )
        self.conn.commit()
        product.quantity = new_quantity
        return product

    # ------------------------------------------------------------------
    # Заказы
    # ------------------------------------------------------------------
    def save_order(self, customer: str, items: Sequence[OrderItem]) -> Order:
        """Сохраняет заказ и уменьшает остатки в одной транзакции."""
        order = Order(id=None, customer=customer, items=list(items))
        try:
            cursor = self.conn.execute(
                "INSERT INTO orders (customer, created_at, status) VALUES (?, ?, ?)",
                (order.customer, order.created_at.isoformat(timespec="seconds"), order.status),
            )
            order_id = int(cursor.lastrowid)
            for item in items:
                self.conn.execute(
                    "INSERT INTO order_items "
                    "(order_id, product_id, product_name, price, quantity) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (order_id, item.product_id, item.product_name, item.price, item.quantity),
                )
                updated = self.conn.execute(
                    "UPDATE products SET quantity = quantity - ? "
                    "WHERE id = ? AND quantity >= ?",
                    (item.quantity, item.product_id, item.quantity),
                )
                if updated.rowcount == 0:
                    raise ValidationError(
                        f"Недостаточно товара «{item.product_name}» на складе"
                    )
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
        order.id = order_id
        return order

    def get_order(self, order_id: int) -> Optional[Order]:
        row = self.conn.execute(
            "SELECT id, customer, created_at, status FROM orders WHERE id = ?",
            (order_id,),
        ).fetchone()
        if row is None:
            return None
        items = self.conn.execute(
            "SELECT product_id, product_name, price, quantity "
            "FROM order_items WHERE order_id = ? ORDER BY id",
            (order_id,),
        ).fetchall()
        return Order(
            id=row["id"],
            customer=row["customer"],
            created_at=datetime.fromisoformat(row["created_at"]),
            status=row["status"],
            items=[
                OrderItem(
                    product_id=item["product_id"],
                    product_name=item["product_name"],
                    price=float(item["price"]),
                    quantity=int(item["quantity"]),
                )
                for item in items
            ],
        )

    def list_orders(self) -> Sequence[Order]:
        rows = self.conn.execute("SELECT id FROM orders ORDER BY id").fetchall()
        return [self.get_order(row["id"]) for row in rows]
