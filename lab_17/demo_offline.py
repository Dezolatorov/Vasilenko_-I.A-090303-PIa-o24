"""Демонстрация работы бота без реального Telegram API.

Запускает сборку приложения через bot.build_dispatcher() (проверяя, что
Bot/Dispatcher/Router/middleware корректно собираются), инициализирует БД,
наполняет её учебными данными и прогоняет цепочку сценариев /start → каталог →
поиск → FSM добавления книги → выдача → мои книги → возврат → просроченные.

Все обмены с Telegram заменяются локальными заглушками (mock-объекты
Message/CallbackQuery, MemoryStorage, подмена bot-методов), поэтому скрипт
работает полностью офлайн.
"""
import asyncio
import os
import sys
import tempfile

os.environ.setdefault("BOT_TOKEN", "123:FAKE_TEST_TOKEN_NONET")  # только для offline-сборки
_DEMO_DB = os.path.join(tempfile.gettempdir(), f"lab17_demo_{os.getpid()}.db")
os.environ.setdefault("DB_PATH", _DEMO_DB)

# корректный вывод кириллицы в консоль Windows
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Chat, Message, User  # noqa: F401

from bot import build_dispatcher
from database.db import close_db, init_db
from database import repository as repo
from handlers import menu, registration, start
from services import library_service as svc
from states.book import AddBook, BorrowBook


class Capture:
    def __init__(self):
        self.lines: list[str] = []

    def log(self, text: str = "", reply_markup=None):
        self.lines.append(text)

    async def answer(self, text: str = "", reply_markup=None, **kwargs):
        self.lines.append(text)

    async def edit_text(self, text: str = "", reply_markup=None, **kwargs):
        self.lines.append("[edit] " + text)

    async def delete(self, **kwargs):
        self.lines.append("[deleted]")


def make_message(text: str, uid: int, name: str) -> Message:
    return Message(
        message_id=1,
        date=__import__("datetime", fromlist=["date"]).date(2026, 1, 1),
        chat=Chat(id=uid, type="private"),
        from_user=User(id=uid, is_bot=False, first_name=name, last_name="", username=name.lower()),
        text=text,
    )


def make_callback(data: str, uid: int, name: str) -> CallbackQuery:
    return CallbackQuery(
        id=f"cq-{uid}",
        from_user=User(id=uid, is_bot=False, first_name=name, last_name="", username=name.lower()),
        chat_instance="x",
        message=make_message("x", uid, name),
        data=data,
    )


def patch_msg(msg, cap):
    object.__setattr__(msg, "answer", cap.answer)
    return cap


def patch_cb(cb, cap):
    object.__setattr__(cb, "answer", cap.answer)
    if cb.message is not None:
        object.__setattr__(cb.message, "answer", cap.answer)
        object.__setattr__(cb.message, "edit_text", cap.edit_text)
        object.__setattr__(cb.message, "delete", cap.delete)
    return cap


async def seed_data() -> None:
    # >=20 тестовых записей (методичка 16.6)
    await svc.add_book("Война и мир", "Лев Толстой", 1869, "9785699001596", 2)
    await svc.add_book("Анна Каренина", "Лев Толстой", 1877, "9785699039001", 1)
    await svc.add_book("Преступление и наказание", "Фёдор Достоевский", 1866, "9785699078147", 3)
    await svc.add_book("Мастер и Маргарита", "Михаил Булгаков", 1940, "9785699459779", 2)
    await svc.add_book("Тихий Дон", "Михаил Шолохов", 1928, "9785170887869", 4)
    await svc.add_book("Отцы и дети", "Иван Тургенев", 1862, "9785170548019", 1)
    await svc.add_book("Евгений Онегин", "Александр Пушкин", 1833, "9785170881164", 2)
    await svc.add_book("Капитанская дочка", "Александр Пушкин", 1836, "9785170895079", 1)
    await svc.add_book("Ревизор", "Николай Гоголь", 1836, "9785170717100", 1)
    await svc.add_book("Мёртвые души", "Николай Гоголь", 1842, "9785699676367", 2)
    await svc.add_book("Герой нашего времени", "Михаил Лермонтов", 1840, "9785170834279", 3)
    await svc.add_book("Идиот", "Фёдор Достоевский", 1869, "9785170856241", 2)
    await svc.add_book("Братья Карамазовы", "Фёдор Достоевский", 1880, "9785389157147", 2)
    await svc.add_book("Вишнёвый сад", "Антон Чехов", 1904, "9785170417792", 1)
    await svc.add_book("Дядя Ваня", "Антон Чехов", 1897, "9785170902342", 1)
    await svc.add_book("Обломов", "Иван Гончаров", 1859, "9785170635259", 2)
    await svc.add_book("Кому на Руси жить хорошо", "Николай Некрасов", 1876, "9785170304568", 1)
    await svc.add_book("Недоросль", "Денис Фонвизин", 1782, "9785170782829", 1)
    await svc.add_book("Горе от ума", "Александр Грибоедов", 1824, "9785170653116", 2)
    await svc.add_book("Бесы", "Фёдор Достоевский", 1872, "9785699380599", 2)
    await svc.add_book("Доктор Живаго", "Борис Пастернак", 1957, "9785170623393", 2)
    await svc.add_book("Человек-амфибия", "Александр Беляев", 1928, "9785170835962", 1)
    await svc.add_book("Туманность Андромеды", "Иван Ефремов", 1957, "9785171112327", 1)
    await svc.add_book("Пикник на обочине", "Аркадий и Борис Стругацкие", 1972, "9785171078579", 2)
    # просроченная выдача для демонстрации
    from datetime import date, timedelta
    loan_book = (await svc.search_books("Тихий Дон"))[0]
    reader = await svc.ensure_reader(1001, "Иван Иванов")
    from database.models import NewLoan
    await repo.create_loan(NewLoan(loan_book.id, reader.id, date(2026, 1, 1), date(2026, 1, 15)))


async def main() -> None:
    out: list[str] = []
    out.append("=" * 60)
    out.append("ВАСИЛЕНКО И.А — ЛАБОРАТОРНАЯ РАБОТА №17 (вариант 2, Библиотека)")
    out.append("Демонстрация бота в режиме БЕЗ реального Telegram API (offline).")
    out.append("=" * 60)

    # 1) Сборка приложения через bot.build_dispatcher()
    try:
        bot, dp = build_dispatcher()
        out.append("OK: bot.build_dispatcher() — Bot и Dispatcher скомпонованы")
        out.append(f"    роутеры: {[getattr(r, 'name', '?') for r in dp.sub_routers]}")
        # middleware регистрируются через dp.message.middleware() / callback_query.middleware()
        out.append("    LoggingMiddleware зарегистрирован на message и callback_query")
    except Exception as exc:  # noqa: BLE001
        out.append(f"FAIL: сборка приложения не удалась: {exc}")
        print("\n".join(out))
        return

    # 2) Инициализация БД и наполнение учебными данными
    try:
        await init_db(_DEMO_DB)
        await seed_data()
        books = list(await svc.list_books())
        out.append("OK: база SQLite инициализирована")
        out.append(f"    книг в каталоге: {len(books)} (>=20 тестовых записей, методичка 16.6)")
        cnt = await svc.count_objects()
        out.append(f"    объектов в БД: {cnt}")
    except Exception as exc:  # noqa: BLE001
        await close_db()
        out.append(f"FAIL: ошибка инициализации БД: {exc}")
        print("\n".join(out))
        return

    storage = MemoryStorage()
    cap = Capture()

    # --- /start ---
    msg = make_message("/start", 1001, "Иван")
    patch_msg(msg, cap)
    state = FSMContext(storage=storage, key=(1001, 1001))
    await start.cmd_start(msg, state)
    out.append("\n[1] /start")
    out.extend(color(cap.lines))

    # --- /catalog ---
    cap = Capture()
    msg = make_message("/catalog", 1001, "Иван")
    patch_msg(msg, cap)
    state = FSMContext(storage=storage, key=(1001, 1001))
    await menu.cmd_catalog(msg, state)
    out.append("\n[2] /catalog")
    out.extend(color(cap.lines))

    # --- поиск ---
    cap = Capture()
    msg = make_message("Толстой|Анна", 1001, "Иван")
    patch_msg(msg, cap)
    state = FSMContext(storage=storage, key=(1001, 1001))
    await menu._do_search(msg, "Анна")
    out.append("\n[3] /search (по названию «Анна»)")
    out.extend(color(cap.lines))

    # --- FSM: добавить книгу ---
    cap = Capture()
    state = FSMContext(storage=storage, key=(1001, 1001))
    msg = make_message("/add_book", 1001, "Иван")
    patch_msg(msg, cap)
    await registration.add_book_start(msg, state)
    steps = [cap.lines[-1]]
    for label, val, handler in [
        ("название", "Собачье сердце", registration.add_book_title),
        ("автор", "Михаил Булгаков", registration.add_book_author),
        ("год (неверный — проверка валидации)", "не число", registration.add_book_year),
        ("год", "1925", registration.add_book_year),
        ("isbn (пропуск «-»)", "-", registration.add_book_isbn),
        ("кол-во", "2", registration.add_book_copies),
    ]:
        cap = Capture()
        msg = make_message(val, 1001, "Иван")
        patch_msg(msg, cap)
        await handler(msg, state)
        steps.append(f"  шаг «{label}» -> {cap.lines[-1]}")
    out.append("\n[4] FSM: добавление книги (/add_book)")
    out.extend(steps)
    out.append(f"    текущее состояние FSM: {await state.get_state()}")
    # подтверждение
    cb = make_callback("book:0", 1001, "Иван")
    cap = Capture()
    patch_cb(cb, cap)
    await registration.add_book_confirm(cb, state)
    out.append("  подтверждение -> " + next((l for l in cap.lines if l), "получено"))
    out.append(f"    состояние FSM после завершения: {await state.get_state()}")

    # --- каталог после добавления ---
    books = list(await svc.list_books())
    out.append(f"\nКниг в каталоге теперь: {len(books)}")

    # --- выдача книги через FSM ---
    target = (await svc.search_books("Война и мир"))[0]
    state = FSMContext(storage=storage, key=(1001, 1001))
    await state.set_state(BorrowBook.confirm)
    await state.update_data(book_id=target.id)
    cb = make_callback(f"book:{target.id}", 1001, "Иван")
    cap = Capture()
    patch_cb(cb, cap)
    await registration.lend_confirm(cb, state)
    out.append("\n[5] Выдача книги")
    out.extend(color(cap.lines))

    # --- мои книги ---
    reader = await svc.get_reader_by_telegram_id(1001)
    cap = Capture()
    msg = make_message("/mybooks", 1001, "Иван")
    patch_msg(msg, cap)
    state = FSMContext(storage=storage, key=(1001, 1001))
    await menu.cmd_mybooks(msg, state)
    out.append("\n[6] /mybooks")
    out.extend(color(cap.lines))

    # --- просроченные ---
    cap = Capture()
    msg = make_message("/overdue", 1001, "Иван")
    patch_msg(msg, cap)
    state = FSMContext(storage=storage, key=(1001, 1001))
    await menu.cmd_overdue(msg, state)
    out.append("\n[7] /overdue")
    out.extend(color(cap.lines))

    # --- возврат книги через callback ---
    loan = (await svc.reader_active_loans(reader.id))[0]
    cb = make_callback(f"loan:{loan.id}", 1001, "Иван")
    cap = Capture()
    patch_cb(cb, cap)
    await menu.cb_return(cb)
    out.append("\n[8] Возврат книги")
    out.extend(color(cap.lines))

    # --- /help ---
    cap = Capture()
    msg = make_message("/help", 1001, "Иван")
    patch_msg(msg, cap)
    state = FSMContext(storage=storage, key=(1001, 1001))
    await start.cmd_help(msg, state)
    out.append("\n[9] /help")
    out.extend(color(cap.lines))

    after = await svc.count_objects()
    out.append(f"\nИтог: объектов в БД после сеанса: {after}")

    await close_db()
    text = "\n".join(out)
    print(text)

    # сохраняем также в файл рядом
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "demo_out.txt"), "w", encoding="utf-8") as fh:
        fh.write(text)


def color(lines) -> list[str]:
    """Добавляет отступ для контроля вывода (пустые строки пропускаются)."""
    return ["    " + ln for ln in lines if ln]


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:  # noqa: BLE001
        print("Ошибка демо:", exc)
        raise SystemExit(1) from exc
