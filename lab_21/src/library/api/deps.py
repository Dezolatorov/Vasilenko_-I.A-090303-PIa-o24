"""Зависимости для API: фабрики сервисов на сессии БД."""
from fastapi import Depends
from sqlalchemy.orm import Session

from ..database import get_session
from ..services import (
    AuthService,
    AuthorService,
    BookService,
    LoanService,
    ReaderService,
)


def get_auth_service(db: Session = Depends(get_session)) -> AuthService:
    return AuthService(db)


def get_reader_service(db: Session = Depends(get_session)) -> ReaderService:
    return ReaderService(db)


def get_author_service(db: Session = Depends(get_session)) -> AuthorService:
    return AuthorService(db)


def get_book_service(db: Session = Depends(get_session)) -> BookService:
    return BookService(db)


def get_loan_service(db: Session = Depends(get_session)) -> LoanService:
    return LoanService(db)