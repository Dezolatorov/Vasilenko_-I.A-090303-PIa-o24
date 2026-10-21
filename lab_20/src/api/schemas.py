from datetime import date

from pydantic import BaseModel, Field


class AuthorOut(BaseModel):
    id: int
    full_name: str


class BookOut(BaseModel):
    id: int
    title: str
    author_id: int
    year: int
    isbn: str
    copies_total: int
    copies_available: int
    description: str

    model_config = {"from_attributes": True}


class BookCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    author_name: str = Field(min_length=1, max_length=150)
    year: int = Field(ge=1400, le=2100)
    isbn: str = Field(min_length=10, max_length=13)
    copies_total: int = Field(ge=1)
    description: str = ""


class LoanCreate(BaseModel):
    reader_name: str = Field(min_length=1, max_length=150)
    days: int = Field(default=14, ge=1, le=365)


class LoanOut(BaseModel):
    id: int
    book_id: int
    reader_name: str
    loan_date: date
    due_date: date
    returned: bool

    model_config = {"from_attributes": True}


class StatsOut(BaseModel):
    total_books: int
    active_loans: int
    authors: int


class HealthOut(BaseModel):
    status: str
    database: str
