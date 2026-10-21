"""Репозиторий книг с фильтрацией и сортировкой."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Book
from .base import BaseRepository


class BookRepository(BaseRepository[Book]):
    model = Book

    def __init__(self, db: Session):
        super().__init__(db)

    def search(
        self,
        title: str | None = None,
        author_id: int | None = None,
        year_from: int | None = None,
        available_only: bool = False,
        sort_by: str = "title",
        descending: bool = False,
    ) -> list[Book]:
        stmt = select(Book)
        if title:
            stmt = stmt.where(Book.title.ilike(f"%{title}%"))
        if author_id is not None:
            stmt = stmt.where(Book.author_id == author_id)
        if year_from is not None:
            stmt = stmt.where(Book.year >= year_from)
        if available_only:
            stmt = stmt.where(Book.available_copies > 0)

        order_col = {
            "title": Book.title,
            "year": Book.year,
            "id": Book.id,
        }.get(sort_by, Book.title)
        order = order_col.desc() if descending else order_col.asc()
        stmt = stmt.order_by(order)
        return list(self.db.scalars(stmt).all())