"""Многошаговые FSM-сценарии (методичка 16.4, 15).

Добавление книги: название → автор → год → ISBN → количество → подтверждение.
Выдача книги: выбор книги → подтверждение (читатель регистрируется по
пользователю Telegram).
"""
from datetime import date

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import LOAN_DAYS
from database.models import Book, BookDraft
from keyboards.menu import confirm_kb, lend_choose_kb, main_menu_kb
from services import library_service as svc
from services import formatting
from states.book import AddBook, BorrowBook

router = Router(name="registration")

HELP_HINT = "\n\nИли нажмите /cancel, чтобы отменить операцию."


# ======================================================================
# Добавление книги (FSM, 6 состояний)
# ======================================================================

@router.message(Command("add_book"))
@router.message(F.text.lower().in_({"добавить книгу", "➕ добавить книгу", "add book"}))
async def add_book_start(message: Message, state: FSMContext) -> None:
    await state.set_state(AddBook.title)
    await message.answer("Добавление новой книги.\nПришлите название книги:" + HELP_HINT)


@router.message(AddBook.title)
async def add_book_title(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.strip():
        await message.answer("Название не может быть пустым. Пришлите название книги:")
        return
    await state.update_data(title=message.text.strip())
    await state.set_state(AddBook.author)
    await message.answer("Укажите автора книги (фамилия и имя):" + HELP_HINT)


@router.message(AddBook.author)
async def add_book_author(message: Message, state: FSMContext) -> None:
    if message.text and message.text.strip():
        await state.update_data(author=message.text.strip())
    elif message.from_user and message.from_user.full_name:
        # допустимый резерв — полное имя пользователя
        await state.update_data(author=message.from_user.full_name)
    else:
        await message.answer("Не удалось определить автора. Укажите автора текстом:")
        return
    await state.set_state(AddBook.year)
    await message.answer("Укажите год издания (число от 1450 до 2100):" + HELP_HINT)


@router.message(AddBook.year)
async def add_book_year(message: Message, state: FSMContext) -> None:
    try:
        year = svc.normalize_year(message.text or "")
    except svc.LibraryError as exc:
        await message.answer(str(exc))
        return
    await state.update_data(year=year)
    await state.set_state(AddBook.isbn)
    await message.answer(
        "Укажите ISBN (10 или 13 цифр) или отправьте «-» чтобы пропустить:" + HELP_HINT
    )


@router.message(AddBook.isbn)
async def add_book_isbn(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    if raw == "-":
        isbn = None
    else:
        try:
            isbn = svc.normalize_isbn(raw)
        except svc.LibraryError as exc:
            await message.answer(str(exc) + " Отправьте «-», чтобы пропустить:")
            return
    await state.update_data(isbn=isbn)
    await state.set_state(AddBook.copies)
    await message.answer("Укажите количество экземпляров (число от 1 до 100):" + HELP_HINT)


@router.message(AddBook.copies)
async def add_book_copies(message: Message, state: FSMContext) -> None:
    try:
        copies = svc.normalize_copies(message.text or "")
    except svc.LibraryError as exc:
        await message.answer(str(exc))
        return
    await state.update_data(copies=copies)
    data = await state.get_data()
    draft = BookDraft(
        title=data.get("title", ""),
        author_name=data.get("author", ""),
        year=data.get("year"),
        isbn=data.get("isbn"),
        copies_total=data.get("copies", 1),
    )
    await state.update_data(_draft=draft)
    text = (
        "Проверьте данные книги:\n\n"
        f"Название: {draft.title}\n"
        f"Автор: {draft.author_name}\n"
        f"Год: {draft.year}\n"
        f"ISBN: {draft.isbn or '—'}\n"
        f"Экземпляров: {draft.copies_total}\n\n"
        "Всё верно?"
    )
    await state.set_state(AddBook.confirm)
    await message.answer(text, reply_markup=confirm_kb(0))


@router.callback_query(AddBook.confirm, F.data.in_({"book:0", "menu", "cancel"}))
async def add_book_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    draft = data.get("_draft")
    if callback.data == "book:0" and isinstance(draft, BookDraft):
        try:
            svc.validate_book_draft(draft)
            book = await svc.add_book(
                draft.title, draft.author_name, draft.year, draft.isbn, draft.copies_total
            )
        except svc.LibraryError as exc:
            await callback.answer(str(exc), show_alert=True)
            if callback.message:
                await callback.message.answer("Попробуйте ещё раз или нажмите /cancel.",
                                              reply_markup=main_menu_kb())
            await state.clear()
            return
        if callback.message:
            await callback.message.answer(f"Книга добавлена!\n\n{formatting.format_book(book)}",
                                          reply_markup=main_menu_kb())
    else:
        if callback.message:
            await callback.message.answer("Добавление книги отменено.",
                                          reply_markup=main_menu_kb())
    await state.clear()
    await callback.answer()


# ======================================================================
# Выдача книги (FSM, 2 шага + выбор)
# ======================================================================

@router.message(Command("lend"))
@router.message(F.text.lower().in_({"выдать книгу", "📖 выдать книгу", "выдать"}))
async def lend_start(message: Message, state: FSMContext) -> None:
    books = list(await svc.list_books())
    available = [b for b in books if b.copies_available > 0]
    if not available:
        await message.answer("Сейчас нет ни одной книги, доступной для выдачи.",
                             reply_markup=main_menu_kb())
        return
    await state.set_state(BorrowBook.choose_book)
    await message.answer("Выберите книгу для выдачи:", reply_markup=lend_choose_kb(books))


@router.callback_query(BorrowBook.choose_book, F.data.startswith("lend:"))
async def lend_choose(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        book_id = int(callback.data.split(":", 1)[1])
    except ValueError:
        await callback.answer("Неверный формат данных", show_alert=True)
        return
    book = await svc.get_book(book_id)
    if book is None:
        await callback.answer("Книга не найдена", show_alert=True)
        await state.clear()
        return
    await state.update_data(book_id=book.id)
    await state.set_state(BorrowBook.confirm)
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            f"Выдаём:\n\n{formatting.format_book(book)}\n\n"
            f"Срок выдачи — {LOAN_DAYS} дней. Подтверждаете?",
            reply_markup=confirm_kb(book.id),
        )


@router.callback_query(BorrowBook.confirm, F.data.startswith("book:"))
async def lend_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    book_id = data.get("book_id")
    reader_name = callback.from_user.full_name if callback.from_user else "Читатель"
    if book_id is None:
        await callback.answer("Данные устарели, начните заново", show_alert=True)
        await state.clear()
        return
    try:
        loan = await svc.lend_book(book_id, callback.from_user.id, reader_name)
    except svc.LibraryError as exc:
        await callback.answer(str(exc), show_alert=True)
        if callback.message:
            await callback.message.answer("Выдача не оформлена.", reply_markup=main_menu_kb())
        await state.clear()
        return
    if callback.message:
        await callback.message.answer(
            f"✅ Книга выдана!\n\n{formatting.loan_text(loan)}",
            reply_markup=main_menu_kb(),
        )
    await callback.answer()
    await state.clear()


@router.callback_query(BorrowBook.confirm, F.data == "cancel")
async def lend_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    if callback.message:
        await callback.message.answer("Выдача отменена.", reply_markup=main_menu_kb())


# /borrow via command with optional book id
@router.message(Command("borrow"))
async def borrow_command(message: Message, command: CommandObject, state: FSMContext) -> None:
    args = (command.args or "").split()
    if not args or not args[0].isdigit():
        await message.answer("Использование: /borrow <id_книги>")
        return
    book_id = int(args[0])
    book = await svc.get_book(book_id)
    if book is None:
        await message.answer("Книга не найдена.")
        return
    await state.update_data(book_id=book_id)
    await state.set_state(BorrowBook.confirm)
    await message.answer(
        f"Выдаём:\n\n{formatting.format_book(book)}\n\nСрок {LOAN_DAYS} дней. Подтверждаете?",
        reply_markup=confirm_kb(book_id),
    )