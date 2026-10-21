from typing import Protocol
from models.entities import Reader


class LoanStrategy(Protocol):
    name: str

    def calculate_days(self, reader: Reader) -> int: ...