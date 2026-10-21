"""Слой хранения данных: библиотечный фонд в памяти процесса."""

from models import Book


class BookRepository:
    """Хранилище книг в памяти с автоматической нумерацией идентификаторов."""

    def __init__(self, books: list[Book] | None = None) -> None:
        self._books: dict[int, Book] = {}
        self._next_id: int = 1
        for book in books or []:
            self.create(book)

    def get_all(self) -> list[Book]:
        return list(self._books.values())

    def get_by_id(self, book_id: int) -> Book | None:
        return self._books.get(book_id)

    def create(self, book: Book) -> Book:
        book.id = self._next_id
        self._books[book.id] = book
        self._next_id += 1
        return book

    def update(self, book: Book) -> Book:
        if book.id not in self._books:
            raise KeyError(book.id)
        self._books[book.id] = book
        return book

    def delete(self, book_id: int) -> bool:
        return self._books.pop(book_id, None) is not None

    def count(self) -> int:
        return len(self._books)
