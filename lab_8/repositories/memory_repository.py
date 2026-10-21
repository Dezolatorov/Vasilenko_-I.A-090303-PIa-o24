from typing import Optional
from models.entities import LibraryItem, LoanRecord


class InMemoryRepository:
    def __init__(self) -> None:
        self._items: dict[int, LibraryItem] = {}
        self._loans: list[LoanRecord] = []

    def add(self, item: LibraryItem) -> None:
        if item.id in self._items:
            raise ValueError(f"Item with id={item.id} already exists")
        self._items[item.id] = item

    def get(self, item_id: int) -> Optional[LibraryItem]:
        return self._items.get(item_id)

    def get_all(self) -> list[LibraryItem]:
        return list(self._items.values())

    def delete(self, item_id: int) -> bool:
        return self._items.pop(item_id, None) is not None

    def update(self, item: LibraryItem) -> None:
        if item.id not in self._items:
            raise ValueError(f"Item with id={item.id} not found")
        self._items[item.id] = item

    def add_loan(self, record: LoanRecord) -> None:
        self._loans.append(record)

    def get_loans(self) -> list[LoanRecord]:
        return list(self._loans)

    def close_loan(self, item_id: int) -> Optional[LoanRecord]:
        for record in reversed(self._loans):
            if record.item_id == item_id and not record.returned:
                record.returned = True
                return record
        return None