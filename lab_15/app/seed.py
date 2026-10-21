from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Author, Book, Loan, Reader

AUTHORS = (
    ("Пушкин А.С.", "Россия"),
    ("Толстой Л.Н.", "Россия"),
    ("Достоевский Ф.М.", "Россия"),
    ("Чехов А.П.", "Россия"),
)

BOOKS = (
    ("Евгений Онегин", 1, "Поэма", 1833, "9785000000011", "450.00", 3, 2),
    ("Капитанская дочка", 1, "Повесть", 1836, "9785000000012", "380.00", 2, 2),
    ("Война и мир", 2, "Роман", 1869, "9785000000013", "1200.00", 4, 3),
    ("Анна Каренина", 2, "Роман", 1877, "9785000000014", "990.00", 3, 3),
    ("Преступление и наказание", 3, "Роман", 1866, "9785000000015", "850.00", 3, 2),
    ("Палата № 6", 4, "Повесть", 1892, "9785000000016", "320.00", 2, 2),
)

READERS = (
    ("Иванов И.И.", "ivanov@mail.ru", "+7-900-100-10-01"),
    ("Петрова А.С.", "petrova@mail.ru", "+7-900-100-10-02"),
    ("Сидоров П.П.", "sidorov@mail.ru", "+7-900-100-10-03"),
)


def seed_database(session: Session) -> int:
    existing = session.scalar(select(func.count(Book.id))) or 0
    if existing:
        return 0

    authors = [Author(full_name=name, country=country) for name, country in AUTHORS]
    session.add_all(authors)
    session.flush()

    books = [
        Book(
            title=title,
            author=authors[author_index - 1],
            genre=genre,
            year=year,
            isbn=isbn,
            price=Decimal(price),
            copies_total=total,
            copies_available=available,
        )
        for title, author_index, genre, year, isbn, price, total, available in BOOKS
    ]
    session.add_all(books)

    readers = [Reader(full_name=name, email=email, phone=phone) for name, email, phone in READERS]
    session.add_all(readers)
    session.flush()

    today = date.today()
    session.add_all(
        [
            Loan(
                book=books[0],
                reader=readers[0],
                loan_date=today - timedelta(days=7),
                due_date=today + timedelta(days=7),
            ),
            Loan(
                book=books[4],
                reader=readers[1],
                loan_date=today - timedelta(days=20),
                due_date=today - timedelta(days=6),
                return_date=today - timedelta(days=8),
            ),
        ]
    )
    session.commit()
    return len(books)


if __name__ == "__main__":
    from app.database import create_tables, get_session

    create_tables()
    session = get_session()
    created = seed_database(session)
    print(f"Добавлено книг: {created}")
