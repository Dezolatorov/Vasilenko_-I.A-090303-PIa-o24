from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Reader(Base):
    __tablename__ = "readers"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30))
    registered_at: Mapped[date] = mapped_column(default=date.today, nullable=False)

    loans: Mapped[List["Loan"]] = relationship(
        back_populates="reader",
        cascade="all, delete",
    )

    def __repr__(self) -> str:
        return f"Reader(id={self.id}, full_name={self.full_name!r}, email={self.email!r})"


class Book(Base):
    __tablename__ = "books"
    __table_args__ = (
        CheckConstraint("year >= 1400 AND year <= 2100", name="ck_books_year"),
        CheckConstraint("price >= 0", name="ck_books_price"),
        CheckConstraint(
            "copies_available >= 0 AND copies_available <= copies_total",
            name="ck_books_copies",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    author: Mapped[str] = mapped_column(String(120), nullable=False)
    genre: Mapped[str] = mapped_column(String(60), nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    copies_total: Mapped[int] = mapped_column(nullable=False)
    copies_available: Mapped[int] = mapped_column(nullable=False)

    loans: Mapped[List["Loan"]] = relationship(
        back_populates="book",
        cascade="all, delete",
    )

    def __repr__(self) -> str:
        return f"Book(id={self.id}, title={self.title!r}, author={self.author!r})"


class Loan(Base):
    __tablename__ = "loans"
    __table_args__ = (
        UniqueConstraint("book_id", "reader_id", "loan_date", name="uq_loans_book_reader_date"),
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
        return (
            f"Loan(id={self.id}, book_id={self.book_id}, reader_id={self.reader_id}, "
            f"return_date={self.return_date})"
        )
