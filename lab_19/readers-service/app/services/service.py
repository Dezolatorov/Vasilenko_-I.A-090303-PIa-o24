"""Сервисный слой readers-service: бизнес-логика работы с читателями."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.models import Reader
from app.schemas.schemas import ReaderCreate, ReaderUpdate

if TYPE_CHECKING:
    from app.repositories import ReaderRepository


class ReadersService:
    def __init__(self, repository: "ReaderRepository"):
        self._repository = repository

    def list_readers(self) -> list[Reader]:
        return self._repository.all()

    def get_reader(self, reader_id: str) -> Reader | None:
        return self._repository.get(reader_id)

    def create_reader(self, payload: ReaderCreate) -> Reader:
        if self._repository.find_by_email(payload.email) is not None:
            raise ValueError("читатель с таким e-mail уже существует")
        reader = Reader(full_name=payload.full_name, email=payload.email, phone=payload.phone)
        return self._repository.create(reader)

    def update_reader(self, reader_id: str, payload: ReaderUpdate) -> Reader | None:
        fields = payload.model_dump(exclude_none=True)
        if not fields:
            return None
        return self._repository.update(reader_id, fields)

    def delete_reader(self, reader_id: str) -> bool:
        return self._repository.delete(reader_id)

    def check_reader(self, reader_id: str) -> dict:
        """Полнота и активность - используется loans-service для проверки читателя."""
        reader = self._repository.get(reader_id)
        if reader is None:
            return {"exists": False, "active": False}
        return {"exists": True, "active": reader.active, "full_name": reader.full_name}