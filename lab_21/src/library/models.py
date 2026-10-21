"""ORM-модели базы данных.

4 связанные сущности по варианту 2 «Библиотека»:
Reader, Author, Book, Loan.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Reader(Base):
    """Читатель (пользователь системы)."""

    __tablename__ = "readers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(128), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(16), default="USER", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=_utcnow, nullable=False
    )

    loans: Mapped[list["Loan"]] = relationship(
        back_populates="reader", cascade="all, delete-orphan"
    )


class Author(Base):
    """Автор книг."""

    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    birth_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    biography: Mapped[str | None] = mapped_column(Text, nullable=True)

    books: Mapped[list["Book"]] = relationship(back_populates="author")


class Book(Base):
    """Книга в фонде библиотеки."""

    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author_id: Mapped[int] = mapped_column(
        ForeignKey("authors.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    total_copies: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    available_copies: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    author: Mapped["Author"] = relationship(back_populates="books")
    loans: Mapped[list["Loan"]] = relationship(back_populates="book")


class Loan(Base):
    """Выдача книги читателю.

    Пара (book_id, reader_id, issue_date) уникальна: одна запись выдачи
    на каждую физическую операцию (для простоты - экземпляр не отслеживается).
    """

    __tablename__ = "loans"
    __table_args__ = (
        UniqueConstraint("book_id", "reader_id", "issue_date", name="uix_loan"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    reader_id: Mapped[int] = mapped_column(
        ForeignKey("readers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    return_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    returned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    book: Mapped["Book"] = relationship(back_populates="loans")
    reader: Mapped["Reader"] = relationship(back_populates="loans")


def as_dict(instance) -> dict:
    """Преобразует ORM-объект в dict (для сервисов/API)."""
    result: dict = {}
    for column in instance.__table__.columns:
        value = getattr(instance, column.name)
        if isinstance(value, datetime):
            result[column.name] = value.isoformat()
        elif isinstance(value, date):
            result[column.name] = value.isoformat()
        else:
            result[column.name] = value
    return result