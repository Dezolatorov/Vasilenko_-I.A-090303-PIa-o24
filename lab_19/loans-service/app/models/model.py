"""Доменная модель 'Выдача книги' (loans-service)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass
class Loan:
    reader_id: str
    book_id: str
    status: str
    issued_at: str
    id: str = field(default_factory=lambda: uuid.uuid4().hex)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "reader_id": self.reader_id,
            "book_id": self.book_id,
            "status": self.status,
            "issued_at": self.issued_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Loan":
        return cls(
            id=data["id"],
            reader_id=data["reader_id"],
            book_id=data["book_id"],
            status=data["status"],
            issued_at=data["issued_at"],
        )


class LoanStatus:
    ISSUED = "issued"
    RETURNED = "returned"