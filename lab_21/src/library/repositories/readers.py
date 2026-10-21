"""Репозиторий читателей."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..exceptions import ConflictException
from ..models import Reader
from .base import BaseRepository


class ReaderRepository(BaseRepository[Reader]):
    model = Reader

    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_username(self, username: str) -> Reader | None:
        return self.db.scalar(
            select(Reader).where(Reader.username == username)
        )

    def get_by_email(self, email: str) -> Reader | None:
        return self.db.scalar(select(Reader).where(Reader.email == email))

    def ensure_unique(self, username: str, email: str) -> None:
        if self.get_by_username(username) is not None:
            raise ConflictException(f"Логин {username!r} уже занят")
        if self.get_by_email(email) is not None:
            raise ConflictException("Пользователь с таким email уже зарегистрирован")