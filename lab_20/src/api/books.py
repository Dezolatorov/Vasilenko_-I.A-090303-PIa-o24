import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..repositories import BookRepository
from ..services import LibraryService
from .schemas import AuthorOut, BookCreate, BookOut, LoanCreate, LoanOut, StatsOut

logger = logging.getLogger("library.api.books")

router = APIRouter(prefix="/api", tags=["library"])

DbDep = Annotated[Session, Depends(get_db)]


def get_service(db: DbDep) -> LibraryService:
    return LibraryService(BookRepository(db))


ServiceDep = Annotated[LibraryService, Depends(get_service)]


@router.get("/books", response_model=list[BookOut])
def list_books(
    service: ServiceDep,
    q: str = Query("", description="поиск по названию"),
    available: bool = Query(False, description="только доступные"),
):
    return service.list_books(q=q, available_only=available)


@router.get("/books/{book_id}", response_model=BookOut)
def get_book(book_id: int, service: ServiceDep):
    return service.get_book(book_id)


@router.get("/authors", response_model=list[AuthorOut])
def list_authors(db: DbDep):
    return BookRepository(db).list_authors()


@router.get("/stats", response_model=StatsOut)
def stats(service: ServiceDep):
    return service.get_stats()


@router.get("/loans", response_model=list[LoanOut])
def loans(db: DbDep, active: bool = Query(False)):
    return BookRepository(db).list_loans(active_only=active)


@router.post("/books", response_model=BookOut, status_code=status.HTTP_201_CREATED)
def create_book(payload: BookCreate, service: ServiceDep):
    return service.create_book(payload.model_dump())


@router.post("/books/{book_id}/borrow", response_model=LoanOut, status_code=status.HTTP_201_CREATED)
def borrow_book(book_id: int, payload: LoanCreate, service: ServiceDep):
    return service.borrow_book(book_id, payload.reader_name, payload.days)
