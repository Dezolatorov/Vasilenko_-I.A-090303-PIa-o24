from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

STATUSES = ("available", "loaned", "archived")


@dataclass
class LoanEntry:
    reader: str
    loan_date: str
    due_date: str
    returned: bool = False

    def to_document(self) -> Dict[str, Any]:
        return {
            "reader": self.reader,
            "loan_date": self.loan_date,
            "due_date": self.due_date,
            "returned": self.returned,
        }

    @classmethod
    def from_document(cls, data: Dict[str, Any]) -> "LoanEntry":
        return cls(
            reader=str(data.get("reader", "")),
            loan_date=str(data.get("loan_date", "")),
            due_date=str(data.get("due_date", "")),
            returned=bool(data.get("returned", False)),
        )


@dataclass
class Book:
    title: str
    authors: List[str]
    publisher: Dict[str, Any]
    genres: List[str]
    year: int
    copies_total: int
    copies_available: int
    readers: List[LoanEntry] = field(default_factory=list)
    status: str = "available"
    id: Optional[str] = None

    def to_document(self) -> Dict[str, Any]:
        document: Dict[str, Any] = {
            "title": self.title,
            "authors": list(self.authors),
            "publisher": dict(self.publisher),
            "genres": list(self.genres),
            "year": self.year,
            "copies": {
                "total": self.copies_total,
                "available": self.copies_available,
            },
            "readers": [entry.to_document() for entry in self.readers],
            "status": self.status,
        }
        return document

    @classmethod
    def from_document(cls, document: Dict[str, Any]) -> "Book":
        copies = document.get("copies", {})
        return cls(
            id=str(document.get("_id", "")),
            title=str(document.get("title", "")),
            authors=list(document.get("authors", [])),
            publisher=dict(document.get("publisher", {})),
            genres=list(document.get("genres", [])),
            year=int(document.get("year", 0)),
            copies_total=int(copies.get("total", 0)),
            copies_available=int(copies.get("available", 0)),
            readers=[LoanEntry.from_document(item) for item in document.get("readers", [])],
            status=str(document.get("status", "available")),
        )
