"""Точка входа FastAPI-приложения LibraryAPI."""
from __future__ import annotations

import logging
import time

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .api import api_router
from .config import settings
from .database import engine, init_db
from .exceptions import DomainError, ErrorResponse
from .utils.logging import get_logger

logger = get_logger("libraryapi.main")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description="Система управления библиотекой: читатели, авторы, книги, выдачи.",
        docs_url="/swagger",
        openapi_url="/swagger/openapi.json",
    )

    init_db()
    logger.info("Приложение %s запущено (DB: %s)", settings.app_name, settings.database_url)

    # --- Централизованная обработка доменных ошибок ---
    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError):
        resp = ErrorResponse(exc.code, exc.message, exc.status_code)
        logger.warning("%s %s -> %s %s",
                       request.method, request.url.path, exc.code, exc.message)
        return JSONResponse(status_code=exc.status_code, content=resp.to_dict())

    # --- Обработка ошибок валидации FastAPI/Pydantic ---
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        message = "Параметры запроса некорректны"
        logger.warning("ValidationError %s %s: %s",
                       request.method, request.url.path, exc.errors()[:3])
        return JSONResponse(
            status_code=422,
            content={"error": "VALIDATION_ERROR", "message": message},
        )

    # --- Единый обработчик непредвиденных исключений (без traceback клиенту) ---
    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception):
        logger.exception("Необработанная ошибка %s %s: %s",
                         request.method, request.url.path, exc)
        return JSONResponse(
            status_code=500,
            content={"error": "INTERNAL_SERVER_ERROR",
                     "message": "Внутренняя ошибка сервера"},
        )

    # --- Логирование HTTP-запросов ---
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            raise
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s status=%s duration=%.0fms",
            request.method, request.url.path, response.status_code, duration_ms,
        )
        return response

    # --- Health check ---
    @app.get("/health", tags=["system"], summary="Проверка работоспособности")
    def health():
        return {"status": "healthy"}

    app.include_router(api_router)
    return app


app = create_app()