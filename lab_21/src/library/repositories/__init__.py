"""Слой репозиториев: инкапсуляция запросов к БД (SQLAlchemy).

HTTP-обработчики и сервисный слой не выполняют SQL напрямую.
"""
from .base import BaseRepository
from .readers import ReaderRepository
from .authors import AuthorRepository
from .books import BookRepository
from .loans import LoanRepository

__all__ = [
    "BaseRepository",
    "ReaderRepository",
    "AuthorRepository",
    "BookRepository",
    "LoanRepository",
]