"""Репозиторий читателей - прямой доступ к собственному хранилищу (Database per Service)."""

from __future__ import annotations

from app.models import Reader
from shared.storage import JsonStorage


class ReaderRepository:
    def __init__(self, storage: JsonStorage):
        self._storage = storage

    def all(self) -> list[Reader]:
        return [Reader.from_dict(d) for d in self._storage.all()]

    def get(self, reader_id: str) -> Reader | None:
        data = self._storage.get(reader_id)
        return Reader.from_dict(data) if data else None

    def find_by_email(self, email: str) -> Reader | None:
        for data in self._storage.all():
            if data.get("email") == email:
                return Reader.from_dict(data)
        return None

    def create(self, reader: Reader) -> Reader:
        saved = self._storage.insert(reader.to_dict())
        return Reader.from_dict(saved)

    def update(self, reader_id: str, fields: dict) -> Reader | None:
        return self._storage.update(reader_id, fields)

    def delete(self, reader_id: str) -> bool:
        return self._storage.delete(reader_id)