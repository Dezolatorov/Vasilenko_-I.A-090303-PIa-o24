"""Общие фикстуры pytest: свежая временная БД SQLite для каждого теста.

Тесты изолированы: каждый тест работает с собственной временной базой,
поэтому не зависят от реального Telegram API и запускаются офлайн.
"""
from pathlib import Path

import pytest

from database import db


@pytest.fixture(autouse=True)
async def fresh_db(tmp_path: Path):
    """Пересоздаёт временную БД до и после каждого теста."""
    dbfile = tmp_path / "test.db"
    await db.init_db(str(dbfile))
    yield dbfile
    await db.close_db()