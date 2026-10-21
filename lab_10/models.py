"""Модель предметной области «Библиотека»."""

from dataclasses import asdict, dataclass


@dataclass
class Book:
    """Книга библиотечного фонда."""

    id: int
    title: str
    author: str
    genre: str
    year: int
    price: float
    available: int

    def to_dict(self) -> dict:
        """Представление книги в виде словаря для JSON-ответа."""
        return asdict(self)
