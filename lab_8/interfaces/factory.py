from typing import Protocol
from models.entities import LibraryItem


class ItemFactory(Protocol):
    def create(self, item_type: str, **kwargs) -> LibraryItem: ...