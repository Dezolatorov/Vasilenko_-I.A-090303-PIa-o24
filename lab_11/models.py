"""Модели предметной области «Библиотека»."""

from dataclasses import asdict, dataclass


@dataclass
class Author:
    """Автор книги."""

    id: int
    full_name: str
    country: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Book:
    """Книга библиотечного фонда."""

    id: int
    title: str
    author_id: int
    genre: str
    year: int
    price: float
    total_copies: int
    available_copies: int
    cover_path: str | None = None

    def to_dict(self) -> dict:
        """Представление книги для JSON-ответа."""
        data = asdict(self)
        data["price"] = round(self.price, 2)
        return data


@dataclass
class BookDetails:
    """Книга вместе с автором и тегами (результат JOIN)."""

    id: int
    title: str
    author: str
    country: str
    genre: str
    year: int
    price: float
    total_copies: int
    available_copies: int
    tags: list[str]
    cover_url: str | None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Reader:
    """Читатель библиотеки."""

    id: int
    full_name: str
    email: str
    phone: str | None
    registered_at: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Loan:
    """Выдача книги читателю."""

    id: int
    book_id: int
    reader_id: int
    taken_at: str
    due_at: str
    returned_at: str | None

    @property
    def is_active(self) -> bool:
        return self.returned_at is None

    def to_dict(self) -> dict:
        data = asdict(self)
        data["is_active"] = self.is_active
        return data
