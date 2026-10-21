from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, Sequence, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import Author, Book, Loan, Reader

SORT_FIELDS = {"title": Book.title, "year": Book.year, "price": Book.price}


class BookRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, book_id: int) -> Optional[Book]:
        return self.session.get(Book, book_id)

    def list(
        self,
        search: Optional[str] = None,
        genre: Optional[str] = None,
        available_only: bool = False,
        sort: str = "title",
        order: str = "asc",
    ) -> Sequence[Book]:
        statement = select(Book).options(selectinload(Book.author))
        conditions = []
        if search:
            pattern = f"%{search}%"
            conditions.append(
                or_(
                    Book.title.ilike(pattern),
                    Book.isbn.ilike(pattern),
                    Book.genre.ilike(pattern),
                    Book.author.has(Author.full_name.ilike(pattern)),
                )
            )
        if genre:
            conditions.append(Book.genre == genre)
        if available_only:
            conditions.append(Book.copies_available > 0)
        if conditions:
            statement = statement.where(*conditions)

        column = SORT_FIELDS.get(sort, Book.title)
        statement = statement.order_by(column.desc() if order == "desc" else column.asc(), Book.id)
        return self.session.scalars(statement).all()

    def create(self, fields: dict) -> Book:
        book = Book(**fields)
        self.session.add(book)
        self.session.commit()
        self.session.refresh(book)
        return book

    def update(self, book: Book, fields: dict) -> Book:
        for name, value in fields.items():
            setattr(book, name, value)
        self.session.commit()
        self.session.refresh(book)
        return book

    def delete(self, book: Book) -> None:
        self.session.delete(book)
        self.session.commit()

    def genres(self) -> Sequence[str]:
        return self.session.scalars(select(Book.genre).distinct().order_by(Book.genre)).all()

    def statistics(self) -> dict:
        totals = self.session.execute(
            select(
                func.count(Book.id),
                func.coalesce(func.sum(Book.copies_total), 0),
                func.coalesce(func.sum(Book.copies_available), 0),
                func.coalesce(func.avg(Book.price), 0),
            )
        ).one()
        by_genre = {
            row[0]: int(row[1])
            for row in self.session.execute(
                select(Book.genre, func.count(Book.id)).group_by(Book.genre)
            ).all()
        }
        return {
            "books": int(totals[0]),
            "copies_total": int(totals[1]),
            "copies_available": int(totals[2]),
            "avg_price": Decimal(str(totals[3])),
            "by_genre": by_genre,
        }


class AuthorRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, author_id: int) -> Optional[Author]:
        return self.session.get(Author, author_id)

    def list(self) -> Sequence[Author]:
        return self.session.scalars(select(Author).order_by(Author.full_name)).all()


class ReaderRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, reader_id: int) -> Optional[Reader]:
        return self.session.get(Reader, reader_id)

    def list(self) -> Sequence[Reader]:
        return self.session.scalars(select(Reader).order_by(Reader.full_name)).all()


class LoanRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, book: Book, reader: Reader, days: int = 14) -> Loan:
        today = date.today()
        loan = Loan(
            book=book,
            reader=reader,
            loan_date=today,
            due_date=today + timedelta(days=days),
        )
        self.session.add(loan)
        self.session.flush()
        return loan

    def get(self, loan_id: int) -> Optional[Loan]:
        return self.session.get(Loan, loan_id)

    def by_reader(self, reader_id: int) -> Sequence[Loan]:
        statement = (
            select(Loan)
            .options(selectinload(Loan.book))
            .where(Loan.reader_id == reader_id)
            .order_by(Loan.loan_date.desc(), Loan.id.desc())
        )
        return self.session.scalars(statement).all()

    def active(self) -> Sequence[Loan]:
        statement = (
            select(Loan)
            .options(selectinload(Loan.book), selectinload(Loan.reader))
            .where(Loan.return_date.is_(None))
            .order_by(Loan.due_date)
        )
        return self.session.scalars(statement).all()

    def active_for(self, book: Book, reader: Reader) -> Optional[Loan]:
        statement = select(Loan).where(
            Loan.book_id == book.id,
            Loan.reader_id == reader.id,
            Loan.return_date.is_(None),
        )
        return self.session.scalar(statement)
