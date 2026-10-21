"""Тесты Telegram-интерфейса: FSM-сценарий, обработчики, middleware.

Реальный Telegram API отсутствует, поэтому обработчики вызываются напрямую
с лёгкими mock-объектами Message/CallbackQuery и реальным FSMContext на
MemoryStorage. Всё работает офлайн.
"""
from datetime import date

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Chat, Message, User

from handlers import menu, registration, start
from middlewares.logging import LoggingMiddleware
from services import library_service as svc
from states.book import AddBook, BorrowBook


class DummyAnswer:
    """Собирает отправленные ботом сообщения/клавиатуры вместо сети."""

    def __init__(self):
        self.sent: list[tuple[str, object]] = []

    async def answer(self, text: str = "", reply_markup=None, **kwargs):
        self.sent.append((text, reply_markup))

    async def edit_text(self, text: str = "", reply_markup=None, **kwargs):
        self.sent.append(("EDIT:" + text, reply_markup))

    async def delete(self, **kwargs):
        self.sent.append(("DELETED", None))


def make_message(text: str, uid: int = 1) -> Message:
    return Message(
        message_id=1,
        date=date(2026, 1, 1),
        chat=Chat(id=uid, type="private"),
        from_user=User(id=uid, is_bot=False, first_name="Тест", last_name="", username="test"),
        text=text,
    )


def make_callback(data: str, uid: int = 1) -> CallbackQuery:
    return CallbackQuery(
        id=f"cq-{uid}",
        from_user=User(id=uid, is_bot=False, first_name="Тест", last_name="", username="test"),
        chat_instance="x",
        message=make_message("x", uid),
        data=data,
    )


async def _fsm(store: MemoryStorage, chat_id: int = 1) -> FSMContext:
    return FSMContext(storage=store, key=(chat_id, chat_id))


def patch_msg(msg: Message) -> DummyAnswer:
    """Заменяет сетевые методы Message на локальные заглушки (модель frozen)."""
    out = DummyAnswer()
    object.__setattr__(msg, "answer", out.answer)
    return out


def patch_cb(cb: CallbackQuery) -> DummyAnswer:
    """Заглушки для CallbackQuery и его Message."""
    out = DummyAnswer()
    object.__setattr__(cb, "answer", out.answer)
    if cb.message is not None:
        object.__setattr__(cb.message, "answer", out.answer)
        object.__setattr__(cb.message, "edit_text", out.edit_text)
        object.__setattr__(cb.message, "delete", out.delete)
    return out


async def _seed():
    await svc.add_book("Война и мир", "Лев Толстой", 1869, "9785699001596", 2)
    await svc.add_book("Анна Каренина", "Лев Толстой", 1877, "9785699039001", 1)


# ---------------------------------------------------------------------------
# Обработчики-команды
# ---------------------------------------------------------------------------

async def test_start_sends_menu():
    msg = make_message("/start")
    out = patch_msg(msg)
    await start.cmd_start(msg, await _fsm(MemoryStorage()))
    assert len(out.sent) == 1
    text, markup = out.sent[0]
    assert "Здравствуйте" in text
    assert markup is not None  # Reply Keyboard главного меню


async def test_cancel_without_state():
    msg = make_message("/cancel")
    out = patch_msg(msg)
    await start.cmd_cancel(msg, await _fsm(MemoryStorage()))
    assert "Нет активной операции" in out.sent[0][0]


# ---------------------------------------------------------------------------
# FSM-сценарий добавления книги (6 состояний)
# ---------------------------------------------------------------------------

async def test_add_book_fsm_flow():
    storage = MemoryStorage()
    state = await _fsm(storage)
    msg = make_message("новичок", uid=3)

    def set_text(value: str) -> None:
        object.__setattr__(msg, "text", value)

    set_text("/add_book")
    out = patch_msg(msg)
    await registration.add_book_start(msg, state)
    assert (await state.get_state()) == AddBook.title

    set_text("Мастер и Маргарита")
    out = patch_msg(msg)
    await registration.add_book_title(msg, state)
    assert (await state.get_state()) == AddBook.author

    set_text("Михаил Булгаков")
    out = patch_msg(msg)
    await registration.add_book_author(msg, state)
    assert (await state.get_state()) == AddBook.year

    # валидация неверного года
    set_text("не число")
    out = patch_msg(msg)
    await registration.add_book_year(msg, state)
    assert "Год" in out.sent[0][0]
    assert (await state.get_state()) == AddBook.year  # состояние не меняется

    set_text("1940")
    out = patch_msg(msg)
    await registration.add_book_year(msg, state)
    assert (await state.get_state()) == AddBook.isbn

    set_text("-")
    out = patch_msg(msg)
    await registration.add_book_isbn(msg, state)
    assert (await state.get_state()) == AddBook.copies

    set_text("3")
    out = patch_msg(msg)
    await registration.add_book_copies(msg, state)
    assert (await state.get_state()) == AddBook.confirm

    data = await state.get_data()
    assert data["_draft"].title == "Мастер и Маргарита"
    assert data["_draft"].author_name == "Михаил Булгаков"


async def test_add_book_fsm_confirm_creates():
    storage = MemoryStorage()
    state = await _fsm(storage)
    await state.set_state(AddBook.confirm)
    await state.update_data(
        _draft=svc.BookDraft(title="Тихий Дон", author_name="Михаил Шолохов",
                             year=1928, isbn=None, copies_total=2)
    )
    cb = make_callback("book:0", uid=5)
    out = patch_cb(cb)
    await registration.add_book_confirm(cb, state)
    assert (await state.get_state()) is None  # FSM завершён
    found = list(await svc.search_books("Тихий Дон"))
    assert len(found) == 1


# ---------------------------------------------------------------------------
# Предметная функциональность через обработчики
# ---------------------------------------------------------------------------

async def test_lend_via_fsm_confirm():
    await _seed()
    storage = MemoryStorage()
    state = await _fsm(storage)
    book = (await svc.search_books("Война и мир"))[0]
    await state.set_state(BorrowBook.confirm)
    await state.update_data(book_id=book.id)
    cb = make_callback(f"book:{book.id}", uid=11)
    out = patch_cb(cb)
    await registration.lend_confirm(cb, state)
    assert (await state.get_state()) is None
    reader = await svc.get_reader_by_telegram_id(11)
    assert reader is not None
    loans = list(await svc.reader_active_loans(reader.id))
    assert len(loans) == 1
    assert "Книга выдана" in out.sent[0][0]


async def test_search_handler_offline():
    await _seed()
    msg = make_message("Анна", uid=2)
    out = patch_msg(msg)
    await menu._do_search(msg, "Анна")
    assert "Анна Каренина" in out.sent[0][0]


async def test_mybooks_none():
    msg = make_message("/mybooks", uid=999)
    out = patch_msg(msg)
    await menu.cmd_mybooks(msg, await _fsm(MemoryStorage()))
    assert "пока нет" in out.sent[0][0]


async def test_return_callback():
    await _seed()
    book = (await svc.search_books("Анна Каренина"))[0]
    loan = await svc.lend_book(book.id, 42, "Читатель")
    cb = make_callback(f"loan:{loan.id}", uid=42)
    out = patch_cb(cb)
    await menu.cb_return(cb)
    assert any("возвращена" in t for t, _ in out.sent)


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

async def test_middleware_counts_and_logs():
    mw = LoggingMiddleware()

    async def handler(event, data):
        return "ok"

    msg = make_message("/start", uid=77)
    await mw(handler, msg, {})
    assert mw.message_counts[77] == 1
    await mw(handler, msg, {})
    assert mw.message_counts[77] == 2

    cb = make_callback("menu", uid=77)
    await mw(handler, cb, {})
    assert mw.message_counts[77] == 3


async def test_middleware_rethrows_on_error():
    mw = LoggingMiddleware()

    async def bad_handler(event, data):
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        await mw(bad_handler, make_message("x"), {})