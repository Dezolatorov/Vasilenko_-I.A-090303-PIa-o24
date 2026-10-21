"""Слой хранения данных: SQL-запросы к библиотечной БД.

Все запросы параметризованы: значения передаются отдельно от текста запроса,
поэтому подстановка пользовательских строк в SQL невозможна.
"""

import sqlite3

from db import Database
from models import Author, Book, BookDetails, Loan, Reader

SORT_COLUMNS: dict[str, str] = {
    "title": "b.title",
    "author": "a.full_name",
    "genre": "b.genre",
    "year": "b.year",
    "price": "b.price",
    "total_copies": "b.total_copies",
    "available_copies": "b.available_copies",
}


def _to_book(row: sqlite3.Row) -> Book:
    return Book(
        id=row["id"],
        title=row["title"],
        author_id=row["author_id"],
        genre=row["genre"],
        year=row["year"],
        price=row["price"],
        total_copies=row["total_copies"],
        available_copies=row["available_copies"],
        cover_path=row["cover_path"],
    )


def _to_loan(row: sqlite3.Row) -> Loan:
    return Loan(
        id=row["id"],
        book_id=row["book_id"],
        reader_id=row["reader_id"],
        taken_at=row["taken_at"],
        due_at=row["due_at"],
        returned_at=row["returned_at"],
    )


def _to_reader(row: sqlite3.Row) -> Reader:
    return Reader(
        id=row["id"],
        full_name=row["full_name"],
        email=row["email"],
        phone=row["phone"],
        registered_at=row["registered_at"],
    )


class BookRepository:
    """Операции над таблицей books через чистый SQL."""

    def __init__(self, database: Database) -> None:
        self.database = database

    def get_all(self, filters: dict | None = None, sort_by: str | None = None, order: str = "asc") -> list[Book]:
        """Выбрать книги с фильтрацией и сортировкой."""
        filters = filters or {}
        conditions: list[str] = []
        params: list[object] = []

        if "author" in filters:
            conditions.append("py_lower(a.full_name) LIKE py_lower(?)")
            params.append(f"%{filters['author']}%")
        if "author_id" in filters:
            conditions.append("b.author_id = ?")
            params.append(filters["author_id"])
        if "genre" in filters:
            conditions.append("py_lower(b.genre) = py_lower(?)")
            params.append(filters["genre"])
        if "q" in filters:
            conditions.append("py_lower(b.title) LIKE py_lower(?)")
            params.append(f"%{filters['q']}%")
        if "tag" in filters:
            conditions.append(
                "EXISTS (SELECT 1 FROM book_tags AS bt"
                " JOIN tags AS t ON t.id = bt.tag_id"
                " WHERE bt.book_id = b.id AND py_lower(t.name) = py_lower(?))"
            )
            params.append(filters["tag"])
        if "available" in filters:
            conditions.append("b.available_copies > 0" if filters["available"] else "b.available_copies = 0")
        if "min_price" in filters:
            conditions.append("b.price >= ?")
            params.append(filters["min_price"])
        if "max_price" in filters:
            conditions.append("b.price <= ?")
            params.append(filters["max_price"])
        if "year_from" in filters:
            conditions.append("b.year >= ?")
            params.append(filters["year_from"])
        if "year_to" in filters:
            conditions.append("b.year <= ?")
            params.append(filters["year_to"])

        query = "SELECT b.* FROM books AS b JOIN authors AS a ON a.id = b.author_id"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        column = SORT_COLUMNS.get(sort_by or "id", "b.id")
        query += f" ORDER BY {column} {'DESC' if order == 'desc' else 'ASC'}"

        with self.database.connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [_to_book(row) for row in rows]

    def get_by_id(self, book_id: int) -> Book | None:
        with self.database.connection() as connection:
            row = connection.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
        return _to_book(row) if row else None

    def get_details(self, book_id: int) -> BookDetails | None:
        """Книга, её автор и теги одним запросом с агрегацией GROUP_CONCAT."""
        query = """
            SELECT b.id, b.title, a.full_name AS author, a.country, b.genre, b.year, b.price,
                   b.total_copies, b.available_copies, b.cover_path,
                   COALESCE(GROUP_CONCAT(t.name, ', '), '') AS tags
            FROM books AS b
            JOIN authors AS a ON a.id = b.author_id
            LEFT JOIN book_tags AS bt ON bt.book_id = b.id
            LEFT JOIN tags AS t ON t.id = bt.tag_id
            WHERE b.id = ?
            GROUP BY b.id
        """
        with self.database.connection() as connection:
            row = connection.execute(query, (book_id,)).fetchone()
        if row is None:
            return None
        return BookDetails(
            id=row["id"],
            title=row["title"],
            author=row["author"],
            country=row["country"],
            genre=row["genre"],
            year=row["year"],
            price=row["price"],
            total_copies=row["total_copies"],
            available_copies=row["available_copies"],
            tags=[tag for tag in row["tags"].split(", ") if tag],
            cover_url=row["cover_path"],
        )

    def create(self, data: dict) -> Book:
        """Добавить книгу. Значения передаются параметрами (?, ?, ...)."""
        query = """
            INSERT INTO books (title, author_id, genre, year, price,
                               total_copies, available_copies, cover_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        available = data.get("available_copies", data["total_copies"])
        params = (
            data["title"],
            data["author_id"],
            data["genre"],
            data["year"],
            data["price"],
            data["total_copies"],
            available,
            data.get("cover_path"),
        )
        with self.database.connection() as connection:
            cursor = connection.execute(query, params)
            book_id = cursor.lastrowid
        created = self.get_by_id(book_id)
        assert created is not None
        return created

    def update(self, book: Book, connection: sqlite3.Connection | None = None) -> Book:
        """Полностью обновить запись книги."""
        query = """
            UPDATE books
            SET title = ?, author_id = ?, genre = ?, year = ?, price = ?,
                total_copies = ?, available_copies = ?, cover_path = ?
            WHERE id = ?
        """
        params = (
            book.title, book.author_id, book.genre, book.year, book.price,
            book.total_copies, book.available_copies, book.cover_path, book.id,
        )
        if connection is not None:
            connection.execute(query, params)
        else:
            with self.database.connection() as own:
                own.execute(query, params)
        return book

    def delete(self, book_id: int) -> bool:
        with self.database.connection() as connection:
            cursor = connection.execute("DELETE FROM books WHERE id = ?", (book_id,))
            return cursor.rowcount > 0

    def count(self) -> int:
        with self.database.connection() as connection:
            row = connection.execute("SELECT COUNT(*) AS total FROM books").fetchone()
        return int(row["total"])

    def author_exists(self, author_id: int) -> bool:
        with self.database.connection() as connection:
            row = connection.execute("SELECT 1 FROM authors WHERE id = ?", (author_id,)).fetchone()
        return row is not None

    def get_authors(self) -> list[Author]:
        with self.database.connection() as connection:
            rows = connection.execute("SELECT * FROM authors ORDER BY full_name").fetchall()
        return [Author(id=row["id"], full_name=row["full_name"], country=row["country"]) for row in rows]

    def genre_stats(self) -> list[dict]:
        """GROUP BY: количество и средняя цена по жанрам."""
        query = """
            SELECT genre,
                   COUNT(*) AS books_count,
                   ROUND(AVG(price), 2) AS avg_price,
                   SUM(total_copies) AS copies
            FROM books
            GROUP BY genre
            ORDER BY books_count DESC, genre
        """
        with self.database.connection() as connection:
            rows = connection.execute(query).fetchall()
        return [dict(row) for row in rows]

    def author_stats(self) -> list[dict]:
        """JOIN + GROUP BY + HAVING: авторы с двумя и более книгами."""
        query = """
            SELECT a.full_name AS author, COUNT(b.id) AS books_count,
                   ROUND(AVG(b.price), 2) AS avg_price
            FROM authors AS a
            JOIN books AS b ON b.author_id = a.id
            GROUP BY a.id, a.full_name
            HAVING COUNT(b.id) >= 2
            ORDER BY books_count DESC, author
        """
        with self.database.connection() as connection:
            rows = connection.execute(query).fetchall()
        return [dict(row) for row in rows]

    def tag_stats(self) -> list[dict]:
        """Связь N:M: популярность тегов через промежуточную таблицу."""
        query = """
            SELECT t.name AS tag, COUNT(bt.book_id) AS books_count
            FROM tags AS t
            LEFT JOIN book_tags AS bt ON bt.tag_id = t.id
            GROUP BY t.id, t.name
            ORDER BY books_count DESC, tag
        """
        with self.database.connection() as connection:
            rows = connection.execute(query).fetchall()
        return [dict(row) for row in rows]

    def set_tags(self, book_id: int, tag_names: list[str], connection: sqlite3.Connection | None = None) -> None:
        """Переписать набор тегов книги (связь N:M через book_tags)."""
        statements = [("DELETE FROM book_tags WHERE book_id = ?", (book_id,))]
        for name in tag_names:
            statements.append(("INSERT OR IGNORE INTO tags (name) VALUES (?)", (name,)))
            statements.append(
                (
                    "INSERT OR IGNORE INTO book_tags (book_id, tag_id)"
                    " SELECT ?, id FROM tags WHERE name = ?",
                    (book_id, name),
                )
            )

        if connection is not None:
            for query, params in statements:
                connection.execute(query, params)
            return

        with self.database.connection() as own:
            for query, params in statements:
                own.execute(query, params)

    def get_tags(self, book_id: int) -> list[str]:
        query = """
            SELECT t.name
            FROM book_tags AS bt
            JOIN tags AS t ON t.id = bt.tag_id
            WHERE bt.book_id = ?
            ORDER BY t.name
        """
        with self.database.connection() as connection:
            rows = connection.execute(query, (book_id,)).fetchall()
        return [row["name"] for row in rows]


class ReaderRepository:
    """Операции над таблицей readers."""

    def __init__(self, database: Database) -> None:
        self.database = database

    def get_all(self) -> list[Reader]:
        with self.database.connection() as connection:
            rows = connection.execute("SELECT * FROM readers ORDER BY full_name").fetchall()
        return [_to_reader(row) for row in rows]

    def get_by_id(self, reader_id: int) -> Reader | None:
        with self.database.connection() as connection:
            row = connection.execute("SELECT * FROM readers WHERE id = ?", (reader_id,)).fetchone()
        return _to_reader(row) if row else None

    def get_by_email(self, email: str) -> Reader | None:
        with self.database.connection() as connection:
            row = connection.execute("SELECT * FROM readers WHERE email = ?", (email.lower(),)).fetchone()
        return _to_reader(row) if row else None

    def create(self, data: dict) -> Reader:
        query = """
            INSERT INTO readers (full_name, email, phone, registered_at)
            VALUES (?, ?, ?, ?)
        """
        with self.database.connection() as connection:
            cursor = connection.execute(
                query,
                (data["full_name"], data["email"], data.get("phone"), data["registered_at"]),
            )
            reader_id = cursor.lastrowid
        created = self.get_by_id(reader_id)
        assert created is not None
        return created

    def delete(self, reader_id: int) -> bool:
        with self.database.connection() as connection:
            cursor = connection.execute("DELETE FROM readers WHERE id = ?", (reader_id,))
            return cursor.rowcount > 0


class LoanRepository:
    """Операции над таблицей loans (выдачи книг)."""

    def __init__(self, database: Database) -> None:
        self.database = database

    def get_by_id(self, loan_id: int, connection: sqlite3.Connection | None = None) -> Loan | None:
        query = "SELECT * FROM loans WHERE id = ?"
        if connection is not None:
            row = connection.execute(query, (loan_id,)).fetchone()
        else:
            with self.database.connection() as own:
                row = own.execute(query, (loan_id,)).fetchone()
        return _to_loan(row) if row else None

    def get_active_by_book(self, book_id: int) -> list[Loan]:
        query = "SELECT * FROM loans WHERE book_id = ? AND returned_at IS NULL ORDER BY due_at"
        with self.database.connection() as connection:
            rows = connection.execute(query, (book_id,)).fetchall()
        return [_to_loan(row) for row in rows]

    def get_by_reader(self, reader_id: int) -> list[Loan]:
        """Выдачи читателя: индекс idx_loans_reader(reader_id, returned_at)."""
        query = "SELECT * FROM loans WHERE reader_id = ? ORDER BY taken_at DESC"
        with self.database.connection() as connection:
            rows = connection.execute(query, (reader_id,)).fetchall()
        return [_to_loan(row) for row in rows]

    def get_active(self) -> list[dict]:
        query = """
            SELECT l.id, b.title, r.full_name AS reader, l.taken_at, l.due_at
            FROM loans AS l
            JOIN books AS b   ON b.id = l.book_id
            JOIN readers AS r ON r.id = l.reader_id
            WHERE l.returned_at IS NULL
            ORDER BY l.due_at
        """
        with self.database.connection() as connection:
            rows = connection.execute(query).fetchall()
        return [dict(row) for row in rows]

    def get_overdue(self, today: str) -> list[dict]:
        query = """
            SELECT r.full_name AS reader, b.title, l.due_at
            FROM loans AS l
            JOIN books AS b   ON b.id = l.book_id
            JOIN readers AS r ON r.id = l.reader_id
            WHERE l.returned_at IS NULL AND l.due_at < ?
            ORDER BY l.due_at
        """
        with self.database.connection() as connection:
            rows = connection.execute(query, (today,)).fetchall()
        return [dict(row) for row in rows]

    def create(self, connection: sqlite3.Connection, book_id: int, reader_id: int, taken_at: str, due_at: str) -> int:
        query = """
            INSERT INTO loans (book_id, reader_id, taken_at, due_at, returned_at)
            VALUES (?, ?, ?, ?, NULL)
        """
        cursor = connection.execute(query, (book_id, reader_id, taken_at, due_at))
        return int(cursor.lastrowid)

    def mark_returned(self, connection: sqlite3.Connection, loan_id: int, returned_at: str) -> int:
        cursor = connection.execute(
            "UPDATE loans SET returned_at = ? WHERE id = ? AND returned_at IS NULL",
            (returned_at, loan_id),
        )
        return cursor.rowcount
