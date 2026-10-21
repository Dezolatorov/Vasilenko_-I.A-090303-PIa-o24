from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)

    books: Mapped[list["Book"]] = relationship(back_populates="author")


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"))
    year: Mapped[int] = mapped_column(Integer)
    isbn: Mapped[str] = mapped_column(String(13), unique=True)
    copies_total: Mapped[int] = mapped_column(Integer, default=1)
    copies_available: Mapped[int] = mapped_column(Integer, default=1)
    description: Mapped[str] = mapped_column(Text, default="")

    author: Mapped["Author"] = relationship(back_populates="books")
    loans: Mapped[list["Loan"]] = relationship(back_populates="book")

    __table_args__ = (
        CheckConstraint("year >= 1400 AND year <= 2100", name="ck_book_year"),
        CheckConstraint(
            "copies_available >= 0 AND copies_available <= copies_total", name="ck_book_copies"
        ),
    )


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))
    reader_name: Mapped[str] = mapped_column(String(150), nullable=False)
    loan_date: Mapped[date] = mapped_column(Date, default=date.today)
    due_date: Mapped[date] = mapped_column(Date)
    returned: Mapped[bool] = mapped_column(default=False)

    book: Mapped["Book"] = relationship(back_populates="loans")
