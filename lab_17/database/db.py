"""Управление подключением к SQLite через aiosqlite.

aiogram является асинхронным фреймворком, поэтому доступ к БД выполняется
асинхронно (aiosqlite), чтобы не блокировать event loop блокирующим I/O.
"""
import sqlite3

import aiosqlite

_DB: aiosqlite.Connection | None = None


async def init_db(path: str) -> None:
    """Создаёт соединение и таблицы, если их ещё нет."""
    global _DB
    _DB = await aiosqlite.connect(path)
    _DB.row_factory = sqlite3.Row
    await _DB.execute("PRAGMA foreign_keys = ON")
    await _create_schema()
    await _DB.commit()


async def _create_schema() -> None:
    if _DB is None:
        raise RuntimeError("база данных не инициализирована")
    await _DB.executescript(
        """
        CREATE TABLE IF NOT EXISTS authors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS readers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL UNIQUE,
            full_name TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author_id INTEGER NOT NULL REFERENCES authors(id) ON DELETE RESTRICT,
            year INTEGER,
            isbn TEXT UNIQUE,
            copies_total INTEGER NOT NULL DEFAULT 1,
            copies_available INTEGER NOT NULL DEFAULT 1,
            CHECK (copies_available >= 0),
            CHECK (copies_available <= copies_total)
        );

        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE RESTRICT,
            reader_id INTEGER NOT NULL REFERENCES readers(id) ON DELETE RESTRICT,
            issued_at TEXT NOT NULL,
            due_date TEXT NOT NULL,
            returned_at TEXT
        );
        """
    )


async def get_db() -> aiosqlite.Connection:
    if _DB is None:
        raise RuntimeError("база данных не инициализирована, вызовите init_db()")
    return _DB


async def close_db() -> None:
    global _DB
    if _DB is not None:
        await _DB.close()
        _DB = None