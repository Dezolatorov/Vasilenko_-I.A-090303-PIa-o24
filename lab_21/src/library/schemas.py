"""Pydantic-схемы валидации входных/выходных данных API."""
from __future__ import annotations

import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


# ---------- Auth / Users ----------

class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=128)
    password: str = Field(min_length=6, max_length=128)

    @field_validator("username")
    @classmethod
    def username_valid(cls, v: str) -> str:
        if not re.match(r"^[A-Za-z0-9_.-]+$", v):
            raise ValueError("username может содержать только латиницу, цифры и _ . -")
        return v


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ReaderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    created_at: str

    @field_validator("created_at", mode="before")
    @classmethod
    def _dt_str(cls, v):
        if hasattr(v, "isoformat"):
            return v.isoformat()
        return v


class ReaderUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=128)
    email: EmailStr | None = None


# ---------- Authors ----------

class AuthorBase(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    birth_year: int | None = Field(default=None, ge=1000, le=2026)
    biography: str | None = Field(default=None, max_length=2000)


class AuthorCreate(AuthorBase):
    pass


class AuthorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    birth_year: int | None = Field(default=None, ge=1000, le=2026)
    biography: str | None = Field(default=None, max_length=2000)


class AuthorOut(AuthorBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


# ---------- Books ----------

class BookBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    author_id: int = Field(gt=0)
    year: int = Field(ge=1000, le=2100)
    total_copies: int = Field(default=1, ge=1, le=1000)


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    author_id: int | None = Field(default=None, gt=0)
    year: int | None = Field(default=None, ge=1000, le=2100)
    total_copies: int | None = Field(default=None, ge=1, le=1000)


class BookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author_id: int
    year: int
    total_copies: int
    available_copies: int


class BookWithAuthor(BookOut):
    author_name: str = ""


# ---------- Loans ----------

class LoanCreate(BaseModel):
    book_id: int = Field(gt=0)
    issue_date: date | None = None  # по умолчанию сегодня
    loan_days: int | None = Field(default=None, ge=1, le=365)


class LoanReturn(BaseModel):
    return_date: date | None = None  # по умолчанию сегодня


class LoanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    reader_id: int
    issue_date: str
    due_date: str
    return_date: str | None
    returned: bool

    @field_validator("issue_date", "due_date", "return_date", mode="before")
    @classmethod
    def _date_str(cls, v):
        if v is None:
            return v
        return v.isoformat() if hasattr(v, "isoformat") else v


class LoanWithDetails(LoanOut):
    book_title: str = ""
    reader_username: str = ""


# ---------- Пагинация / фильтры ----------

class Page(BaseModel):
    items: list
    total: int