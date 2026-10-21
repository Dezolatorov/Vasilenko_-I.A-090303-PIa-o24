"""Роутер авторов: /authors."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from ..auth import require_admin, require_user
from ..database import get_session
from ..models import Reader
from ..schemas import AuthorCreate, AuthorOut, AuthorUpdate
from ..services import AuthorService
from .deps import get_author_service

router = APIRouter()


@router.get("", response_model=list[AuthorOut], summary="Список/поиск авторов")
def list_authors(
    name: str | None = Query(default=None, description="Подстрока имени"),
    service: AuthorService = Depends(get_author_service),
    _: Reader = Depends(require_user),
) -> list[AuthorOut]:
    return [AuthorOut.model_validate(a) for a in service.search(name)]


@router.post("", response_model=AuthorOut, status_code=201, summary="Создать автора (ADMIN)")
def create_author(
    data: AuthorCreate,
    service: AuthorService = Depends(get_author_service),
    _: Reader = Depends(require_admin),
) -> AuthorOut:
    return AuthorOut.model_validate(service.create(data))


@router.get("/{author_id}", response_model=AuthorOut, summary="Автор по id")
def get_author(
    author_id: int,
    service: AuthorService = Depends(get_author_service),
    _: Reader = Depends(require_user),
) -> AuthorOut:
    return AuthorOut.model_validate(service.get(author_id))


@router.put("/{author_id}", response_model=AuthorOut, summary="Обновить автора (ADMIN)")
def update_author(
    author_id: int,
    data: AuthorUpdate,
    service: AuthorService = Depends(get_author_service),
    _: Reader = Depends(require_admin),
) -> AuthorOut:
    return AuthorOut.model_validate(service.update(author_id, data))


@router.delete("/{author_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить автора (ADMIN)")
def delete_author(
    author_id: int,
    service: AuthorService = Depends(get_author_service),
    _: Reader = Depends(require_admin),
) -> Response:
    service.delete(author_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)