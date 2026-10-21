from __future__ import annotations

from decimal import Decimal

from sqlalchemy import CheckConstraint, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Book(Base):
    __tablename__ = "books"
    __table_args__ = (
        CheckConstraint("year >= 1400 AND year <= 2100", name="ck_books_year"),
        CheckConstraint("copies_total >= 0", name="ck_books_copies_total"),
        CheckConstraint(
            "copies_available >= 0 AND copies_available <= copies_total",
            name="ck_books_copies_available",
        ),
        CheckConstraint("rating >= 0 AND rating <= 5", name="ck_books_rating"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    author: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    genre: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    year: Mapped[int] = mapped_column(nullable=False)
    isbn: Mapped[str] = mapped_column(String(13), nullable=False, unique=True)
    publisher: Mapped[str] = mapped_column(String(120), nullable=False)
    copies_total: Mapped[int] = mapped_column(nullable=False)
    copies_available: Mapped[int] = mapped_column(nullable=False)
    rating: Mapped[Decimal] = mapped_column(Numeric(2, 1), nullable=False, default=Decimal("0.0"))

    def __repr__(self) -> str:
        return f"Book(id={self.id}, title={self.title!r}, author={self.author!r})"
