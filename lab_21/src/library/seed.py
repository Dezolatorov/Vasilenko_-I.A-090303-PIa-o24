"""Скрипт наполнения БД стартовыми данными (для демонстрации)."""
from __future__ import annotations

from datetime import date, timedelta

from .auth import hash_password
from .database import SessionLocal, engine
from .models import Author, Base, Book, Loan, Reader


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Reader).first() is not None:
            return  # данные уже есть
        author_pushkin = Author(name="Александр Пушкин", birth_year=1799)
        author_tolstoy = Author(name="Лев Толстой", birth_year=1828)
        author_dostoevsky = Author(name="Фёдор Достоевский", birth_year=1821)
        db.add_all([author_pushkin, author_tolstoy, author_dostoevsky])

        book_1 = Book(title="Евгений Онегин", author=author_pushkin,
                      year=1833, total_copies=3, available_copies=3)
        book_2 = Book(title="Война и мир", author=author_tolstoy,
                      year=1869, total_copies=4, available_copies=4)
        book_3 = Book(title="Преступление и наказание", author=author_dostoevsky,
                      year=1866, total_copies=2, available_copies=2)
        db.add_all([book_1, book_2, book_3])

        admin = Reader(
            username="admin", email="admin@lib.local", full_name="Администратор",
            hashed_password=hash_password("admin123"), role="ADMIN",
        )
        user = Reader(
            username="reader", email="reader@lib.local", full_name="Обычный читатель",
            hashed_password=hash_password("reader123"), role="USER",
        )
        db.add_all([admin, user])
        db.flush()

        today = date.today()
        db.add(Loan(book_id=book_1.id, reader_id=user.id, issue_date=today,
                    due_date=today + timedelta(days=30), returned=False))
        db.commit()
        print("БД заполнена стартовыми данными.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()