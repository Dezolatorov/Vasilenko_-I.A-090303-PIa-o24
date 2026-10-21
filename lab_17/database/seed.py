"""Демонстрационные данные для БД бота (не менее 20 книг).

Сидирование выполняется только для пустой базы, чтобы повторный запуск
бота не создавал дубликаты.
"""
from __future__ import annotations

from datetime import date, timedelta

from database import repository

AUTHORS = [
    "Лев Толстой",
    "Фёдор Достоевский",
    "Михаил Булгаков",
    "Антон Чехов",
    "Роберт Мартин",
    "Дональд Кнут",
]

# (название, автор, год, всего экземпляров)
BOOKS = [
    ("Война и мир", "Лев Толстой", 1869, 3),
    ("Анна Каренина", "Лев Толстой", 1877, 2),
    ("Воскресение", "Лев Толстой", 1899, 1),
    ("Преступление и наказание", "Фёдор Достоевский", 1866, 3),
    ("Идиот", "Фёдор Достоевский", 1869, 2),
    ("Братья Карамазовы", "Фёдор Достоевский", 1880, 2),
    ("Бесы", "Фёдор Достоевский", 1872, 1),
    ("Мастер и Маргарита", "Михаил Булгаков", 1967, 4),
    ("Белая гвардия", "Михаил Булгаков", 1925, 2),
    ("Собачье сердце", "Михаил Булгаков", 1925, 2),
    ("Театральный роман", "Михаил Булгаков", 1965, 1),
    ("Вишнёвый сад", "Антон Чехов", 1904, 2),
    ("Три сестры", "Антон Чехов", 1901, 2),
    ("Чайка", "Антон Чехов", 1896, 1),
    ("Дама с собачкой", "Антон Чехов", 1899, 2),
    ("Палата № 6", "Антон Чехов", 1892, 1),
    ("Clean Code", "Роберт Мартин", 2008, 3),
    ("Clean Architecture", "Роберт Мартин", 2017, 2),
    ("Идеальный программист", "Роберт Мартин", 2011, 1),
    ("Гибкая разработка", "Роберт Мартин", 2002, 1),
    ("Искусство программирования, т. 1", "Дональд Кнут", 1968, 2),
    ("Искусство программирования, т. 2", "Дональд Кнут", 1969, 2),
    ("Искусство программирования, т. 3", "Дональд Кнут", 1973, 1),
    ("Конкретная математика", "Дональд Кнут", 1994, 1),
]

READERS = [
    (1001, "Иванов Иван"),
    (1002, "Петрова Анна"),
    (1003, "Сидоров Пётр"),
    (1004, "Кузнецова Мария"),
]


async def seed_if_empty() -> int:
    """Заполняет БД, если книг ещё нет. Возвращает число добавленных книг."""
    if await repository.list_books():
        return 0

    authors = {}
    for name in AUTHORS:
        authors[name] = await repository.get_or_create_author(name)

    readers = []
    for telegram_id, full_name in READERS:
        reader = await repository.get_reader_by_telegram(telegram_id)
        if reader is None:
            reader = await repository.create_reader(telegram_id, full_name)
        readers.append(reader)

    added = 0
    book_ids = []
    for index, (title, author_name, year, copies) in enumerate(BOOKS, start=1):
        isbn = f"978{index:010d}"
        book = await repository.create_book(
            title=title,
            author=authors[author_name],
            year=year,
            isbn=isbn,
            copies_total=copies,
            copies_available=copies,
        )
        book_ids.append(book.id)
        added += 1

    # Пара активных выдач и одна просроченная — для демонстрации /mybooks и /overdue.
    today = date.today()
    loans = [
        (book_ids[0], readers[0], today - timedelta(days=5), today + timedelta(days=9)),
        (book_ids[3], readers[1], today - timedelta(days=20), today - timedelta(days=6)),
        (book_ids[7], readers[2], today - timedelta(days=2), today + timedelta(days=12)),
    ]
    for book_id, reader, issued_at, due_date in loans:
        await repository.create_loan(
            repository.NewLoan(
                book_id=book_id,
                reader_id=reader.id,
                issued_at=issued_at,
                due_date=due_date,
            )
        )

    return added
