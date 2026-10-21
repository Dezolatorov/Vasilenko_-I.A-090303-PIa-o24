"""Тесты бизнес-логики: BookService, cache-aside, валидация."""

import pytest

from exceptions import ConflictError, NotFoundError, ValidationError


def test_get_book_raises_not_found(services):
    with pytest.raises(NotFoundError):
        services["books"].get_book(999)


def test_get_book_cache_aside_miss_then_hit(services, fake_cache):
    book = services["books"].get_book(1)
    assert book.title == "Мастер и Маргарита"
    assert fake_cache.misses == 1
    assert "book:1" in fake_cache.store

    again = services["books"].get_book(1)
    assert again.title == book.title
    assert fake_cache.hits == 1
    assert fake_cache.misses == 1


def test_patch_book_invalidates_cache(services, fake_cache):
    services["books"].get_book(2)
    assert "book:2" in fake_cache.store

    updated = services["books"].patch_book(2, {"price": 555.0})
    assert updated.price == 555.0
    assert "book:2" not in fake_cache.store

    fresh = services["books"].get_book(2)
    assert fresh.price == 555.0


def test_create_book_rejects_unknown_author(services):
    with pytest.raises(ValidationError):
        services["books"].create_book({
            "title": "Книга",
            "author_id": 99,
            "genre": "роман",
            "year": 2000,
            "price": 100.0,
            "total_copies": 1,
        })


def test_create_book_validation_of_price(services):
    with pytest.raises(ValidationError):
        services["books"].create_book({
            "title": "Книга",
            "author_id": 1,
            "genre": "роман",
            "year": 2000,
            "price": -5,
            "total_copies": 1,
        })


def test_create_book_unknown_field(services):
    with pytest.raises(ValidationError):
        services["books"].create_book({
            "title": "Книга",
            "author_id": 1,
            "genre": "роман",
            "year": 2000,
            "price": 100.0,
            "total_copies": 1,
            "hacker": True,
        })


def test_delete_book_missing(services):
    with pytest.raises(NotFoundError):
        services["books"].delete_book(999)


def test_search_records_query_in_cache(services, fake_cache):
    books = services["books"].search("война")
    assert [book.title for book in books] == ["Война и мир"]
    assert fake_cache.store["search:count:война"] == "1"

    services["books"].search("война")
    assert fake_cache.store["search:count:война"] == "2"


def test_search_history_sorted_by_count(services):
    for query in ("мастер", "мастер", "война"):
        services["books"].search(query)
    history = services["books"].search_history()
    assert history[0]["query"] == "мастер"
    assert history[0]["count"] == 2


def test_search_without_results(services):
    with pytest.raises(NotFoundError):
        services["books"].search("нет такой книги")


def test_create_reader_with_duplicate_email(services):
    with pytest.raises(ConflictError):
        services["readers"].create_reader({
            "full_name": "Дубль",
            "email": "ivanov@example.com",
        })


def test_reader_loans_returns_history(services):
    loans = services["readers"].reader_loans(1)
    assert len(loans) == 2
    assert all(loan.reader_id == 1 for loan in loans)


def test_stats_include_group_by(services):
    stats = services["books"].stats()
    assert stats["books_total"] == 12
    assert any(row["genre"] == "роман" for row in stats["by_genre"])
