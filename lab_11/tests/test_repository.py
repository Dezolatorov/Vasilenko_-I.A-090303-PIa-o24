"""Тесты слоя Repository: SQL-запросы, JOIN, связи N:M."""

import pytest


def test_get_all_returns_seeded_books(repositories):
    books = repositories["books"].get_all()
    assert len(books) == 12
    assert books[0].id == 1


def test_filter_by_genre_and_availability(repositories):
    books = repositories["books"].get_all({"genre": "роман", "available": True}, "title", "asc")
    assert books
    assert all(book.genre == "роман" and book.available_copies > 0 for book in books)


def test_filter_without_available_copies(repositories):
    books = repositories["books"].get_all({"available": False}, "title", "asc")
    assert [book.id for book in books] == [5]


def test_sort_by_price_desc(repositories):
    books = repositories["books"].get_all({}, "price", "desc")
    prices = [book.price for book in books]
    assert prices == sorted(prices, reverse=True)


def test_filter_by_author_name_and_price_range(repositories):
    books = repositories["books"].get_all({"author": "булгаков", "min_price": 500}, "price", "asc")
    assert [book.id for book in books] == [12, 1]
    assert all(book.price >= 500 for book in books)


def test_get_details_joins_author_and_tags(repositories):
    details = repositories["books"].get_details(1)
    assert details is not None
    assert details.author == "Булгаков М.А."
    assert "мистика" in details.tags
    assert details.available_copies == 1


def test_get_by_id_missing_returns_none(repositories):
    assert repositories["books"].get_by_id(999) is None


def test_create_update_delete_book(repositories):
    books = repositories["books"]
    created = books.create({
        "title": "Тестовая книга",
        "author_id": 2,
        "genre": "роман",
        "year": 2000,
        "price": 100.0,
        "total_copies": 2,
    })
    assert created.id == 13
    assert created.available_copies == 2

    created.title = "Тестовая книга (изм.)"
    books.update(created)
    assert books.get_by_id(13).title == "Тестовая книга (изм.)"

    assert books.delete(13) is True
    assert books.get_by_id(13) is None
    assert books.delete(13) is False


def test_tags_relation_many_to_many(repositories):
    books = repositories["books"]
    books.set_tags(3, ["классика", "эпопея"])
    assert books.get_tags(3) == ["классика", "эпопея"]

    books.set_tags(3, ["эпопея"])
    assert books.get_tags(3) == ["эпопея"]


def test_genre_stats_group_by(repositories):
    stats = repositories["books"].genre_stats()
    genres = {row["genre"]: row for row in stats}
    assert genres["роман"]["books_count"] == 6
    assert genres["роман"]["avg_price"] > 0


def test_author_stats_having(repositories):
    stats = repositories["books"].author_stats()
    authors = {row["author"]: row["books_count"] for row in stats}
    assert authors["Булгаков М.А."] == 3
    assert "Лем С." not in authors


def test_tag_stats_left_join(repositories):
    stats = repositories["books"].tag_stats()
    tags = {row["tag"]: row["books_count"] for row in stats}
    assert tags["классика"] == 6
    assert tags["эксперимент"] == 1


def test_foreign_key_violation_on_unknown_author(repositories):
    import sqlite3

    with pytest.raises(sqlite3.IntegrityError):
        repositories["books"].create({
            "title": "Книга без автора",
            "author_id": 999,
            "genre": "роман",
            "year": 2000,
            "price": 100.0,
            "total_copies": 1,
        })


def test_sql_injection_attempt_is_treated_as_text(repositories):
    books = repositories["books"].get_all({"author": "' OR '1'='1"}, "title", "asc")
    assert books == []
