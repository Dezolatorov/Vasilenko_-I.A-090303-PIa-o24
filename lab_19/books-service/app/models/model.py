"""Доменная модель 'Книга' (books-service)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass
class Book:
    title: str
    author: str
    total_copies: int
    available_copies: int
    id: str = field(default_factory=lambda: uuid.uuid4().hex)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "total_copies": self.total_copies,
            "available_copies": self.available_copies,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Book":
        return cls(
            id=data["id"],
            title=data["title"],
            author=data["author"],
            total_copies=data["total_copies"],
            available_copies=data["available_copies"],
        )


class BookAvailability:
    @staticmethod
    def is_available(book: Book) -> bool:
        return book.available_copies > 0