import pytest
from bson import ObjectId

from app.errors import NotFoundError, ValidationError
from app.mongodb import MongoDatabase
from app.repository import InvalidBookId, MongoBookRepository
from app.service import LibraryService


def test_connection_and_indexes(database: MongoDatabase):
    assert database.ping() is True
    assert database.mode == "mongomock"
    indexes = database.create_indexes()
    assert {"idx_title", "idx_genres_year", "idx_publisher_city"} <= set(indexes)


def test_insert_document_with_nested_and_array(service: LibraryService):
    created = service.add_book(
        {
            "title": "Тестовая книга",
            "authors": ["Тестовый автор", "Соавтор"],
            "publisher": {"name": "Питер", "city": "Санкт-Петербург", "year": 2024},
            "genres": ["Роман", "Тест"],
            "year": 2024,
            "copies_total": 3,
        }
    )

    assert created["title"] == "Тестовая книга"
    assert created["publisher"]["city"] == "Санкт-Петербург"
    assert created["genres"] == ["Роман", "Тест"]
    assert created["copies"] == {"total": 3, "available": 3}
    assert ObjectId.is_valid(created["_id"])


def test_get_missing_document(service: LibraryService):
    with pytest.raises(NotFoundError):
        service.get_book(str(ObjectId()))


def test_invalid_identifier(service: LibraryService):
    with pytest.raises(InvalidBookId):
        service.get_book("не-идентификатор")


def test_update_document(service: LibraryService):
    book = service.list_books(limit=1)[0]
    updated = service.update_book(book["_id"], {"year": 2000, "status": "archived"})

    assert updated["year"] == 2000
    assert updated["status"] == "archived"
    assert service.get_book(book["_id"])["year"] == 2000


def test_delete_document(service: LibraryService):
    book = service.add_book(
        {
            "title": "Временная",
            "authors": ["Автор"],
            "publisher": {"name": "АСТ", "city": "Москва"},
            "genres": ["Рассказ"],
            "year": 2020,
            "copies_total": 1,
        }
    )
    service.delete_book(book["_id"])

    with pytest.raises(NotFoundError):
        service.get_book(book["_id"])


def test_filter_by_genre(service: LibraryService):
    result = service.search(genre="Фантастика")
    assert result["count"] >= 3
    assert all("Фантастика" in item["genres"] for item in result["items"])


def test_nested_field_query(service: LibraryService):
    rows = service.by_publisher_city("Санкт-Петербург")
    assert rows
    assert all(row["publisher"]["city"] == "Санкт-Петербург" for row in rows)


def test_array_element_query(service: LibraryService):
    rows = service.by_reader("Петрова А.С.")
    assert len(rows) == 1
    assert rows[0]["title"] == "Идиот"


def test_multiple_conditions(service: LibraryService):
    result = service.search(query="Толстой", min_year=1870, available_only=True)
    titles = [item["title"] for item in result["items"]]
    assert "Анна Каренина" in titles
    assert all(item["year"] >= 1870 for item in result["items"])
    assert all(item["copies"]["available"] > 0 for item in result["items"])


def test_aggregation_by_status(service: LibraryService):
    stats = service.statistics()
    statuses = {row["_id"]: row["count"] for row in stats["by_status"]}
    assert statuses.get("available", 0) >= 15
    assert statuses.get("loaned", 0) >= 1


def test_aggregation_by_genre_and_authors(service: LibraryService):
    stats = service.statistics()
    genres = {row["_id"]: row["books"] for row in stats["by_genre"]}
    assert genres["Классика"] >= 5

    authors = [row["_id"] for row in stats["top_authors"]]
    assert "Достоевский Ф.М." in authors


def test_borrow_and_return_updates_document(service: LibraryService):
    book = service.add_book(
        {
            "title": "Книга для выдачи",
            "authors": ["Автор"],
            "publisher": {"name": "АСТ", "city": "Москва"},
            "genres": ["Роман"],
            "year": 2021,
            "copies_total": 1,
        }
    )
    borrowed = service.borrow_book(book["_id"], "Иванов И.И.", days=10)
    assert borrowed["copies"]["available"] == 0
    assert borrowed["readers"][0]["reader"] == "Иванов И.И."
    assert borrowed["readers"][0]["returned"] is False

    returned = service.return_book(book["_id"], "Иванов И.И.")
    assert returned["copies"]["available"] == 1
    assert returned["readers"][0]["returned"] is True


def test_borrow_without_copies_raises(service: LibraryService):
    book = service.add_book(
        {
            "title": "Нет экземпляров",
            "authors": ["Автор"],
            "publisher": {"name": "АСТ", "city": "Москва"},
            "genres": ["Роман"],
            "year": 2021,
            "copies_total": 1,
            "copies_available": 0,
        }
    )
    with pytest.raises(ValidationError):
        service.borrow_book(book["_id"], "Иванов И.И.")
