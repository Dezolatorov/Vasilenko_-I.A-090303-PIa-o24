from sqlalchemy.orm import Session

from ..models import Author, Book, Loan


class BookRepository:
    """Доступ к данным книг, авторов и выдач."""

    def __init__(self, db: Session):
        self.db = db

    def list_books(self, q: str = "", available_only: bool = False) -> list[Book]:
        query = self.db.query(Book)
        if q:
            query = query.filter(Book.title.ilike(f"%{q}%"))
        if available_only:
            query = query.filter(Book.copies_available > 0)
        return query.order_by(Book.title).all()

    def get_book(self, book_id: int) -> Book | None:
        return self.db.get(Book, book_id)

    def get_author(self, author_id: int) -> Author | None:
        return self.db.get(Author, author_id)

    def list_authors(self) -> list[Author]:
        return self.db.query(Author).order_by(Author.full_name).all()

    def count_books(self) -> int:
        return self.db.query(Book).count()

    def count_loans_active(self) -> int:
        return self.db.query(Loan).filter(Loan.returned.is_(False)).count()

    def create_book(self, **kwargs) -> Book:
        book = Book(**kwargs)
        self.db.add(book)
        self.db.commit()
        self.db.refresh(book)
        return book

    def extend_author(self, full_name: str) -> Author:
        author = self.db.query(Author).filter(Author.full_name == full_name).first()
        if author is None:
            author = Author(full_name=full_name)
            self.db.add(author)
            self.db.commit()
            self.db.refresh(author)
        return author

    def add_loan(self, book_id: int, reader_name: str, due_date) -> Loan:
        loan = Loan(book_id=book_id, reader_name=reader_name, due_date=due_date)
        self.db.add(loan)
        self.db.commit()
        self.db.refresh(loan)
        return loan

    def list_loans(self, active_only: bool = False) -> list[Loan]:
        query = self.db.query(Loan)
        if active_only:
            query = query.filter(Loan.returned.is_(False))
        return query.order_by(Loan.loan_date.desc()).all()
