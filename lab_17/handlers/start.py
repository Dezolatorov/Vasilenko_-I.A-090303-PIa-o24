"""Обработчики базовых команд: /start, /help, /cancel (методичка 16.1)."""
from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from keyboards.menu import main_menu_kb

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Здравствуйте! Это бот электронной библиотеки.\n\n"
        "Здесь можно посмотреть каталог книг, найти нужную, взять книгу "
        "на руки и вернуть её. Выберите действие в меню ниже.",
        reply_markup=main_menu_kb(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "📚 Команды бота:\n"
        "/start — начать работу и показать меню\n"
        "/help — эта справка\n"
        "/cancel — отменить текущую операцию\n"
        "/catalog — список книг в каталоге\n"
        "/search — поиск книги по названию или автору\n\n"
        "Также доступны кнопки меню:\n"
        "• 📚 Каталог — список всех книг\n"
        "• 🔍 Поиск — поиск по названию/автору\n"
        "• ➕ Добавить книгу — создать новую запись\n"
        "• 📖 Выдать книгу — оформить выдачу\n"
        "• ↩️ Мои книги — список выданных вам книг\n"
        "• ⏰ Просроченные — список просроченных выдач",
    )


@router.message(Command("cancel"))
@router.message(F.text.lower().in_({"отмена"}))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    if current is None:
        await message.answer("Нет активной операции для отмены.")
        return
    await state.clear()
    await message.answer("Операция отменена. Вы в главном меню:", reply_markup=main_menu_kb())