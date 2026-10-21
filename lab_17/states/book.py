"""FSM-состояния (конечный автомат) для многошаговых диалогов."""

from aiogram.fsm.state import State, StatesGroup


class AddBook(StatesGroup):
    """Многошаговый сценарий добавления книги (минимум 4 состояния)."""

    title = State()        # Ввод названия
    author = State()       # Ввод автора
    year = State()         # Ввод года
    isbn = State()         # Ввод ISBN (можно пропустить)
    copies = State()       # Ввод количества экземпляров
    confirm = State()      # Подтверждение


class BorrowBook(StatesGroup):
    """Многошаговый сценарий выдачи книги читателю."""

    choose_book = State()  # Выбор книги из каталога
    confirm = State()      # Подтверждение выдачи
    return_choose = State()  # Выбор выдачи для возврата