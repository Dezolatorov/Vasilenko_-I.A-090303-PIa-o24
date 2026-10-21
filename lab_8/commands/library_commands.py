from abc import ABC, abstractmethod
from datetime import date, timedelta
from typing import Optional

from models.entities import LibraryItem, Reader, LoanRecord
from models.enums import ItemStatus
from strategies.loan_strategies import strategy_for_reader


class Command(ABC):
    name: str = "command"

    @abstractmethod
    def execute(self) -> Optional[str]:
        ...


class IssueCommand(Command):
    name = "issue"

    def __init__(self, repo, item_id: int, reader: Reader):
        self.repo = repo
        self.item_id = item_id
        self.reader = reader

    def execute(self) -> str:
        item: Optional[LibraryItem] = self.repo.get(self.item_id)
        if item is None:
            raise ValueError(f"Item {self.item_id} not found")
        if item.status != ItemStatus.AVAILABLE:
            raise ValueError(f"Item {self.item_id} is not available")

        strategy = strategy_for_reader(self.reader)
        days = strategy.calculate_days(self.reader)

        item.status = ItemStatus.ISSUED
        self.repo.update(item)

        record = LoanRecord(
            item_id=item.id,
            reader_id=self.reader.id,
            issued_at=date.today(),
            due_at=date.today() + timedelta(days=days),
        )
        self.repo.add_loan(record)
        return (
            f"Выдана позиция «{item.title}» читателю {self.reader.name}. "
            f"Срок: {days} дн. (до {record.due_at})"
        )


class ReturnCommand(Command):
    name = "return"

    def __init__(self, repo, item_id: int):
        self.repo = repo
        self.item_id = item_id

    def execute(self) -> str:
        item: Optional[LibraryItem] = self.repo.get(self.item_id)
        if item is None:
            raise ValueError(f"Item {self.item_id} not found")
        if item.status != ItemStatus.ISSUED:
            raise ValueError(f"Item {self.item_id} was not issued")

        item.status = ItemStatus.AVAILABLE
        self.repo.update(item)
        self.repo.close_loan(item.id)
        return f"Возвращена позиция «{item.title}»"


class ReserveCommand(Command):
    name = "reserve"

    def __init__(self, repo, item_id: int):
        self.repo = repo
        self.item_id = item_id

    def execute(self) -> str:
        item: Optional[LibraryItem] = self.repo.get(self.item_id)
        if item is None:
            raise ValueError(f"Item {self.item_id} not found")
        if item.status != ItemStatus.AVAILABLE:
            raise ValueError(f"Item {self.item_id} cannot be reserved")

        item.status = ItemStatus.RESERVED
        self.repo.update(item)
        return f"Забронирована позиция «{item.title}»"