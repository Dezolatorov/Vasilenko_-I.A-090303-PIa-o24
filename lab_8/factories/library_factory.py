from models.entities import LibraryItem, PrintedBook, EBook, Magazine
from models.enums import ItemType


class LibraryItemFactory:
    _registry = {
        ItemType.PRINTED_BOOK: PrintedBook,
        ItemType.EBOOK: EBook,
        ItemType.MAGAZINE: Magazine,
    }

    @staticmethod
    def create(item_type: ItemType, **kwargs) -> LibraryItem:
        cls = LibraryItemFactory._registry.get(item_type)
        if cls is None:
            raise ValueError(f"Unknown item type: {item_type}")
        return cls(**kwargs)