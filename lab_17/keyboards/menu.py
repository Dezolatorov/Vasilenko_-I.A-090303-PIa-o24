"""Клавиатуры: Reply Keyboard (главное меню) и Inline Keyboard.

Callback data использует структурированный формат `действие:идентификатор`
(методичка, разделы 8–9), например:
  book:12  — просмотр/выбор книги с id 12
  lend:12  — начать выдачу книги с id 12
  loan:7   — вернуть выдачу с id 7
  cancel   — отмена FSM.
"""
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models import Book, Loan


def main_menu_kb() -> ReplyKeyboardMarkup:
    """Главное (Reply) меню — минимум 4 функциональных пункта (16.2)."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📚 Каталог"),
                KeyboardButton(text="🔍 Поиск"),
            ],
            [
                KeyboardButton(text="➕ Добавить книгу"),
                KeyboardButton(text="📖 Выдать книгу"),
            ],
            [
                KeyboardButton(text="↩️ Мои книги"),
                KeyboardButton(text="⏰ Просроченные"),
            ],
            [
                KeyboardButton(text="ℹ️ Помощь"),
            ],
        ],
        resize_keyboard=True,
    )


def books_kb(books: list[Book]) -> InlineKeyboardMarkup:
    """Inline-кнопки каталога: каждая книга передаёт свой id через callback data."""
    kb = InlineKeyboardBuilder()
    for b in books[:10]:
        label = f"{b.title} — {b.author_name}"
        kb.button(text=label[:55], callback_data=f"book:{b.id}")
    kb.button(text="⬅️ Назад в меню", callback_data="menu")
    kb.adjust(1)
    return kb.as_markup()


def lend_choose_kb(books: list[Book]) -> InlineKeyboardMarkup:
    """Выбор книги для выдачи (только те, что в наличии)."""
    kb = InlineKeyboardBuilder()
    for b in books:
        if b.copies_available <= 0:
            continue
        label = f"{b.title} — {b.author_name} (в наличии {b.copies_available})"
        kb.button(text=label[:55], callback_data=f"lend:{b.id}")
    kb.button(text="ОТМЕНА", callback_data="cancel")
    kb.adjust(1)
    return kb.as_markup()


def return_kb(loans: list[Loan]) -> InlineKeyboardMarkup:
    """Выбор активной выдачи для возврата."""
    kb = InlineKeyboardBuilder()
    for ln in loans:
        label = f"{ln.book_title} (до {ln.due_date.isoformat()})"
        kb.button(text=label[:55], callback_data=f"loan:{ln.id}")
    kb.button(text="ОТМЕНА", callback_data="cancel")
    kb.adjust(1)
    return kb.as_markup()


def book_detail_kb(book_id: int) -> InlineKeyboardMarkup:
    """Действия с конкретной книгой (CRUD, выдача, поиск)."""
    kb = InlineKeyboardBuilder()
    kb.button(text="📖 Выдать", callback_data=f"lend:{book_id}")
    kb.button(text="✏️ Изменить", callback_data=f"edit:{book_id}")
    kb.button(text="🗑 Удалить", callback_data=f"del:{book_id}")
    kb.button(text="⬅️ Каталог", callback_data="catalog")
    kb.adjust(2)
    return kb.as_markup()


def confirm_kb(book_id: int) -> InlineKeyboardMarkup:
    """Подтверждение действий с книгой (изменение/удаление)."""
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Да", callback_data=f"book:{book_id}")
    kb.button(text="❌ Нет", callback_data="cancel")
    kb.adjust(2)
    return kb.as_markup()