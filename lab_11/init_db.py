"""Создание БД: схема + тестовые данные.

Запуск: python init_db.py
"""

import config
from db import Database


def main() -> None:
    database = Database(config.DB_PATH)
    database.reset()

    with database.connection() as connection:
        counts = {}
        for table in ("authors", "books", "readers", "loans", "tags", "book_tags"):
            counts[table] = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        indexes = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()

    print(f"База данных создана: {config.DB_PATH}")
    for table, count in counts.items():
        print(f"  {table:<10} записей: {count}")
    print("Индексы:")
    for row in indexes:
        print(f"  {row[0]}")


if __name__ == "__main__":
    main()
