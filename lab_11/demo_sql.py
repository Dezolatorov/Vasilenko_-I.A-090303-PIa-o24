"""Выполнение 15 SQL-запросов из queries.sql с печатью результатов.

Запуск: python demo_sql.py
"""

import re
import sqlite3

import config
from db import Database


def split_statements(script: str) -> list[tuple[str, str]]:
    """Разделить скрипт на (комментарий-заголовок, SQL) по пустым строкам."""
    statements: list[tuple[str, str]] = []
    title = ""
    buffer: list[str] = []

    for line in script.splitlines():
        stripped = line.strip()
        if stripped.startswith("--") and not buffer:
            title = stripped.lstrip("- ").strip()
            continue
        if not stripped:
            if buffer:
                statements.append((title, " ".join(buffer)))
                buffer, title = [], ""
            continue
        buffer.append(stripped)

    if buffer:
        statements.append((title, " ".join(buffer)))
    return statements


def print_rows(cursor: sqlite3.Cursor) -> None:
    columns = [description[0] for description in cursor.description or []]
    rows = cursor.fetchall()
    if not columns:
        print(f"    затронуто строк: {cursor.rowcount}")
        return

    widths = [len(name) for name in columns]
    for row in rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(str(value)))

    line = "    " + " | ".join(name.ljust(widths[index]) for index, name in enumerate(columns))
    print(line)
    print("    " + "-+-".join("-" * width for width in widths))
    for row in rows:
        print("    " + " | ".join(str(value).ljust(widths[index]) for index, value in enumerate(row)))
    print(f"    строк: {len(rows)}")


def main() -> None:
    database = Database(config.DB_PATH)
    script = (config.BASE_DIR / "queries.sql").read_text(encoding="utf-8")
    statements = split_statements(script)

    print("=" * 78)
    print(f"ВЫПОЛНЕНИЕ {len(statements)} SQL-ЗАПРОСОВ (БД: {config.DB_PATH.name})")
    print("=" * 78)

    connection = database.connect()
    try:
        for number, (title, query) in enumerate(statements, start=1):
            print()
            print(f"{number}. {title}")
            print(f"    SQL: {re.sub(r'\\s+', ' ', query)[:150]}")
            cursor = connection.execute(query)
            print_rows(cursor)
        connection.commit()
    finally:
        connection.close()


if __name__ == "__main__":
    main()
