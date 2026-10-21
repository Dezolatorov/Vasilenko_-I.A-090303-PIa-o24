"""Подключение к SQLite и управление транзакциями."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "library.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"
SEED_PATH = BASE_DIR / "seed.sql"


class Database:
    """Фабрика соединений SQLite с поддержкой транзакций."""

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH) -> None:
        self.db_path = str(db_path)

    def connect(self) -> sqlite3.Connection:
        """Открыть соединение с включёнными внешними ключами.

        SQLite приводит регистр только для латиницы, поэтому для поиска
        по русским названиям регистрируется собственная функция py_lower().
        """
        connection = sqlite3.connect(self.db_path, timeout=10.0)
        connection.row_factory = sqlite3.Row
        connection.create_function(
            "py_lower",
            1,
            lambda value: value.lower() if isinstance(value, str) else value,
            deterministic=True,
        )
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        """Соединение на время одной операции: фиксация или откат."""
        connection = self.connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Явная транзакция: несколько операторов выполняются как одно целое.

        COMMIT — если блок завершился без исключения,
        ROLLBACK — при любом исключении внутри блока.
        """
        connection = self.connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def init_schema(self) -> None:
        """Создать таблицы и индексы из schema.sql."""
        script = SCHEMA_PATH.read_text(encoding="utf-8")
        with self.connection() as connection:
            connection.executescript(script)

    def seed(self) -> None:
        """Заполнить БД тестовыми данными из seed.sql."""
        script = SEED_PATH.read_text(encoding="utf-8")
        with self.connection() as connection:
            connection.executescript(script)

    def reset(self) -> None:
        """Пересоздать БД с нуля: схема + тестовые данные."""
        self.init_schema()
        self.seed()
