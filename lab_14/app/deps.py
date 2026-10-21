from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.cache import BookCache
from app.database import get_db
from app.repositories.book import BookRepository
from app.services.book import BookService

cache = BookCache()


def get_cache() -> BookCache:
    return cache


def get_service(
    db: Session = Depends(get_db),
    book_cache: BookCache = Depends(get_cache),
) -> BookService:
    return BookService(BookRepository(db), book_cache)
