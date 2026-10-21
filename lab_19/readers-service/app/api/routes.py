"""HTTP-слой (эндпоинты) readers-service: REST API читателей."""

from __future__ import annotations

import logging
import os
import time

from fastapi import APIRouter, HTTPException, status

from app.models import Reader
from app.repositories import ReaderRepository
from app.schemas.schemas import ReaderCreate, ReaderOut, ReaderUpdate
from app.services import ReadersService
from shared.storage import make_storage

logger = logging.getLogger("readers-service")

router = APIRouter()

_svc = None


def init_service(storage_source: str) -> None:
    global _svc
    repo = ReaderRepository(make_storage(storage_source))
    _svc = ReadersService(repo)


def _get_svc() -> ReadersService:
    if _svc is None:
        init_service(
            os.environ.get("DATABASE_URL", os.environ.get("READERS_DB", "./data/readers.json"))
        )
    return _svc


def _out(reader: Reader) -> ReaderOut:
    return ReaderOut(**reader.to_dict())


def _log(method: str, path: str, start_ns: int) -> None:
    logger.info("%s %s status=200 duration=%.1fms", method, path, (time.perf_counter_ns() - start_ns) / 1e6)


@router.get("/health")
def health():
    return {"status": "healthy", "service": "readers-service"}


@router.get("/readers", response_model=list[ReaderOut])
def list_readers():
    start = time.perf_counter_ns()
    result = [_out(r) for r in _get_svc().list_readers()]
    _log("GET", "/readers", start)
    return result


@router.get("/readers/check/{reader_id}")
def check_reader(reader_id: str):
    """Используется loans-service и gateway для проверки читателя."""
    return _get_svc().check_reader(reader_id)


@router.get("/readers/{reader_id}", response_model=ReaderOut)
def get_reader(reader_id: str):
    reader = _get_svc().get_reader(reader_id)
    if reader is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="читатель не найден")
    return _out(reader)


@router.post("/readers", response_model=ReaderOut, status_code=status.HTTP_201_CREATED)
def create_reader(payload: ReaderCreate):
    try:
        reader = _get_svc().create_reader(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return _out(reader)


@router.put("/readers/{reader_id}", response_model=ReaderOut)
def update_reader(reader_id: str, payload: ReaderUpdate):
    reader = _get_svc().update_reader(reader_id, payload)
    if reader is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="читатель не найден")
    return _out(reader)


@router.delete("/readers/{reader_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reader(reader_id: str):
    if not _get_svc().delete_reader(reader_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="читатель не найден")
