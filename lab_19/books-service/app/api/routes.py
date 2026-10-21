"""HTTP-слой (эндпоинты) books-service: REST API книг и доступности."""

from __future__ import annotations

import logging
import os
import time

from fastapi import APIRouter, HTTPException, status

from app.models import Book
from app.repositories import BookRepository
from app.schemas.schemas import BookCreate, BookOut, BookUpdate
from app.services import BooksService
from shared.storage import make_storage

logger = logging.getLogger("books-service")

router = APIRouter()

_svc = None


def init_service(storage_source: str) -> None:
    global _svc
    repo = BookRepository(make_storage(storage_source))
    _svc = BooksService(repo)


def _get_svc() -> BooksService:
    if _svc is None:
        init_service(
            os.environ.get("DATABASE_URL", os.environ.get("BOOKS_DB", "./data/books.json"))
        )
    return _svc


def _out(book: Book) -> BookOut:
    return BookOut(**book.to_dict())


def _log(method: str, path: str, start_ns: int, status_code: int = 200) -> None:
    logger.info("%s %s status=%d duration=%.1fms", method, path, status_code, (time.perf_counter_ns() - start_ns) / 1e6)


@router.get("/health")
def health():
    return {"status": "healthy", "service": "books-service"}


@router.get("/books", response_model=list[BookOut])
def list_books():
    result = [_out(b) for b in _get_svc().list_books()]
    return result


@router.get("/books/check/{book_id}")
def check_availability(book_id: str):
    """Доступность книги - вызывается loans-service (проверка перед выдачей)."""
    return _get_svc().check_availability(book_id)


@router.post("/books/{book_id}/decrement", status_code=status.HTTP_200_OK)
def decrement_stock(book_id: str):
    """Резервирование/списание экземпляра при выдаче (внутренний вызов loans)."""
    ok = _get_svc().decrement_stock(book_id)
    if not ok:
        book = _get_svc().get_book(book_id)
        if book is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="книга не найдена")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="нет доступных экземпляров")
    return {"status": "decremented"}


@router.post("/books/{book_id}/increment", status_code=status.HTTP_200_OK)
def increment_stock(book_id: str):
    ok = _get_svc().increment_stock(book_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="книга не найдена")
    return {"status": "incremented"}


@router.get("/books/{book_id}", response_model=BookOut)
def get_book(book_id: str):
    book = _get_svc().get_book(book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="книга не найдена")
    return _out(book)


@router.post("/books", response_model=BookOut, status_code=status.HTTP_201_CREATED)
def create_book(payload: BookCreate):
    book = _get_svc().create_book(payload)
    return _out(book)


@router.put("/books/{book_id}", response_model=BookOut)
def update_book(book_id: str, payload: BookUpdate):
    book = _get_svc().update_book(book_id, payload)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="книга не найдена")
    return _out(book)


@router.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: str):
    if not _get_svc().delete_book(book_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="книга не найдена")
