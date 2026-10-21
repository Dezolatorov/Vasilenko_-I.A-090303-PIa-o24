# models.py
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class LoanStatus(Enum):
    ACTIVE = "Active"
    OVERDUE = "Overdue"

@dataclass
class Book:
    id: int
    title: str
    author: str
    is_borrowed: bool
    is_reserved: bool = False

@dataclass
class Reservation:
    book_id: int
    reader_id: int
    created_at: datetime

@dataclass
class Reader:
    id: int
    name: str
    email: str
    phone: str

@dataclass
class Loan:
    book_id: int
    reader_id: int
    due_date: datetime
