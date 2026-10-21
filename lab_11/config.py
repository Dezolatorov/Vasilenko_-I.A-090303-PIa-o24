"""Настройки приложения."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DB_PATH = Path(os.environ.get("LIBRARY_DB", BASE_DIR / "library.db"))

REDIS_HOST = os.environ.get("LIBRARY_REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.environ.get("LIBRARY_REDIS_PORT", "6379"))

CACHE_TTL = int(os.environ.get("LIBRARY_CACHE_TTL", "60"))
CACHE_PREFIX = "library"

API_HOST = os.environ.get("LIBRARY_API_HOST", "127.0.0.1")
API_PORT = int(os.environ.get("LIBRARY_API_PORT", "5000"))

CDN_BASE_URL = os.environ.get("LIBRARY_CDN_URL", "http://127.0.0.1:8081")
