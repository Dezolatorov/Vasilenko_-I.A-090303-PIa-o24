"""Точка входа loans-service (выдача книг)."""

import logging
import os

import uvicorn
from fastapi import FastAPI

from app.api.routes import init_service, router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s loans-service %(levelname)s %(message)s",
)
logger = logging.getLogger("loans-service")

app = FastAPI(title="loans-service", version="1.0.0")
app.include_router(router)


@app.on_event("startup")
def startup():
    init_service(
        os.environ.get("DATABASE_URL", os.environ.get("LOANS_DB", "./data/loans.json")),
        os.environ.get("READERS_URL", "http://127.0.0.1:8001"),
        os.environ.get("BOOKS_URL", "http://127.0.0.1:8002"),
        os.environ.get("EVENTS_DIR", "./events"),
        int(os.environ.get("CIRCUIT_FAILURES", "2")),
        float(os.environ.get("CIRCUIT_TIMEOUT", "2.0")),
        os.environ.get("BROKER_URL"),
    )
    logger.info("loans-service готов")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8003"))
    uvicorn.run(app, host="0.0.0.0", port=port)