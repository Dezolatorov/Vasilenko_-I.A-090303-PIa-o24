"""Собственный middleware (методичка 16.9).

LoggingMiddleware журналирует входящие события: до обработки — запись
в лог с id пользователя и текстом/командой, после — время обработки.
Также ведётся счётчик сообщений по каждому пользователю.
"""
import logging
import time
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class LoggingMiddleware(BaseMiddleware):
    """Пишет в лог каждое входящее событие и замеряет время обработки."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger("bot.middleware")
        self.message_counts: dict[int, int] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        started = time.monotonic()
        uid: int | None = None
        label = ""
        if hasattr(event, "from_user") and event.from_user is not None:
            uid = event.from_user.id
        if hasattr(event, "text") and event.text:
            label = event.text
        elif hasattr(event, "data") and event.data:
            label = f"callback:{event.data}"

        if uid is not None:
            self.message_counts[uid] = self.message_counts.get(uid, 0) + 1

        try:
            result = await handler(event, data)
        except Exception:
            self._logger.exception("Ошибка при обработке события %r", label)
            raise
        elapsed = (time.monotonic() - started) * 1000.0
        self._logger.info("uid=%s msg='%s' ok %.1f ms", uid, label, elapsed)
        return result