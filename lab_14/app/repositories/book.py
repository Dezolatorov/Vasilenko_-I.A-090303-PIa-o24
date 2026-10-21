from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, Optional, Sequence, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Book

SORT_FIELDS = {
    "title": Book.title,
    "author": Book.author,
    "year": Book.year,
    "rating": Book.rating,
}


class BookRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, book: Book) -> Book:
        self.session.add(book)
        self.session.commit()
        self.session.refresh(book)
        return book

    def get(self, book_id: int) -> Optional[Book]:
        return self.session.get(Book, book_id)

    def get_by_isbn(self, isbn: str) -> Optional[Book]:
        return self.session.scalar(select(Book).where(Book.isbn == isbn))

    def list(
        self,
        genre: Optional[str] = None,
        author: Optional[str] = None,
        min_rating: Optional[float] = None,
        sort: str = "title",
        order: str = "asc",
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[Sequence[Book], int]:
        conditions = []
        if genre:
            conditions.append(Book.genre == genre)
        if author:
            conditions.append(Book.author.ilike(f"%{author}%"))
        if min_rating is not None:
            conditions.append(Book.rating >= Decimal(str(min_rating)))

        base = select(Book)
        if conditions:
            base = base.where(*conditions)

        total = self.session.scalar(select(func.count()).select_from(base.subquery())) or 0
        column = SORT_FIELDS.get(sort, Book.title)
        direction = column.desc() if order.lower() == "desc" else column.asc()
        statement = base.order_by(direction, Book.id).limit(limit).offset(offset)

        return self.session.scalars(statement).all(), int(total)

    def search(self, query: str, limit: int = 20) -> Sequence[Book]:
        pattern = f"%{query}%"
        statement = (
            select(Book)
            .where(
                or_(
                    Book.title.ilike(pattern),
                    Book.author.ilike(pattern),
                    Book.publisher.ilike(pattern),
                    Book.genre.ilike(pattern),
                )
            )
            .order_by(Book.title)
            .limit(limit)
        )
        return self.session.scalars(statement).all()

    def update(self, book: Book, fields: Dict[str, Any]) -> Book:
        for name, value in fields.items():
            setattr(book, name, value)
        self.session.commit()
        self.session.refresh(book)
        return book

    def delete(self, book: Book) -> None:
        self.session.delete(book)
        self.session.commit()

    def statistics(self) -> Dict[str, Any]:
        totals = self.session.execute(
            select(
                func.count(Book.id),
                func.coalesce(func.avg(Book.rating), 0),
                func.coalesce(func.max(Book.rating), 0),
                func.coalesce(func.sum(Book.copies_total), 0),
            )
        ).one()

        by_genre = {
            row[0]: int(row[1])
            for row in self.session.execute(
                select(Book.genre, func.count(Book.id))
                .group_by(Book.genre)
                .order_by(func.count(Book.id).desc())
            ).all()
        }

        return {
            "total": int(totals[0]),
            "average_rating": round(float(totals[1]), 2),
            "max_rating": float(totals[2]),
            "total_copies": int(totals[3]),
            "by_genre": by_genre,
        }
