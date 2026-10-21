"""Репозиторий выдач - собственное хранилище loans-service (Database per Service)."""

from __future__ import annotations

from app.models import Loan
from shared.storage import JsonStorage


class LoanRepository:
    def __init__(self, storage: JsonStorage):
        self._storage = storage

    def all(self) -> list[Loan]:
        return [Loan.from_dict(d) for d in self._storage.all()]

    def get(self, loan_id: str) -> Loan | None:
        data = self._storage.get(loan_id)
        return Loan.from_dict(data) if data else None

    def create(self, loan: Loan) -> Loan:
        saved = self._storage.insert(loan.to_dict())
        return Loan.from_dict(saved)

    def update(self, loan_id: str, fields: dict) -> Loan | None:
        return self._storage.update(loan_id, fields)