from __future__ import annotations

import logging
import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import SessionLocal, create_tables
from app.errors import AppError
from app.routers import books
from app.seed import seed_database

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("library.api")


def create_app(with_seed: bool = True) -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description="REST API библиотеки: CRUD книг, поиск, фильтрация, сортировка, пагинация и статистика.",
    )
    application.include_router(books.router)

    @application.middleware("http")
    async def log_requests(request: Request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        elapsed = (time.perf_counter() - started) * 1000
        logger.info(
            "%s %s -> %s (%.1f ms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed,
        )
        return response

    @application.exception_handler(AppError)
    async def handle_app_error(request: Request, error: AppError):
        logger.warning("%s %s -> %s", request.method, request.url.path, error.code)
        return JSONResponse(
            status_code=error.status_code,
            content={"detail": error.message, "code": error.code},
        )

    @application.get("/health", tags=["service"], summary="Проверка работоспособности")
    def health():
        from app.deps import cache

        return {"status": "ok", "env": settings.app_env, "cache": cache.mode}

    if with_seed:
        create_tables()
        with SessionLocal() as session:
            seed_database(session)

    return application


app = create_app()
