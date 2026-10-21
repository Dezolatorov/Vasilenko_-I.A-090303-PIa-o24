"""Обработчики главного меню и предметной функциональности (методичка 16.2).

Каталог, поиск, мои книги, просроченные, возврат, а также Inline-кнопки и
Callback Query с передачей идентификатора объекта (методичка 8–9).
"""
from aiogram import F, Router
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database.models import Book
from keyboards.menu import (
    book_detail_kb,
    books_kb,
    main_menu_kb,
    return_kb,
)
from services import library_service as svc
from services import formatting

router = Router(name="menu")


# ======================================================================
# Каталог и карточка книги
# ======================================================================

@router.message(Command("catalog"), StateFilter(None))
@router.message(F.text.lower().in_({"каталог", "📚 каталог", "книги", "список"}), StateFilter(None))
async def cmd_catalog(message: Message, state: FSMContext) -> None:
    await state.clear()
    books = list(await svc.list_books())
    if not books:
        await message.answer("В каталоге нет книг.", reply_markup=main_menu_kb())
        return
    text = formatting.book_catalog_text(books)
    await message.answer(
        text,
        reply_markup=books_kb(books) if len(books) > 1 else None,
    )


@router.callback_query(F.data == "catalog")
async def cb_catalog(callback: CallbackQuery) -> None:
    books = list(await svc.list_books())
    text = formatting.book_catalog_text(books)
    await callback.answer()
    if callback.message:
        await callback.message.edit_text(text, reply_markup=books_kb(books))


@router.callback_query(F.data.startswith("book:"))
async def cb_book_detail(callback: CallbackQuery) -> None:
    try:
        book_id = int(callback.data.split(":", 1)[1])
    except ValueError:
        await callback.answer("Неверный формат", show_alert=True)
        return
    book = await svc.get_book(book_id)
    if book is None:
        await callback.answer("Книга не найдена", show_alert=True)
        return
    await callback.answer()
    if callback.message:
        await callback.message.edit_text(
            formatting.format_book(book),
            reply_markup=book_detail_kb(book.id),
        )


# ======================================================================
# Поиск (методичка 16.8)
# ======================================================================

@router.message(Command("search"), StateFilter(None))
async def cmd_search(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Пришлите текст для поиска: часть названия книги или имя автора "
        "(можно разделить автора и название через «|», например «Толстой|война»)."
    )


@router.message(Command("find"))
async def cmd_find(message: Message, command: CommandObject, state: FSMContext) -> None:
    await state.clear()
    if not (command.args or "").strip():
        await message.answer("Использование: /find <текст>")
        return
    await _do_search(message, command.args)


@router.message(F.text.lower().in_({"поиск", "🔍 поиск", "найти", "find"}), StateFilter(None))
async def menu_search(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Пришлите текст для поиска: часть названия книги или имя автора "
        "(можно разделить через «|»)."
    )


async def _do_search(message: Message, query: str) -> None:
    query = (query or "").strip()
    if not query:
        await message.answer("Текст для поиска не может быть пустым.")
        return
    parts = [p.strip() for p in query.split("|")]
    title = parts[0]
    author = parts[1] if len(parts) > 1 else ""
    books = list(await svc.search_books(title, author))
    await message.answer(formatting.search_results_text(query, books), reply_markup=main_menu_kb())


# ======================================================================
# Мои книги и просроченные (функции варианта 2)
# ======================================================================

@router.message(Command("mybooks"), StateFilter(None))
@router.message(F.text.lower().in_({"мои книги", "↩️ мои книги", "мои"}), StateFilter(None))
async def cmd_mybooks(message: Message, state: FSMContext) -> None:
    await state.clear()
    reader = await svc.get_reader_by_telegram_id(message.from_user.id)
    if reader is None:
        await message.answer("У вас пока нет выданных книг.", reply_markup=main_menu_kb())
        return
    loans = list(await svc.reader_active_loans(reader.id))
    await message.answer(formatting.my_loans_text(loans), reply_markup=main_menu_kb())


@router.message(Command("overdue"), StateFilter(None))
@router.message(F.text.lower().in_({"просроченные", "⏰ просроченные", "просрочка"}), StateFilter(None))
async def cmd_overdue(message: Message, state: FSMContext) -> None:
    await state.clear()
    loans = list(await svc.overdue_loans())
    await message.answer(formatting.overdue_text(loans), reply_markup=main_menu_kb())


# ======================================================================
# Возврат книги
# ======================================================================

@router.message(Command("return"), StateFilter(None))
@router.message(F.text.lower().in_({"вернуть", "возврат", "↩️ вернуть"}), StateFilter(None))
async def cmd_return(message: Message, state: FSMContext) -> None:
    await state.clear()
    reader = await svc.get_reader_by_telegram_id(message.from_user.id)
    if reader is None:
        await message.answer("Нет активных выдач для возврата.", reply_markup=main_menu_kb())
        return
    loans = list(await svc.reader_active_loans(reader.id))
    if not loans:
        await message.answer("У вас нет активных выдач.", reply_markup=main_menu_kb())
        return
    await message.answer("Выберите книгу для возврата:", reply_markup=return_kb(loans))


@router.callback_query(F.data.startswith("loan:"))
async def cb_return(callback: CallbackQuery) -> None:
    try:
        loan_id = int(callback.data.split(":", 1)[1])
    except ValueError:
        await callback.answer("Неверный формат", show_alert=True)
        return
    ok = await svc.return_book(loan_id)
    await callback.answer()
    if callback.message:
        msg = "✅ Книга возвращена." if ok else "Не удалось вернуть книгу (выдача не найдена или уже возвращена)."
        await callback.message.edit_text(msg, reply_markup=main_menu_kb())


# ======================================================================
# Изменение и удаление книги (CRUD; методичка 16.7)
# ======================================================================

@router.callback_query(F.data.startswith("del:"))
async def cb_delete(callback: CallbackQuery) -> None:
    try:
        book_id = int(callback.data.split(":", 1)[1])
    except ValueError:
        await callback.answer("Неверный формат", show_alert=True)
        return
    book = await svc.get_book(book_id)
    if book is None:
        await callback.answer("Книга не найдена", show_alert=True)
        return
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🗑 Удалить", callback_data=f"confirm_del:{book_id}"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"),
            ]
        ]
    )
    await callback.answer()
    if callback.message:
        await callback.message.edit_text(
            f"Точно удалить книгу?\n\n{formatting.format_book(book)}",
            reply_markup=kb,
        )


@router.callback_query(F.data.startswith("confirm_del:"))
async def cb_confirm_delete(callback: CallbackQuery) -> None:
    try:
        book_id = int(callback.data.split(":", 1)[1])
    except ValueError:
        await callback.answer("Неверный формат", show_alert=True)
        return
    ok = await svc.remove_book(book_id)
    await callback.answer()
    if callback.message:
        msg = "🗑 Книга удалена." if ok else "Не удалось удалить книгу."
        await callback.message.edit_text(msg, reply_markup=main_menu_kb())


@router.callback_query(F.data.startswith("edit:"))
async def cb_edit(callback: CallbackQuery) -> None:
    try:
        book_id = int(callback.data.split(":", 1)[1])
    except ValueError:
        await callback.answer("Неверный формат", show_alert=True)
        return
    book = await svc.get_book(book_id)
    if book is None:
        await callback.answer("Книга не найдена", show_alert=True)
        return
    await callback.answer("Изменение доступно через команду /edit_book")
    if callback.message:
        await callback.message.answer(
            "Изменение книги выполняется командой\n/edit_book <id>|<название>|<автор> "
            "<год>|<количество>\n\nПример:\n/edit_book {id}|Война и мир|Толстой|1869|5".format(id=book.id),
            reply_markup=main_menu_kb(),
        )


@router.message(Command("edit_book"))
async def cmd_edit_book(message: Message, command: CommandObject, state: FSMContext) -> None:
    await state.clear()
    parts = (command.args or "").split("|")
    if len(parts) < 5:
        await message.answer(
            "Использование: /edit_book <id>|<название>|<автор>|<год>|<экземпляров>"
        )
        return
    try:
        book_id = int(parts[0].strip())
        title = parts[1].strip()
        author = parts[2].strip()
        year = svc.normalize_year(parts[3]) if parts[3].strip() else None
        copies_total = svc.normalize_copies(parts[4])
    except ValueError as exc:
        await message.answer(f"Некорректные аргументы: {exc}")
        return
    except svc.LibraryError as exc:
        await message.answer(str(exc))
        return
    book = await svc.get_book(book_id)
    if book is None:
        await message.answer("Книга не найдена.")
        return
    edited = await svc.edit_book(
        book_id, title, author, year, None, copies_total, min(book.copies_available, copies_total)
    )
    if edited is None:
        await message.answer("Не удалось изменить книгу.")
        return
    await message.answer(f"Книга изменена!\n\n{formatting.format_book(edited)}",
                         reply_markup=main_menu_kb())


# ======================================================================
# Кнопка «Назад в меню» (callback "cancel" / "menu")
# ======================================================================

@router.callback_query(F.data.in_({"menu", "cancel"}))
async def cb_back(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.answer("Вы в главном меню:", reply_markup=main_menu_kb())
        await callback.message.delete()
    else:
        await callback.bot.send_message(
            callback.from_user.id,
            "Вы в главном меню:",
            reply_markup=main_menu_kb(),
        )


# Регистрируется последним как «catch-all» для произвольных текстовых сообщений.
@router.message(F.text, StateFilter(None))
async def search_text_filter(message: Message, state: FSMContext) -> None:
    """Обработчик-заглушка для прочих текстовых сообщений вне состояний FSM."""
    await message.answer(
        "Я не понял команду. Используйте /help или кнопки меню, либо отправьте "
        "текст для поиска книги.",
        reply_markup=main_menu_kb(),
    )