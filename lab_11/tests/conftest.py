"""Общие фикстуры тестов: временная БД, тестовый кэш и приложение."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import Database  # noqa: E402


class FakeCache:
    """Мини-реализация кэша для тестов: тот же интерфейс, что у RedisCache."""

    def __init__(self, ttl: int = 60) -> None:
        self.ttl = ttl
        self.store: dict[str, str] = {}
        self.hits = 0
        self.misses = 0

    def ping(self) -> bool:
        return True

    def get(self, name: str) -> str | None:
        return self.store.get(name)

    def set(self, name: str, value: str, ttl: int | None = None) -> None:
        self.store[name] = value

    def delete(self, *names: str) -> int:
        removed = 0
        for name in names:
            removed += 1 if self.store.pop(name, None) is not None else 0
        return removed

    def expire(self, name: str, ttl: int) -> bool:
        return name in self.store

    def ttl_of(self, name: str) -> int:
        return self.ttl if name in self.store else -2

    def incr(self, name: str) -> int:
        value = int(self.store.get(name, "0")) + 1
        self.store[name] = str(value)
        return value

    def keys(self, pattern: str = "*") -> list[str]:
        prefix = pattern.rstrip("*")
        return sorted(name for name in self.store if name.startswith(prefix))

    def stats(self) -> dict:
        total = self.hits + self.misses
        return {"backend": "fake", "hits": self.hits, "misses": self.misses,
                "hit_ratio": round(self.hits / total, 3) if total else 0.0, "keys": len(self.store)}

    def get_product_json(self, name: str) -> str | None:
        value = self.store.get(name)
        if value is None:
            self.misses += 1
        else:
            self.hits += 1
        return value

    def record_search(self, query: str, ttl: int = 3600) -> int:
        return self.incr(f"search:count:{query.strip().lower()}")

    def search_history(self, limit: int = 5) -> list[dict]:
        items = [
            {"query": name.split("search:count:", 1)[-1], "count": int(value), "ttl": self.ttl}
            for name, value in self.store.items()
            if name.startswith("search:count:")
        ]
        items.sort(key=lambda item: (-item["count"], item["query"]))
        return items[:limit]


@pytest.fixture()
def database(tmp_path):
    db = Database(tmp_path / "test_library.db")
    db.reset()
    return db


@pytest.fixture()
def fake_cache():
    return FakeCache()


@pytest.fixture()
def repositories(database):
    from repository import BookRepository, LoanRepository, ReaderRepository

    return {
        "books": BookRepository(database),
        "readers": ReaderRepository(database),
        "loans": LoanRepository(database),
    }


@pytest.fixture()
def services(database, repositories, fake_cache):
    from service import BookService, LoanService, ReaderService

    return {
        "books": BookService(repositories["books"], fake_cache),
        "readers": ReaderService(repositories["readers"], repositories["loans"]),
        "loans": LoanService(
            database,
            repositories["books"],
            repositories["readers"],
            repositories["loans"],
            fake_cache,
        ),
    }


@pytest.fixture()
def api(database, fake_cache):
    from app import create_app

    app = create_app(database=database, cache=fake_cache)
    app.config.update(TESTING=True)
    return app.test_client()
