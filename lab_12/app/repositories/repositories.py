from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import Book, Loan, Reader

SORT_FIELDS = {
    "title": Book.title,
    "author": Book.author,
    "year": Book.year,
    "price": Book.price,
}


class BookRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, book: Book) -> Book:
        self.session.add(book)
        self.session.flush()
        return book

    def get(self, book_id: int) -> Optional[Book]:
        return self.session.get(Book, book_id)

    def list(
        self,
        sort: str = "title",
        descending: bool = False,
        offset: int = 0,
        limit: int = 50,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        available_only: bool = False,
    ) -> Sequence[Book]:
        stmt = select(Book)
        if min_price is not None:
            stmt = stmt.where(Book.price >= min_price)
        if max_price is not None:
            stmt = stmt.where(Book.price <= max_price)
        if available_only:
            stmt = stmt.where(Book.copies_available > 0)

        column = SORT_FIELDS.get(sort, Book.title)
        stmt = stmt.order_by(column.desc() if descending else column.asc(), Book.id)
        stmt = stmt.offset(offset).limit(limit)
        return self.session.scalars(stmt).all()

    def search(self, query: str) -> Sequence[Book]:
        pattern = f"%{query}%"
        stmt = (
            select(Book)
            .where(
                or_(
                    Book.title.ilike(pattern),
                    Book.author.ilike(pattern),
                    Book.genre.ilike(pattern),
                )
            )
            .order_by(Book.title)
        )
        return self.session.scalars(stmt).all()

    def by_author(self, author: str) -> Sequence[Book]:
        stmt = select(Book).where(Book.author.ilike(f"%{author}%")).order_by(Book.year)
        return self.session.scalars(stmt).all()

    def delete(self, book: Book) -> None:
        self.session.delete(book)
        self.session.flush()

    def statistics(self) -> dict:
        stmt = select(
            func.count(Book.id),
            func.coalesce(func.sum(Book.copies_total), 0),
            func.coalesce(func.sum(Book.copies_available), 0),
            func.coalesce(func.avg(Book.price), 0),
            func.coalesce(func.min(Book.price), 0),
            func.coalesce(func.max(Book.price), 0),
        )
        count, total, available, avg_price, min_price, max_price = self.session.execute(stmt).one()
        return {
            "books": int(count),
            "copies_total": int(total),
            "copies_available": int(available),
            "avg_price": Decimal(str(avg_price)),
            "min_price": Decimal(str(min_price)),
            "max_price": Decimal(str(max_price)),
        }


class ReaderRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, reader: Reader) -> Reader:
        self.session.add(reader)
        self.session.flush()
        return reader

    def get(self, reader_id: int) -> Optional[Reader]:
        return self.session.get(Reader, reader_id)

    def get_by_email(self, email: str) -> Optional[Reader]:
        return self.session.scalar(select(Reader).where(Reader.email == email))

    def list(self, limit: int = 50) -> Sequence[Reader]:
        return self.session.scalars(select(Reader).order_by(Reader.full_name).limit(limit)).all()

    def delete(self, reader: Reader) -> None:
        self.session.delete(reader)
        self.session.flush()


class LoanRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, book: Book, reader: Reader, days: int = 14) -> Loan:
        loan = Loan(
            book=book,
            reader=reader,
            loan_date=date.today(),
            due_date=date.today() + timedelta(days=days),
        )
        self.session.add(loan)
        self.session.flush()
        return loan

    def get(self, loan_id: int) -> Optional[Loan]:
        return self.session.get(Loan, loan_id)

    def by_reader(self, reader_id: int) -> Sequence[Loan]:
        stmt = (
            select(Loan)
            .options(selectinload(Loan.book), selectinload(Loan.reader))
            .where(Loan.reader_id == reader_id)
            .order_by(Loan.loan_date.desc(), Loan.id.desc())
        )
        return self.session.scalars(stmt).all()

    def active(self) -> Sequence[Loan]:
        stmt = (
            select(Loan)
            .options(selectinload(Loan.book), selectinload(Loan.reader))
            .where(Loan.return_date.is_(None))
            .order_by(Loan.due_date)
        )
        return self.session.scalars(stmt).all()

    def overdue(self) -> Sequence[Loan]:
        stmt = (
            select(Loan)
            .options(selectinload(Loan.book), selectinload(Loan.reader))
            .where(Loan.return_date.is_(None), Loan.due_date < date.today())
            .order_by(Loan.due_date)
        )
        return self.session.scalars(stmt).all()

    def active_for(self, book: Book, reader: Reader) -> Optional[Loan]:
        stmt = select(Loan).where(
            Loan.book_id == book.id,
            Loan.reader_id == reader.id,
            Loan.return_date.is_(None),
        )
        return self.session.scalar(stmt)

