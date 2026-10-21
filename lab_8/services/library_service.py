from interfaces.repository import Repository
from models.entities import LibraryItem, Reader
from models.enums import ItemType, ItemStatus
from factories.library_factory import LibraryItemFactory
from commands.library_commands import IssueCommand, ReturnCommand, ReserveCommand


class LibraryService:
    def __init__(self, repository: Repository):
        self.repository = repository

    def add_item(self, item_type: ItemType, **kwargs) -> LibraryItem:
        item = LibraryItemFactory.create(item_type, **kwargs)
        self.repository.add(item)
        return item

    def list_items(self) -> list[LibraryItem]:
        return self.repository.get_all()

    def find_by_author(self, author: str) -> list[LibraryItem]:
        return [i for i in self.repository.get_all()
                if author.lower() in i.author.lower()]

    def find_by_title(self, query: str) -> list[LibraryItem]:
        return [i for i in self.repository.get_all()
                if query.lower() in i.title.lower()]

    def filter_by_status(self, status: ItemStatus) -> list[LibraryItem]:
        return [i for i in self.repository.get_all() if i.status == status]

    def issue(self, item_id: int, reader: Reader) -> str:
        return IssueCommand(self.repository, item_id, reader).execute()

    def return_item(self, item_id: int) -> str:
        return ReturnCommand(self.repository, item_id).execute()

    def reserve(self, item_id: int) -> str:
        return ReserveCommand(self.repository, item_id).execute()

    def loan_history(self) -> list:
        return self.repository.get_loans()

    def statistics(self) -> dict:
        items = self.repository.get_all()
        return {
            "total": len(items),
            "available": sum(1 for i in items if i.status == ItemStatus.AVAILABLE),
            "issued": sum(1 for i in items if i.status == ItemStatus.ISSUED),
            "reserved": sum(1 for i in items if i.status == ItemStatus.RESERVED),
        }