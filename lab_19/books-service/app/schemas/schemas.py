"""Pydantic-схемы для books-service."""

from __future__ import annotations

from pydantic import BaseModel, Field


class BookCreate(BaseModel):
    title: str = Field(..., min_length=1)
    author: str = Field(..., min_length=1)
    total_copies: int = Field(..., gt=0)


class BookUpdate(BaseModel):
    title: str | None = None
    author: str | None = None
    total_copies: int | None = Field(None, gt=0)


class BookOut(BaseModel):
    id: str
    title: str
    author: str
    total_copies: int
    available_copies: int