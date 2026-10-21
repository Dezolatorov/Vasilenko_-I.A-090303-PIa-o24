"""Точка входа books-service (книги)."""

import logging
import os

import uvicorn
from fastapi import FastAPI

from app.api.routes import init_service, router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s books-service %(levelname)s %(message)s",
)
logger = logging.getLogger("books-service")

app = FastAPI(title="books-service", version="1.0.0")
app.include_router(router)


@app.on_event("startup")
def startup():
    source = os.environ.get("DATABASE_URL", os.environ.get("BOOKS_DB", "./data/books.json"))
    init_service(source)
    logger.info("books-service готов, БД=%s", source)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8002"))
    uvicorn.run(app, host="0.0.0.0", port=port)