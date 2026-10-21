from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from app.database import Database
from app.models import Book, Loan, Reader


BOOKS = (
    ("Евгений Онегин", "Пушкин А.С.", "Поэма", 1833, "450.00", 3, 2),
    ("Капитанская дочка", "Пушкин А.С.", "Повесть", 1836, "380.00", 2, 2),
    ("Война и мир", "Толстой Л.Н.", "Роман", 1869, "1200.00", 4, 4),
    ("Анна Каренина", "Толстой Л.Н.", "Роман", 1877, "990.00", 3, 3),
    ("Преступление и наказание", "Достоевский Ф.М.", "Роман", 1866, "850.00", 3, 2),
    ("Идиот", "Достоевский Ф.М.", "Роман", 1869, "780.00", 2, 0),
    ("Палата № 6", "Чехов А.П.", "Повесть", 1892, "320.00", 2, 2),
    ("Мастер и Маргарита", "Булгаков М.А.", "Роман", 1967, "950.00", 5, 4),
)

READERS = (
    ("Иванов И.И.", "ivanov@mail.ru", "+7-900-100-10-01"),
    ("Петрова А.С.", "petrova@mail.ru", "+7-900-100-10-02"),
    ("Сидоров П.П.", "sidorov@mail.ru", "+7-900-100-10-03"),
    ("Кузнецова М.В.", "kuznetsova@mail.ru", "+7-900-100-10-04"),
    ("Смирнов Д.А.", "smirnov@mail.ru", "+7-900-100-10-05"),
)


def seed_database(database: Database) -> dict:
    today = date.today()
    with database.session() as session:
        books = [
            Book(
                title=title,
                author=author,
                genre=genre,
                year=year,
                price=Decimal(price),
                copies_total=total,
                copies_available=available,
            )
            for title, author, genre, year, price, total, available in BOOKS
        ]
        readers = [
            Reader(full_name=name, email=email, phone=phone, registered_at=today - timedelta(days=90))
            for name, email, phone in READERS
        ]
        session.add_all(books)
        session.add_all(readers)
        session.flush()

        loans = [
            Loan(
                book=books[0],
                reader=readers[0],
                loan_date=today - timedelta(days=47),
                due_date=today - timedelta(days=33),
                return_date=today - timedelta(days=36),
            ),
            Loan(
                book=books[4],
                reader=readers[1],
                loan_date=today - timedelta(days=10),
                due_date=today + timedelta(days=4),
            ),
            Loan(
                book=books[7],
                reader=readers[2],
                loan_date=today - timedelta(days=28),
                due_date=today - timedelta(days=14),
            ),
        ]
        session.add_all(loans)
        session.commit()

    return {"books": len(BOOKS), "readers": len(READERS), "loans": 3}
