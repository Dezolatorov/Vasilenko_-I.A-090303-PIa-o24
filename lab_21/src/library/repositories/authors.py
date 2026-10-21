"""Репозиторий авторов."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Author
from .base import BaseRepository


class AuthorRepository(BaseRepository[Author]):
    model = Author

    def __init__(self, db: Session):
        super().__init__(db)

    def search(self, name_contains: str | None = None) -> list[Author]:
        stmt = select(Author)
        if name_contains:
            stmt = stmt.where(Author.name.ilike(f"%{name_contains}%"))
        return list(self.db.scalars(stmt.order_by(Author.name)).all())