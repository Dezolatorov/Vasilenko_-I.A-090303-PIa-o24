"""Роутер выдач: /loans - выдача и возврат книг."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..auth import get_current_reader, require_admin, require_user
from ..database import get_session
from ..exceptions import AuthorizationException
from ..models import Reader
from ..schemas import (LoanCreate, LoanOut, LoanReturn)
from ..services import LoanService
from .deps import get_loan_service

router = APIRouter()


@router.post(
    "",
    response_model=LoanOut,
    status_code=201,
    summary="Выдать книгу читателю",
)
def issue_loan(
    data: LoanCreate,
    service: LoanService = Depends(get_loan_service),
    current: Reader = Depends(require_user),
) -> LoanOut:
    loan = service.issue(current, data)
    return LoanOut.model_validate(loan)


@router.post(
    "/{loan_id}/return",
    response_model=LoanOut,
    summary="Вернуть книгу",
)
def return_loan(
    loan_id: int,
    data: LoanReturn,
    service: LoanService = Depends(get_loan_service),
    current: Reader = Depends(require_user),
) -> LoanOut:
    loan = service.get(loan_id)
    if current.role != "ADMIN" and loan.reader_id != current.id:
        raise AuthorizationException("Нельзя возвращать чужую выдачу")
    loan = service.return_loan(loan_id, data)
    return LoanOut.model_validate(loan)


@router.get(
    "",
    response_model=list[LoanOut],
    summary="Список выдач (фильтр по читателю/книге/статусу)",
)
def list_loans(
    reader_id: int | None = Query(default=None),
    book_id: int | None = Query(default=None),
    returned: bool | None = Query(default=None),
    view: str = Query(default="own", pattern="^(own|all)$"),
    service: LoanService = Depends(get_loan_service),
    current: Reader = Depends(get_current_reader),
) -> list[LoanOut]:
    if view == "all" and current.role == "ADMIN":
        pass  # ADMIN видит все
    elif reader_id is not None and reader_id != current.id and current.role != "ADMIN":
        raise AuthorizationException("Нет доступа к чужим выдачам")
    elif reader_id is None:
        reader_id = current.id
    loans = service.filter(reader_id=reader_id, book_id=book_id, returned=returned)
    return [LoanOut.model_validate(l) for l in loans]


@router.get("/{loan_id}", response_model=LoanOut, summary="Выдача по id")
def get_loan(
    loan_id: int,
    service: LoanService = Depends(get_loan_service),
    current: Reader = Depends(get_current_reader),
) -> LoanOut:
    loan = service.get(loan_id)
    if current.role != "ADMIN" and loan.reader_id != current.id:
        raise AuthorizationException("Нет доступа к чужой выдаче")
    return LoanOut.model_validate(loan)