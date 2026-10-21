"""Pydantic-схемы для loans-service."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LoanCreate(BaseModel):
    reader_id: str = Field(..., min_length=1)
    book_id: str = Field(..., min_length=1)


class LoanOut(BaseModel):
    id: str
    reader_id: str
    book_id: str
    status: str
    issued_at: str