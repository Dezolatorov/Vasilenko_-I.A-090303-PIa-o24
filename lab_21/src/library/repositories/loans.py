"""Репозиторий выдач (loans)."""
from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Loan
from .base import BaseRepository


class LoanRepository(BaseRepository[Loan]):
    model = Loan

    def __init__(self, db: Session):
        super().__init__(db)

    def count_active_for_reader(self, reader_id: int) -> int:
        return self.db.scalar(
            select(func.count(Loan.id)).where(
                Loan.reader_id == reader_id,
                Loan.returned.is_(False),
            )
        ) or 0

    def list_active_for_reader(self, reader_id: int) -> list[Loan]:
        return list(
            self.db.scalars(
                select(Loan)
                .where(Loan.reader_id == reader_id, Loan.returned.is_(False))
                .order_by(Loan.issue_date)
            ).all()
        )

    def filter(
        self, reader_id: int | None = None, book_id: int | None = None,
        returned: bool | None = None
    ) -> list[Loan]:
        stmt = select(Loan)
        if reader_id is not None:
            stmt = stmt.where(Loan.reader_id == reader_id)
        if book_id is not None:
            stmt = stmt.where(Loan.book_id == book_id)
        if returned is not None:
            stmt = stmt.where(Loan.returned.is_(returned))
        return list(self.db.scalars(stmt.order_by(Loan.issue_date.desc())).all())

    def has_overdue(self, reader_id: int, today: date) -> bool:
        return self.db.scalar(
            select(func.count(Loan.id)).where(
                Loan.reader_id == reader_id,
                Loan.returned.is_(False),
                Loan.due_date < today,
            )
        ) or 0