"""Печать структуры БД: таблицы, столбцы, ключи и индексы.

Запуск: python demo_schema.py
"""

import config
from db import Database


def main() -> None:
    database = Database(config.DB_PATH)
    with database.connection() as connection:
        tables = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()

        print("=" * 90)
        print(f"СТРУКТУРА БАЗЫ ДАННЫХ «БИБЛИОТЕКА» ({config.DB_PATH.name})")
        print("=" * 90)

        for table in tables:
            name = table["name"]
            print()
            print(f"ТАБЛИЦА {name}")
            columns = connection.execute(f"PRAGMA table_info({name})").fetchall()
            for column in columns:
                flags = []
                if column["pk"]:
                    flags.append("PRIMARY KEY")
                if column["notnull"]:
                    flags.append("NOT NULL")
                marker = f"  [{', '.join(flags)}]" if flags else ""
                print(f"    {column['name']:<18} {column['type']:<8}{marker}")

            keys = connection.execute(f"PRAGMA foreign_key_list({name})").fetchall()
            for key in keys:
                print(f"    FOREIGN KEY ({key['from']}) REFERENCES {key['table']}({key['to']})")

            count = connection.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
            print(f"    записей: {count}")

        print()
        print("=" * 90)
        print("ИНДЕКСЫ")
        print("=" * 90)
        indexes = connection.execute(
            "SELECT name, tbl_name, sql FROM sqlite_master"
            " WHERE type = 'index' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        for index in indexes:
            print(f"  {index['name']:<20} на таблице {index['tbl_name']}")
            print(f"      {index['sql']}")


if __name__ == "__main__":
    main()
