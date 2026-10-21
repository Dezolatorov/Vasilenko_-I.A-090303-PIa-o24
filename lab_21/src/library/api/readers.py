"""Роутер читателей: /readers (ADMIN и сам пользователь)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from ..auth import get_current_reader, require_admin, require_user
from ..database import get_session
from ..models import Reader
from ..schemas import ReaderOut, ReaderUpdate
from ..services import ReaderService
from .deps import get_reader_service

router = APIRouter()


@router.get("", response_model=list[ReaderOut], summary="Список всех читателей (ADMIN)")
def list_readers(
    service: ReaderService = Depends(get_reader_service),
    _: Reader = Depends(require_admin),
) -> list[ReaderOut]:
    return [ReaderOut.model_validate(r) for r in service.list_all()]


@router.get("/me", response_model=ReaderOut, summary="Текущий пользователь")
def get_me(
    current: Reader = Depends(get_current_reader),
) -> ReaderOut:
    return ReaderOut.model_validate(current)


@router.get("/{reader_id}", response_model=ReaderOut, summary="Читатель по id")
def get_reader(
    reader_id: int,
    service: ReaderService = Depends(get_reader_service),
    current: Reader = Depends(get_current_reader),
) -> ReaderOut:
    reader = service.get(reader_id)
    if current.role != "ADMIN" and current.id != reader_id:
        from ..exceptions import AuthorizationException

        raise AuthorizationException("Нет доступа к чужому профилю")
    return ReaderOut.model_validate(reader)


@router.put("/{reader_id}", response_model=ReaderOut, summary="Обновить читателя")
def update_reader(
    reader_id: int,
    data: ReaderUpdate,
    service: ReaderService = Depends(get_reader_service),
    current: Reader = Depends(get_current_reader),
) -> ReaderOut:
    reader = service.update(reader_id, data, current)
    return ReaderOut.model_validate(reader)


@router.delete("/{reader_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить читателя (ADMIN)")
def delete_reader(
    reader_id: int,
    service: ReaderService = Depends(get_reader_service),
    _: Reader = Depends(require_admin),
) -> Response:
    service.delete(reader_id, _)
    return Response(status_code=status.HTTP_204_NO_CONTENT)