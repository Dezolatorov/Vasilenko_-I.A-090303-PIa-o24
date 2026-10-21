"""Репозиторий — слой доступа к данным.

Репозиторий инкапсулирует SQL-запросы к SQLite (через aiosqlite) и
возвращает доменные модели. Обработчики и сервисы не работают с SQL
напрямую — это требование методички (разделение на слои).
"""
from datetime import date, timedelta
from typing import Sequence

import aiosqlite

from .db import get_db
from .models import Author, Book, Loan, NewLoan, Reader


def _iso(d: date) -> str:
    return d.isoformat()


async def _fetch_book(row: aiosqlite.Row) -> Book:
    return Book(
        id=row["id"],
        title=row["title"],
        author_id=row["author_id"],
        author_name=row["author_name"],
        year=row["year"],
        isbn=row["isbn"],
        copies_total=row["copies_total"],
        copies_available=row["copies_available"],
    )


# --------------------------------------------------------------------------
# Author
# --------------------------------------------------------------------------

async def create_author(full_name: str) -> Author:
    db = await get_db()
    cur = await db.execute("INSERT INTO authors (full_name) VALUES (?)", (full_name.strip(),))
    await db.commit()
    return Author(id=cur.lastrowid, full_name=full_name.strip())


async def get_or_create_author(full_name: str) -> Author:
    db = await get_db()
    cur = await db.execute("SELECT * FROM authors WHERE full_name = ?", (full_name.strip(),))
    row = await cur.fetchone()
    if row is not None:
        return Author(id=row["id"], full_name=row["full_name"])
    return await create_author(full_name)


async def find_authors(full_name: str) -> Sequence[Author]:
    db = await get_db()
    cur = await db.execute(
        "SELECT * FROM authors WHERE full_name LIKE ? ORDER BY full_name",
        (f"%{full_name.strip()}%",),
    )
    rows = await cur.fetchall()
    return [Author(id=r["id"], full_name=r["full_name"]) for r in rows]


# --------------------------------------------------------------------------
# Reader
# --------------------------------------------------------------------------

async def create_reader(telegram_id: int, full_name: str) -> Reader:
    db = await get_db()
    cur = await db.execute(
        "INSERT INTO readers (telegram_id, full_name) VALUES (?, ?)",
        (telegram_id, full_name.strip()),
    )
    await db.commit()
    return Reader(id=cur.lastrowid, telegram_id=telegram_id, full_name=full_name.strip())


async def get_reader_by_telegram(telegram_id: int) -> Reader | None:
    db = await get_db()
    cur = await db.execute("SELECT * FROM readers WHERE telegram_id = ?", (telegram_id,))
    row = await cur.fetchone()
    if row is None:
        return None
    return Reader(id=row["id"], telegram_id=row["telegram_id"], full_name=row["full_name"])


async def get_reader(reader_id: int) -> Reader | None:
    db = await get_db()
    cur = await db.execute("SELECT * FROM readers WHERE id = ?", (reader_id,))
    row = await cur.fetchone()
    if row is None:
        return None
    return Reader(id=row["id"], telegram_id=row["telegram_id"], full_name=row["full_name"])


async def list_readers() -> Sequence[Reader]:
    db = await get_db()
    cur = await db.execute("SELECT * FROM readers ORDER BY full_name")
    rows = await cur.fetchall()
    return [Reader(id=r["id"], telegram_id=r["telegram_id"], full_name=r["full_name"]) for r in rows]


# --------------------------------------------------------------------------
# Book
# --------------------------------------------------------------------------

_LIST_BOOKS = """
    SELECT b.*, a.full_name AS author_name
    FROM books b JOIN authors a ON a.id = b.author_id
    {where}
    ORDER BY b.title
"""


async def list_books() -> Sequence[Book]:
    db = await get_db()
    cur = await db.execute(_LIST_BOOKS.format(where=""))
    rows = await cur.fetchall()
    return [await _fetch_book(r) for r in rows]


async def get_book(book_id: int) -> Book | None:
    db = await get_db()
    cur = await db.execute(
        _LIST_BOOKS.format(where="WHERE b.id = ?"),
        (book_id,),
    )
    row = await cur.fetchone()
    if row is None:
        return None
    return await _fetch_book(row)


async def create_book(
    title: str,
    author: Author,
    year: int | None,
    isbn: str | None,
    copies_total: int,
    copies_available: int,
) -> Book:
    db = await get_db()
    cur = await db.execute(
        "INSERT INTO books (title, author_id, year, isbn, copies_total, copies_available) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (title.strip(), author.id, year, isbn, copies_total, copies_available),
    )
    await db.commit()
    return Book(
        id=cur.lastrowid,
        title=title.strip(),
        author_id=author.id,
        author_name=author.full_name,
        year=year,
        isbn=isbn,
        copies_total=copies_total,
        copies_available=copies_available,
    )


async def update_book(
    book_id: int,
    title: str,
    author: Author,
    year: int | None,
    isbn: str | None,
    copies_total: int,
    copies_available: int,
) -> Book | None:
    db = await get_db()
    cur = await db.execute(
        "UPDATE books SET title=?, author_id=?, year=?, isbn=?, copies_total=?, copies_available=? "
        "WHERE id=?",
        (title.strip(), author.id, year, isbn, copies_total, copies_available, book_id),
    )
    await db.commit()
    if cur.rowcount == 0:
        return None
    return await get_book(book_id)


async def delete_book(book_id: int) -> bool:
    db = await get_db()
    cur = await db.execute("DELETE FROM books WHERE id=?", (book_id,))
    await db.commit()
    return cur.rowcount > 0


async def search_books(query: str, author_name: str = "") -> Sequence[Book]:
    """Поиск книг по названию и/или по имени автора."""
    db = await get_db()
    where = ["(b.title LIKE ? OR a.full_name LIKE ?)"]
    params: list = [f"%{query.strip()}%", f"%{query.strip()}%"]
    if author_name.strip():
        where.append("a.full_name LIKE ?")
        params.append(f"%{author_name.strip()}%")
    cur = await db.execute(
        _LIST_BOOKS.format(where="WHERE " + " AND ".join(where)),
        params,
    )
    rows = await cur.fetchall()
    return [await _fetch_book(r) for r in rows]


# --------------------------------------------------------------------------
# Loan
# --------------------------------------------------------------------------

_LOAN_SELECT = """
    SELECT l.*, b.title AS book_title, r.full_name AS reader_name
    FROM loans l
    JOIN books b ON b.id = l.book_id
    JOIN readers r ON r.id = l.reader_id
"""


def _row_to_loan(row: aiosqlite.Row) -> Loan:
    return Loan(
        id=row["id"],
        book_id=row["book_id"],
        reader_id=row["reader_id"],
        issued_at=date.fromisoformat(row["issued_at"]),
        due_date=date.fromisoformat(row["due_date"]),
        returned_at=date.fromisoformat(row["returned_at"]) if row["returned_at"] else None,
        book_title=row["book_title"],
        reader_name=row["reader_name"],
    )


async def create_loan(new: NewLoan) -> Loan:
    db = await get_db()
    cur = await db.execute(
        "INSERT INTO loans (book_id, reader_id, issued_at, due_date) VALUES (?, ?, ?, ?)",
        (new.book_id, new.reader_id, _iso(new.issued_at), _iso(new.due_date)),
    )
    await db.execute(
        "UPDATE books SET copies_available = copies_available - 1 WHERE id=?",
        (new.book_id,),
    )
    await db.commit()
    loan = await get_loan(cur.lastrowid)
    assert loan is not None
    return loan


async def get_loan(loan_id: int) -> Loan | None:
    db = await get_db()
    cur = await db.execute(_LOAN_SELECT + " WHERE l.id=?", (loan_id,))
    row = await cur.fetchone()
    return _row_to_loan(row) if row else None


async def list_active_loans() -> Sequence[Loan]:
    db = await get_db()
    cur = await db.execute(_LOAN_SELECT + " WHERE l.returned_at IS NULL ORDER BY l.due_date")
    rows = await cur.fetchall()
    return [_row_to_loan(r) for r in rows]


async def list_loans_by_reader(reader_id: int) -> Sequence[Loan]:
    db = await get_db()
    cur = await db.execute(
        _LOAN_SELECT + " WHERE l.reader_id=? ORDER BY l.issued_at DESC",
        (reader_id,),
    )
    rows = await cur.fetchall()
    return [_row_to_loan(r) for r in rows]


async def is_book_with_reader(book_id: int, reader_id: int) -> bool:
    db = await get_db()
    cur = await db.execute(
        "SELECT 1 FROM loans WHERE book_id=? AND reader_id=? AND returned_at IS NULL",
        (book_id, reader_id),
    )
    return await cur.fetchone() is not None


async def return_loan(loan_id: int) -> bool:
    db = await get_db()
    cur = await db.execute("SELECT * FROM loans WHERE id=?", (loan_id,))
    row = await cur.fetchone()
    if row is None or row["returned_at"] is not None:
        return False
    await db.execute("UPDATE loans SET returned_at=? WHERE id=?", (_iso(date.today()), loan_id))
    await db.execute(
        "UPDATE books SET copies_available = copies_available + 1 WHERE id=?",
        (row["book_id"],),
    )
    await db.commit()
    return True


async def overdue_loans(today: date) -> Sequence[Loan]:
    """Активные выдачи, срок которых истёк к дате today."""
    active = await list_active_loans()
    return [ln for ln in active if ln.due_date < today]