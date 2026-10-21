"""Доменная модель сущности 'Читатель' (readers-service)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass
class Reader:
    """Читатель библиотеки. Каждый сервис владеет собственными данными."""
    full_name: str
    email: str
    phone: str = ""
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    active: bool = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "active": self.active,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Reader":
        return cls(
            id=data["id"],
            full_name=data["full_name"],
            email=data["email"],
            phone=data.get("phone", ""),
            active=data.get("active", True),
        )


class ReaderStatus:
    ACTIVE = "active"
    BLOCKED = "blocked"

    @classmethod
    def validity(cls, reader: Reader) -> str:
        return cls.ACTIVE if reader.active else cls.BLOCKED