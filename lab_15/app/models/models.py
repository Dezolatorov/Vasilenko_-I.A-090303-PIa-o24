from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    country: Mapped[str] = mapped_column(String(60), nullable=False, default="Россия")

    books: Mapped[List["Book"]] = relationship(back_populates="author", cascade="all, delete")

    def __repr__(self) -> str:
        return f"Author(id={self.id}, full_name={self.full_name!r})"


class Reader(Base):
    __tablename__ = "readers"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30))

    loans: Mapped[List["Loan"]] = relationship(back_populates="reader", cascade="all, delete")

    def __repr__(self) -> str:
        return f"Reader(id={self.id}, full_name={self.full_name!r})"


class Book(Base):
    __tablename__ = "books"
    __table_args__ = (
        CheckConstraint("year >= 1400 AND year <= 2100", name="ck_books_year"),
        CheckConstraint("copies_total >= 0", name="ck_books_copies_total"),
        CheckConstraint(
            "copies_available >= 0 AND copies_available <= copies_total",
            name="ck_books_copies_available",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id", ondelete="CASCADE"), nullable=False)
    genre: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    year: Mapped[int] = mapped_column(nullable=False)
    isbn: Mapped[str] = mapped_column(String(13), nullable=False, unique=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    copies_total: Mapped[int] = mapped_column(nullable=False, default=1)
    copies_available: Mapped[int] = mapped_column(nullable=False, default=1)

    author: Mapped["Author"] = relationship(back_populates="books")
    loans: Mapped[List["Loan"]] = relationship(back_populates="book", cascade="all, delete")

    def __repr__(self) -> str:
        return f"Book(id={self.id}, title={self.title!r})"


class Loan(Base):
    __tablename__ = "loans"
    __table_args__ = (
        CheckConstraint("due_date >= loan_date", name="ck_loans_dates"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    reader_id: Mapped[int] = mapped_column(ForeignKey("readers.id", ondelete="CASCADE"), nullable=False)
    loan_date: Mapped[date] = mapped_column(nullable=False, default=date.today)
    due_date: Mapped[date] = mapped_column(nullable=False)
    return_date: Mapped[Optional[date]] = mapped_column(nullable=True)

    book: Mapped["Book"] = relationship(back_populates="loans")
    reader: Mapped["Reader"] = relationship(back_populates="loans")

    def __repr__(self) -> str:
        return f"Loan(id={self.id}, book_id={self.book_id}, reader_id={self.reader_id})"
