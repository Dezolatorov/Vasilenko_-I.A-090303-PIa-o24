"""Тесты бизнес-логики сервисного слоя (методичка п. 21).

Проверяются CRUD, поиск, валидация, выдача/возврат, просрочка — всё
офлайн на временной SQLite, без реального Telegram API.
"""
from datetime import date, timedelta

import pytest

from database import repository as repo
from services import library_service as svc


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

async def test_create_book():
    book = await svc.add_book("Война и мир", "Лев Толстой", 1869, "9785699001596", 3)
    assert book.id is not None
    assert book.title == "Война и мир"
    assert book.author_name == "Лев Толстой"
    assert book.copies_total == 3
    assert book.copies_available == 3


async def test_get_book():
    added = await svc.add_book("Евгений Онегин", "Александр Пушкин", 1833, "9785170881164", 2)
    found = await svc.get_book(added.id)
    assert found is not None
    assert found.id == added.id
    assert found.title == "Евгений Онегин"


async def test_update_book():
    added = await svc.add_book("Старое название", "Автор", 2000, "9785170881164", 1)
    updated = await svc.edit_book(added.id, "Новое название", "Новый автор", 2020, None, 2, 2)
    assert updated is not None
    assert updated.title == "Новое название"
    assert updated.author_name == "Новый автор"
    assert updated.copies_total == 2


async def test_delete_book():
    added = await svc.add_book("Удаляемая", "Автор", 2001, "9785170881164", 1)
    assert await svc.remove_book(added.id) is True
    assert await svc.get_book(added.id) is None


# ---------------------------------------------------------------------------
# Поиск
# ---------------------------------------------------------------------------

async def test_search_by_title():
    await svc.add_book("Анна Каренина", "Лев Толстой", 1877, "9785699039001", 1)
    await svc.add_book("Преступление и наказание", "Фёдор Достоевский", 1866, "9785699078147", 1)
    found = list(await svc.search_books("Анна"))
    assert len(found) == 1
    assert found[0].title == "Анна Каренина"


async def test_search_by_author():
    await svc.add_book("Отцы и дети", "Иван Тургенев", 1862, "9785170548019", 1)
    found = list(await svc.search_books("Тургенев"))
    assert len(found) >= 1
    assert found[0].author_name == "Иван Тургенев"


async def test_search_empty_result():
    found = list(await svc.search_books("фывапролд"))
    assert found == []


# ---------------------------------------------------------------------------
# Валидация
# ---------------------------------------------------------------------------

async def test_validate_bad_year():
    with pytest.raises(svc.LibraryError):
        svc.normalize_year("две тысячи")


async def test_validate_year_range():
    with pytest.raises(svc.LibraryError):
        svc.normalize_year("1200")


async def test_validate_copies():
    with pytest.raises(svc.LibraryError):
        svc.normalize_copies("0")


async def test_validate_isbn():
    assert svc.normalize_isbn("9785699001596") == "9785699001596"
    with pytest.raises(svc.LibraryError):
        svc.normalize_isbn("978569900159")


async def test_validate_draft_available_le_total():
    draft = svc.BookDraft(title="Книга", author_name="А", copies_total=1, copies_available=5)
    with pytest.raises(svc.LibraryError):
        svc.validate_book_draft(draft)


# ---------------------------------------------------------------------------
# Выдача и возврат
# ---------------------------------------------------------------------------

async def test_lend_book():
    book = await svc.add_book("Выдача", "Автор", 2000, "9785170881164", 2)
    loan = await svc.lend_book(book.id, 100500, "Иван Петров")
    assert loan.id is not None
    assert loan.due_date == loan.issued_at + timedelta(days=svc.LOAN_DAYS)
    # экземпляр списан
    after = await svc.get_book(book.id)
    assert after.copies_available == 1


async def test_lend_no_copies():
    book = await svc.add_book("Один экземпляр", "Автор", 2000, "9785170881164", 1)
    await svc.lend_book(book.id, 1, "Читатель А")
    with pytest.raises(svc.LibraryError):
        await svc.lend_book(book.id, 2, "Читатель Б")


async def test_lend_same_reader_twice():
    book = await svc.add_book("Двойная выдача", "Автор", 2000, "9785170881164", 2)
    await svc.lend_book(book.id, 42, "Читатель")
    with pytest.raises(svc.LibraryError):
        await svc.lend_book(book.id, 42, "Читатель")


async def test_return_book():
    book = await svc.add_book("Возврат", "Автор", 2000, "9785170881164", 1)
    loan = await svc.lend_book(book.id, 7, "Читатель")
    assert await svc.return_book(loan.id) is True
    after = await svc.get_book(book.id)
    assert after.copies_available == 1


async def test_overdue_loans():
    book = await svc.add_book("Просрочка", "Автор", 2000, "9785170881164", 1)
    loan = await svc.lend_book(book.id, 9, "Читатель", today=date(2026, 1, 1))
    overdue = list(await svc.overdue_loans(today=date(2026, 3, 1)))
    assert len(overdue) == 1
    assert loan.id in {ln.id for ln in overdue}


# ---------------------------------------------------------------------------
# Репозиторий: прямая работа со связанными сущностями
# ---------------------------------------------------------------------------

async def test_reader_creation_and_registration():
    reader = await svc.ensure_reader(555, "Пётр Смирнов")
    assert reader.id is not None
    again = await svc.ensure_reader(555, "Пётр Смирнов")
    assert again.id == reader.id  # не создаётся повторно


async def test_count_objects():
    await svc.add_book("Книга 1", "Автор 1", 2000, "9785170881164", 1)
    cnt = await svc.count_objects()
    assert cnt["books"] >= 1
    assert cnt["readers"] >= 0