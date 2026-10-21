"""Конфигурация приложения.

Все секретные и параметрические значения читаются из переменных окружения.
Токен бота НЕ должен храниться в исходном коде.
"""
import os
from pathlib import Path


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


BASE_DIR = Path(__file__).resolve().parent

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

ADMIN_IDS: tuple[int, ...] = tuple(
    int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()
)

# Путь к файлу БД SQLite (для удобства тестирования переопределяется).
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "library.db"))

# Срок выдачи книги по умолчанию (дней).
LOAN_DAYS = _env_int("LOAN_DAYS", 14)

# Смещение от имени пользователя Telegram, подставляемое в повторные сеансы.
SKIP_UPDATES = os.getenv("SKIP_UPDATES", "1") == "1"