from repositories.memory_repository import InMemoryRepository
from services.library_service import LibraryService
from ui.console import ConsoleUI
from models.enums import ItemType


def seed(service: LibraryService) -> None:
    service.add_item(ItemType.PRINTED_BOOK, id=1, title="Война и мир",
                     author="Л. Толстой", year=1869)
    service.add_item(ItemType.PRINTED_BOOK, id=2, title="Преступление и наказание",
                     author="Ф. Достоевский", year=1866)
    service.add_item(ItemType.EBOOK, id=3, title="Clean Code",
                     author="R. Martin", year=2008)
    service.add_item(ItemType.MAGAZINE, id=4, title="Наука и жизнь",
                     author="Редакция", year=2024)


def main() -> None:
    repo = InMemoryRepository()
    service = LibraryService(repo)
    seed(service)
    ConsoleUI(service).run()


if __name__ == "__main__":
    main()