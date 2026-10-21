from __future__ import annotations

from functools import partial
from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status
from starlette.concurrency import run_in_threadpool

from app.deps import get_service
from app.schemas import BookCreate, BookListResponse, BookResponse, BookStatistics, BookUpdate
from app.services.book import BookService

router = APIRouter(prefix="/books", tags=["books"])


@router.get(
    "",
    response_model=BookListResponse,
    summary="Список книг",
    description="Возвращает список книг с фильтрацией, сортировкой и пагинацией.",
)
async def list_books(
    genre: Optional[str] = Query(None, description="Фильтр по жанру"),
    author: Optional[str] = Query(None, description="Фильтр по автору (частичное совпадение)"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Минимальный рейтинг"),
    sort: str = Query("title", pattern="^(title|author|year|rating)$", description="Поле сортировки"),
    order: str = Query("asc", pattern="^(asc|desc)$", description="Направление сортировки"),
    limit: int = Query(20, ge=1, le=100, description="Размер страницы"),
    offset: int = Query(0, ge=0, description="Смещение"),
    service: BookService = Depends(get_service),
):
    items, total = await run_in_threadpool(
        partial(
            service.list_books,
            genre=genre,
            author=author,
            min_rating=min_rating,
            sort=sort,
            order=order,
            limit=limit,
            offset=offset,
        )
    )
    return {"total": total, "limit": limit, "offset": offset, "items": items}


@router.get(
    "/search",
    response_model=list[BookResponse],
    summary="Поиск книг",
    description="Поиск по названию, автору, издательству и жанру.",
)
def search_books(
    q: str = Query(..., min_length=1, description="Строка поиска"),
    limit: int = Query(20, ge=1, le=100),
    service: BookService = Depends(get_service),
):
    return service.search_books(q, limit=limit)


@router.get(
    "/statistics",
    response_model=BookStatistics,
    summary="Статистика фонда",
    description="Количество книг, средний и максимальный рейтинг, суммарное число экземпляров, распределение по жанрам.",
)
def statistics(service: BookService = Depends(get_service)):
    return service.statistics()


@router.get(
    "/{book_id}",
    response_model=BookResponse,
    summary="Книга по идентификатору",
    responses={404: {"description": "Книга не найдена"}},
)
def get_book(book_id: int, service: BookService = Depends(get_service)):
    return service.get_book(book_id)


@router.post(
    "",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создание книги",
    responses={409: {"description": "Книга с таким ISBN уже существует"}},
)
def create_book(payload: BookCreate, service: BookService = Depends(get_service)):
    return service.create_book(payload.model_dump())


@router.put(
    "/{book_id}",
    response_model=BookResponse,
    summary="Полное обновление книги",
    responses={404: {"description": "Книга не найдена"}, 409: {"description": "Конфликт ISBN"}},
)
def replace_book(book_id: int, payload: BookCreate, service: BookService = Depends(get_service)):
    return service.replace_book(book_id, payload.model_dump())


@router.patch(
    "/{book_id}",
    response_model=BookResponse,
    summary="Частичное обновление книги",
    responses={404: {"description": "Книга не найдена"}},
)
def patch_book(book_id: int, payload: BookUpdate, service: BookService = Depends(get_service)):
    return service.patch_book(book_id, payload.model_dump(exclude_unset=True))


@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Удаление книги",
    responses={404: {"description": "Книга не найдена"}},
)
def delete_book(book_id: int, service: BookService = Depends(get_service)) -> Response:
    service.delete_book(book_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
