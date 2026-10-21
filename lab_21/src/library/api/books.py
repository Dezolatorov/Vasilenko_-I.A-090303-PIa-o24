"""Роутер книг: /books - каталог, CRUD, фильтрация, сортировка."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from ..auth import require_admin, require_user
from ..database import get_session
from ..models import Reader
from ..schemas import BookCreate, BookOut, BookUpdate
from ..services import BookService
from .deps import get_book_service

router = APIRouter()


@router.get(
    "",
    response_model=list[BookOut],
    summary="Каталог книг (поиск/фильтрация/сортировка)",
)
def list_books(
    title: str | None = Query(default=None),
    author_id: int | None = Query(default=None),
    year_from: int | None = Query(default=None, ge=1000, le=2100),
    available_only: bool = Query(default=False),
    sort_by: str = Query(default="title", pattern="^(title|year|id)$"),
    descending: bool = Query(default=False),
    service: BookService = Depends(get_book_service),
    _: Reader = Depends(require_user),
) -> list[BookOut]:
    books = service.search(
        title=title,
        author_id=author_id,
        year_from=year_from,
        available_only=available_only,
        sort_by=sort_by,
        descending=descending,
    )
    return [BookOut.model_validate(b) for b in books]


@router.post("", response_model=BookOut, status_code=201, summary="Добавить книгу (ADMIN)")
def create_book(
    data: BookCreate,
    service: BookService = Depends(get_book_service),
    _: Reader = Depends(require_admin),
) -> BookOut:
    return BookOut.model_validate(service.create(data))


@router.get("/{book_id}", response_model=BookOut, summary="Книга по id")
def get_book(
    book_id: int,
    service: BookService = Depends(get_book_service),
    _: Reader = Depends(require_user),
) -> BookOut:
    return BookOut.model_validate(service.get(book_id))


@router.put("/{book_id}", response_model=BookOut, summary="Обновить книгу (ADMIN)")
def update_book(
    book_id: int,
    data: BookUpdate,
    service: BookService = Depends(get_book_service),
    _: Reader = Depends(require_admin),
) -> BookOut:
    return BookOut.model_validate(service.update(book_id, data))


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить книгу (ADMIN)")
def delete_book(
    book_id: int,
    service: BookService = Depends(get_book_service),
    _: Reader = Depends(require_admin),
) -> Response:
    service.delete(book_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)