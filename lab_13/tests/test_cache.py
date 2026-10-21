import pytest

from app.cache import BookCache
from app.service import LibraryService


def test_cache_aside_reads_database_once(service: LibraryService, monkeypatch):
    book = service.list_books(limit=1)[0]
    book_id = book["_id"]

    calls = []
    original = service.repository.get

    def counted(identifier):
        calls.append(identifier)
        return original(identifier)

    monkeypatch.setattr(service.repository, "get", counted)

    first = service.get_book(book_id)
    second = service.get_book(book_id)

    assert len(calls) == 1
    assert first["title"] == second["title"]
    assert service.cache.hit_rate()["hits"] >= 1


def test_update_invalidates_cache_and_returns_fresh_data(service: LibraryService, monkeypatch):
    book = service.list_books(limit=1)[0]
    book_id = book["_id"]

    service.get_book(book_id)
    service.update_book(book_id, {"year": 1999})

    assert service.cache.get_book(book_id) is None

    fresh = service.get_book(book_id)
    assert fresh["year"] == 1999
    assert service.cache.get_book(book_id)["year"] == 1999


def test_delete_invalidates_cache(service: LibraryService):
    created = service.add_book(
        {
            "title": "Удаляемая",
            "authors": ["Автор"],
            "publisher": {"name": "АСТ", "city": "Москва"},
            "genres": ["Рассказ"],
            "year": 2020,
            "copies_total": 1,
        }
    )
    service.get_book(created["_id"])
    assert service.cache.get_book(created["_id"]) is not None

    service.delete_book(created["_id"])
    assert service.cache.get_book(created["_id"]) is None


def test_hit_rate_counters(service: LibraryService):
    book = service.list_books(limit=1)[0]
    service.clear_cache()

    service.get_book(book["_id"])
    service.get_book(book["_id"])
    service.get_book(book["_id"])

    rate = service.cache.hit_rate()
    assert rate["misses"] == 1
    assert rate["hits"] == 2


def test_clear_cache_removes_keys(service: LibraryService):
    book = service.list_books(limit=1)[0]
    service.get_book(book["_id"])
    service.find_by_title("Дюна")

    removed = service.clear_cache()

    assert removed >= 2
    assert service.cache_info()["keys_total"] == 0


def test_benchmark_returns_rows(service: LibraryService):
    rows = service.benchmark((10, 50))

    assert [row["count"] for row in rows] == [10, 50]
    assert all(row["mongo_ms"] >= 0 and row["redis_ms"] >= 0 for row in rows)
