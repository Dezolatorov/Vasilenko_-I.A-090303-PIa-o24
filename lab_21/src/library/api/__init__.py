"""Слой API: HTTP-обработчики FastAPI."""
from fastapi import APIRouter

from .auth_routes import router as auth_router
from .authors import router as authors_router
from .books import router as books_router
from .loans import router as loans_router
from .readers import router as readers_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(readers_router, prefix="/readers", tags=["readers"])
api_router.include_router(authors_router, prefix="/authors", tags=["authors"])
api_router.include_router(books_router, prefix="/books", tags=["books"])
api_router.include_router(loans_router, prefix="/loans", tags=["loans"])

__all__ = ["api_router"]