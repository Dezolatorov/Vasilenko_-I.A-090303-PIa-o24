import logging
from datetime import date, timedelta

from fastapi import HTTPException

from ..repositories import BookRepository

logger = logging.getLogger("library.service")


class LibraryService:
    """Бизнес-логика библиотеки поверх репозитория."""

    def __init__(self, repo: BookRepository):
        self.repo = repo

    def list_books(self, q: str = "", available_only: bool = False):
        logger.info("list_books called (q=%r, available_only=%s)", q, available_only)
        return self.repo.list_books(q=q, available_only=available_only)

    def get_book(self, book_id: int):
        book = self.repo.get_book(book_id)
        if book is None:
            logger.warning("book %s not found", book_id)
            raise HTTPException(status_code=404, detail="Book not found")
        return book

    def get_stats(self) -> dict:
        stats = {
            "total_books": self.repo.count_books(),
            "active_loans": self.repo.count_loans_active(),
            "authors": len(self.repo.list_authors()),
        }
        logger.info("stats computed: %s", stats)
        return stats

    def create_book(self, payload: dict):
        author = self.repo.extend_author(payload["author_name"])
        book = self.repo.create_book(
            title=payload["title"],
            author_id=author.id,
            year=payload["year"],
            isbn=payload["isbn"],
            copies_total=payload["copies_total"],
            copies_available=payload["copies_total"],
            description=payload.get("description", ""),
        )
        logger.info("book created: #%s %s", book.id, book.title)
        return book

    def borrow_book(self, book_id: int, reader_name: str, days: int = 14):
        book = self.get_book(book_id)
        if book.copies_available <= 0:
            logger.error("no copies for book %s", book_id)
            raise HTTPException(status_code=409, detail="No available copies")
        book.copies_available -= 1
        due = date.today() + timedelta(days=days)
        loan = self.repo.add_loan(book_id=book.id, reader_name=reader_name, due_date=due)
        logger.info("loan created: book=%s reader=%s due=%s", book.id, reader_name, due)
        return loan
