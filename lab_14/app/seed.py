from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Book

BOOKS = (
    {
        "title": "Евгений Онегин",
        "author": "Пушкин А.С.",
        "genre": "Поэма",
        "year": 1833,
        "isbn": "9785000000001",
        "publisher": "Эксмо",
        "copies_total": 3,
        "copies_available": 2,
        "rating": Decimal("4.8"),
    },
    {
        "title": "Капитанская дочка",
        "author": "Пушкин А.С.",
        "genre": "Повесть",
        "year": 1836,
        "isbn": "9785000000002",
        "publisher": "АСТ",
        "copies_total": 2,
        "copies_available": 2,
        "rating": Decimal("4.6"),
    },
    {
        "title": "Война и мир",
        "author": "Толстой Л.Н.",
        "genre": "Роман",
        "year": 1869,
        "isbn": "9785000000003",
        "publisher": "Эксмо",
        "copies_total": 4,
        "copies_available": 3,
        "rating": Decimal("4.9"),
    },
    {
        "title": "Анна Каренина",
        "author": "Толстой Л.Н.",
        "genre": "Роман",
        "year": 1877,
        "isbn": "9785000000004",
        "publisher": "АСТ",
        "copies_total": 3,
        "copies_available": 3,
        "rating": Decimal("4.7"),
    },
    {
        "title": "Преступление и наказание",
        "author": "Достоевский Ф.М.",
        "genre": "Роман",
        "year": 1866,
        "isbn": "9785000000005",
        "publisher": "Азбука",
        "copies_total": 3,
        "copies_available": 2,
        "rating": Decimal("4.8"),
    },
    {
        "title": "Палата № 6",
        "author": "Чехов А.П.",
        "genre": "Повесть",
        "year": 1892,
        "isbn": "9785000000006",
        "publisher": "АСТ",
        "copies_total": 2,
        "copies_available": 2,
        "rating": Decimal("4.5"),
    },
    {
        "title": "Мастер и Маргарита",
        "author": "Булгаков М.А.",
        "genre": "Роман",
        "year": 1967,
        "isbn": "9785000000007",
        "publisher": "АСТ",
        "copies_total": 5,
        "copies_available": 4,
        "rating": Decimal("5.0"),
    },
    {
        "title": "Дюна",
        "author": "Герберт Ф.",
        "genre": "Фантастика",
        "year": 1965,
        "isbn": "9785000000008",
        "publisher": "Питер",
        "copies_total": 4,
        "copies_available": 3,
        "rating": Decimal("4.4"),
    },
)


def seed_database(session: Session) -> int:
    existing = session.scalar(select(func.count(Book.id))) or 0
    if existing:
        return 0

    session.add_all([Book(**row) for row in BOOKS])
    session.commit()
    return len(BOOKS)
