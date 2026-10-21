"""Pydantic-схемы для readers-service."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class ReaderCreate(BaseModel):
    full_name: str = Field(..., min_length=1, description="ФИО читателя")
    email: EmailStr
    phone: str = ""


class ReaderUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    active: bool | None = None


class ReaderOut(BaseModel):
    id: str
    full_name: str
    email: str
    phone: str
    active: bool