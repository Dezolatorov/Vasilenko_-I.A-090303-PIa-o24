"""Вспомогательные функции форматирования текста ответов."""
from typing import Sequence

from database.models import Book, Loan


def format_book(b: Book) -> str:
    title = b.title or b.author_name
    author = b.author_name or "неизвестен"
    year = str(b.year) if b.year else "—"
    isbn = b.isbn or "—"
    status = f"в наличии {b.copies_available} / {b.copies_total}" if b.copies_available > 0 \
        else f"нет в наличии (всего {b.copies_total})"
    return (
        f"📕 {title}\n"
        f"Автор: {author}\n"
        f"Год: {year}\n"
        f"ISBN: {isbn}\n"
        f"Доступность: {status}"
    )


def book_catalog_text(books: Sequence[Book]) -> str:
    if not books:
        return "В каталоге нет книг."
    lines = [f"{i + 1}. {b.title} — {b.author_name} ({f'{b.copies_available} экз.' if b.copies_available > 0 else 'нет в наличии'})"
             for i, b in enumerate(books)]
    return "Каталог книг:\n\n" + "\n".join(lines)


def search_results_text(query: str, books: Sequence[Book]) -> str:
    if not books:
        return f"По запросу «{query}» ничего не найдено."
    lines = [f"{i + 1}. {b.title} — {b.author_name}" for i, b in enumerate(books)]
    return f"Найдено по запросу «{query}» ({len(books)}):\n\n" + "\n".join(lines)


def loan_text(ln: Loan) -> str:
    state = "активна" if ln.returned_at is None else f"возвращена {ln.returned_at.isoformat()}"
    return f"📖 {ln.book_title} (читатель: {ln.reader_name})\nДо: {ln.due_date.isoformat()} — {state}"


def my_loans_text(loans: Sequence[Loan]) -> str:
    if not loans:
        return "У вас пока нет выданных книг."
    lines = [loan_text(ln) for ln in loans]
    return "Ваши книги:\n\n" + "\n".join(lines)


def overdue_text(loans: Sequence[Loan]) -> str:
    if not loans:
        return "Просроченных выдач нет. ✅"
    lines = [loan_text(ln) for ln in loans]
    return f"Просроченные выдачи ({len(loans)}):\n\n" + "\n".join(lines)