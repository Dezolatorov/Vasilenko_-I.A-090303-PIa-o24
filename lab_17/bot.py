"""Точка входа: сборка приложения (bot.py).

Создаёт Bot и Dispatcher, подключает роутеры, регистрирует middleware,
инициализирует базу данных и запускает polling. Логика предметной области
находится в services, доступ к данным — в database/repository.
"""
import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, Router

from config import BOT_TOKEN, DB_PATH, SKIP_UPDATES
from database.db import close_db, init_db
from database.seed import seed_if_empty
from handlers import menu, registration, start
from middlewares.logging import LoggingMiddleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("bot")


def build_dispatcher() -> tuple[Bot, Dispatcher]:
    """Создаёт Bot и Dispatcher с подключёнными роутерами и middleware."""
    if not BOT_TOKEN:
        raise RuntimeError("Переменная окружения BOT_TOKEN не задана.")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Порядок подключения важен: FSM-обработчики регистрируются раньше
    # общих, чтобы фильтры состояния обрабатывались первыми.
    main_router = Router(name="main")
    main_router.include_router(start.router)
    main_router.include_router(registration.router)
    main_router.include_router(menu.router)
    dp.include_router(main_router)

    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())

    return bot, dp


async def main() -> None:
    """Инициализация БД и запуск polling."""
    await init_db(DB_PATH)
    seeded = await seed_if_empty()
    if seeded:
        logger.info("Добавлены демонстрационные данные: %s книг", seeded)

    bot, dp = build_dispatcher()
    try:
        await dp.start_polling(bot, skip_updates=SKIP_UPDATES)
    finally:
        await bot.session.close()
        await close_db()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as exc:
        logger.error("%s", exc)
        raise SystemExit(1) from exc