from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class Calculation:
    id: int
    expression: str
    result: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Calculation":
        return cls(
            id=int(data["id"]),
            expression=str(data["expression"]),
            result=float(data["result"]),
            timestamp=str(data.get("timestamp", datetime.now().isoformat(timespec="seconds"))),
        )