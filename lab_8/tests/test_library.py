import pytest

from repositories.memory_repository import InMemoryRepository
from services.library_service import LibraryService
from models.entities import Reader
from models.enums import ItemType, ItemStatus, ReaderCategory
from factories.library_factory import LibraryItemFactory


@pytest.fixture
def service():
    repo = InMemoryRepository()
    return LibraryService(repo)


def test_factory_creates_printed_book():
    item = LibraryItemFactory.create(
        ItemType.PRINTED_BOOK, id=1, title="A", author="B", year=2000
    )
    assert item.item_type == ItemType.PRINTED_BOOK
    assert item.status == ItemStatus.AVAILABLE


def test_repository_add_and_get(service):
    service.add_item(ItemType.EBOOK, id=10, title="X", author="Y", year=2020)
    item = service.repository.get(10)
    assert item is not None
    assert item.title == "X"


def test_repository_rejects_duplicate(service):
    service.add_item(ItemType.EBOOK, id=1, title="X", author="Y", year=2020)
    with pytest.raises(ValueError):
        service.add_item(ItemType.EBOOK, id=1, title="Z", author="W", year=2021)


def test_strategy_for_teacher_gives_60_days(service):
    service.add_item(ItemType.PRINTED_BOOK, id=1, title="A", author="B", year=2000)
    reader = Reader(1, "Проф. Иванов", ReaderCategory.TEACHER)
    result = service.issue(1, reader)
    assert "60" in result


def test_strategy_for_preferential_gives_30_days(service):
    service.add_item(ItemType.PRINTED_BOOK, id=1, title="A", author="B", year=2000)
    reader = Reader(1, "Льготник", ReaderCategory.PREFERENTIAL)
    result = service.issue(1, reader)
    assert "30" in result


def test_strategy_for_student_gives_14_days(service):
    service.add_item(ItemType.PRINTED_BOOK, id=1, title="A", author="B", year=2000)
    reader = Reader(1, "Студент", ReaderCategory.STUDENT)
    result = service.issue(1, reader)
    assert "14" in result


def test_issue_changes_status(service):
    service.add_item(ItemType.PRINTED_BOOK, id=1, title="A", author="B", year=2000)
    reader = Reader(1, "Студент", ReaderCategory.STUDENT)
    service.issue(1, reader)
    assert service.repository.get(1).status == ItemStatus.ISSUED


def test_cannot_issue_reserved_item(service):
    service.add_item(ItemType.PRINTED_BOOK, id=1, title="A", author="B", year=2000)
    service.reserve(1)
    reader = Reader(1, "Студент", ReaderCategory.STUDENT)
    with pytest.raises(ValueError):
        service.issue(1, reader)


def test_return_restores_available(service):
    service.add_item(ItemType.PRINTED_BOOK, id=1, title="A", author="B", year=2000)
    reader = Reader(1, "Студент", ReaderCategory.STUDENT)
    service.issue(1, reader)
    service.return_item(1)
    assert service.repository.get(1).status == ItemStatus.AVAILABLE


def test_find_by_author(service):
    service.add_item(ItemType.EBOOK, id=1, title="X", author="Толстой", year=2000)
    service.add_item(ItemType.EBOOK, id=2, title="Y", author="Пушкин", year=2000)
    found = service.find_by_author("толст")
    assert len(found) == 1 and found[0].id == 1


def test_statistics(service):
    service.add_item(ItemType.PRINTED_BOOK, id=1, title="A", author="B", year=2000)
    service.add_item(ItemType.PRINTED_BOOK, id=2, title="C", author="D", year=2000)
    reader = Reader(1, "Студент", ReaderCategory.STUDENT)
    service.issue(1, reader)

    s = service.statistics()
    assert s["total"] == 2
    assert s["issued"] == 1
    assert s["available"] == 1