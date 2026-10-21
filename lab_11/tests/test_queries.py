from db import BASE_DIR, Database


def test_queries_script_executes_and_keeps_data_consistent(database: Database):
    script = (BASE_DIR / "queries.sql").read_text(encoding="utf-8")

    with database.connection() as conn:
        conn.executescript(script)
        books_total = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
        loans_total = conn.execute("SELECT COUNT(*) FROM loans").fetchone()[0]

    assert books_total == 12
    assert loans_total == 8


def test_subquery_returns_books_above_average_price(database: Database):
    with database.connection() as conn:
        rows = conn.execute(
            "SELECT title, price FROM books"
            " WHERE price > (SELECT AVG(price) FROM books)"
            " ORDER BY price DESC"
        ).fetchall()

    assert rows[0]["title"] == "Война и мир"
    assert all(row["price"] > 0 for row in rows)


def test_group_by_with_having(database: Database):
    with database.connection() as conn:
        rows = conn.execute(
            "SELECT g.name AS genre, COUNT(b.id) AS books_count"
            " FROM genres g JOIN books b ON b.genre_id = g.id"
            " GROUP BY g.id, g.name HAVING COUNT(b.id) > 1"
            " ORDER BY books_count DESC"
        ).fetchall()

    assert rows[0]["genre"] == "Роман"
    assert rows[0]["books_count"] == 5
    assert all(row["books_count"] > 1 for row in rows)


def test_left_join_keeps_books_without_loans(database: Database):
    with database.connection() as conn:
        rows = conn.execute(
            "SELECT b.title, COUNT(l.id) AS loans_count"
            " FROM books b LEFT JOIN loans l ON l.book_id = b.id"
            " GROUP BY b.id, b.title"
        ).fetchall()

    assert len(rows) == 12
    assert any(row["loans_count"] == 0 for row in rows)


def test_indexes_exist_and_are_used(database: Database):
    with database.connection() as conn:
        indexes = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index' AND name LIKE 'idx_%'"
            ).fetchall()
        }
        plan = conn.execute(
            "EXPLAIN QUERY PLAN SELECT id FROM books WHERE title = 'Война и мир'"
        ).fetchall()

    assert {"idx_books_title", "idx_books_author", "idx_loans_reader", "idx_loans_book"} <= indexes
    assert any("idx_books_title" in row["detail"] for row in plan)
