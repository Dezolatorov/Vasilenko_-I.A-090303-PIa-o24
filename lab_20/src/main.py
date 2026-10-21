import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api.books import router as books_router
from .api.health import router as health_router
from .config import get_settings
from .database import engine, init_db
from .logging_config import setup_logging

setup_logging()
logger = logging.getLogger("library.main")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "starting %s v%s (engine=%s)",
        settings.app_name,
        settings.app_version,
        engine.url.drivername,
    )
    init_db()
    yield
    logger.info("application stopped")


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
    app.include_router(health_router)
    app.include_router(books_router)
    return app


app = create_app()
