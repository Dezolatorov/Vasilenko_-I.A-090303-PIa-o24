from dataclasses import dataclass
from datetime import date
from models.enums import ItemType, ItemStatus, ReaderCategory


@dataclass
class LibraryItem:
    id: int
    title: str
    author: str
    year: int
    item_type: ItemType
    status: ItemStatus = ItemStatus.AVAILABLE

    def __str__(self) -> str:
        return (
            f"[{self.id}] {self.title} — {self.author} "
            f"({self.year}, {self.item_type.value}, {self.status.value})"
        )


class PrintedBook(LibraryItem):
    def __init__(self, id: int, title: str, author: str, year: int, pages: int = 100):
        super().__init__(id, title, author, year, ItemType.PRINTED_BOOK)
        self.pages = pages

    def __str__(self) -> str:
        return super().__str__() + f", {self.pages} стр."


class EBook(LibraryItem):
    def __init__(self, id: int, title: str, author: str, year: int, size_mb: float = 5.0):
        super().__init__(id, title, author, year, ItemType.EBOOK)
        self.size_mb = size_mb

    def __str__(self) -> str:
        return super().__str__() + f", {self.size_mb} МБ"


class Magazine(LibraryItem):
    def __init__(self, id: int, title: str, author: str, year: int,
                 issue: int = 1, month: str = "January"):
        super().__init__(id, title, author, year, ItemType.MAGAZINE)
        self.issue = issue
        self.month = month

    def __str__(self) -> str:
        return super().__str__() + f", выпуск №{self.issue} ({self.month})"


@dataclass
class Reader:
    id: int
    name: str
    category: ReaderCategory

    def __str__(self) -> str:
        return f"[{self.id}] {self.name} ({self.category.value})"


@dataclass
class LoanRecord:
    item_id: int
    reader_id: int
    issued_at: date
    due_at: date
    returned: bool = False