from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

ISBN_PATTERN = r"^(?:\d{10}|\d{13})$"


class BookCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200, examples=["Война и мир"])
    author: str = Field(min_length=1, max_length=120, examples=["Толстой Л.Н."])
    genre: str = Field(min_length=1, max_length=60, examples=["Роман"])
    year: int = Field(ge=1400, le=2100, examples=[1869])
    isbn: str = Field(pattern=ISBN_PATTERN, examples=["9785000000001"])
    publisher: str = Field(min_length=1, max_length=120, examples=["Эксмо"])
    copies_total: int = Field(ge=0, examples=[4])
    copies_available: Optional[int] = Field(default=None, ge=0)
    rating: float = Field(ge=0, le=5, examples=[4.8])

    @model_validator(mode="after")
    def check_copies(self) -> "BookCreate":
        if self.copies_available is None:
            object.__setattr__(self, "copies_available", self.copies_total)
        if self.copies_available > self.copies_total:
            raise ValueError("copies_available cannot exceed copies_total")
        return self


class BookUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    author: Optional[str] = Field(default=None, min_length=1, max_length=120)
    genre: Optional[str] = Field(default=None, min_length=1, max_length=60)
    year: Optional[int] = Field(default=None, ge=1400, le=2100)
    isbn: Optional[str] = Field(default=None, pattern=ISBN_PATTERN)
    publisher: Optional[str] = Field(default=None, min_length=1, max_length=120)
    copies_total: Optional[int] = Field(default=None, ge=0)
    copies_available: Optional[int] = Field(default=None, ge=0)
    rating: Optional[float] = Field(default=None, ge=0, le=5)


class BookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author: str
    genre: str
    year: int
    isbn: str
    publisher: str
    copies_total: int
    copies_available: int
    rating: float


class BookListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[BookResponse]


class BookStatistics(BaseModel):
    total: int
    average_rating: float
    max_rating: float
    total_copies: int
    by_genre: Dict[str, int]
