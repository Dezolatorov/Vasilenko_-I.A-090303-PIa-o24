"""Базовый репозиторий: общий CRUD поверх SQLAlchemy."""
from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import Base
from ..exceptions import EntityNotFoundException

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, db: Session):
        self.db = db

    def get(self, entity_id: int) -> ModelT:
        instance = self.db.get(self.model, entity_id)
        if instance is None:
            raise EntityNotFoundException(
                f"{self.model.__name__} с id {entity_id} не найден"
            )
        return instance

    def get_or_none(self, entity_id: int) -> ModelT | None:
        return self.db.get(self.model, entity_id)

    def list_all(self) -> list[ModelT]:
        return list(self.db.scalars(select(self.model).order_by(self.model.id)).all())

    def add(self, instance: ModelT) -> ModelT:
        self.db.add(instance)
        self.db.flush()
        return instance

    def delete(self, instance: ModelT) -> None:
        self.db.delete(instance)
        self.db.flush()