import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..database import get_db
from .schemas import HealthOut

logger = logging.getLogger("library.api.health")

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
def health(db: Annotated[Session, Depends(get_db)]):
    """Health check: при недоступной БД возвращает 503, чтобы Docker это видел."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:  # pragma: no cover
        logger.error("health check failed: %s", exc)
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": "error"},
        )
    return HealthOut(status="healthy", database="ok")
