"""API Gateway - единая точка входа (паттерн API Gateway).

Gateway выполняет маршрутизацию запросов клиента к микросервисам,
агрегацию (создать книгу -> выдать -> проверить) и Health Check всей системы.
Клиент не знает адресов отдельных микросервисов.
"""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s gateway %(levelname)s %(message)s")
logger = logging.getLogger("gateway")

READERS_URL = os.environ.get("READERS_URL", "http://127.0.0.1:8001")
BOOKS_URL = os.environ.get("BOOKS_URL", "http://127.0.0.1:8002")
LOANS_URL = os.environ.get("LOANS_URL", "http://127.0.0.1:8003")

app = FastAPI(title="library-gateway", version="1.0.0")


@app.get("/health")
def health_lite():
    return {"status": "healthy", "service": "gateway"}


@app.get("/health/system")
def health():
    """Health Check всей системы (паттерн Service Discovery/Health Check)."""
    import httpx

    services = {
        "readers": READERS_URL,
        "books": BOOKS_URL,
        "loans": LOANS_URL,
    }
    result = {}
    with httpx.Client(timeout=1.5) as client:
        for name, url in services.items():
            try:
                r = client.get(f"{url}/health")
                result[name] = "[ok] healthy" if r.status_code == 200 else f"[fail] status={r.status_code}"
            except Exception:
                result[name] = "[fail] unavailable"
    return {"system": "healthy", "services": result}


def _proxy(path: str, method: str, url: str, body=None):
    import httpx

    with httpx.Client(timeout=5.0) as client:
        try:
            resp = client.request(method, f"{url}{path}", json=body)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"сервис недоступен ({url}): {exc}")
    return JSONResponse(status_code=resp.status_code, content=resp.json() if resp.content else {"status": "ok"})


@app.get("/readers")
def readers_list():
    return _proxy("/readers", "GET", READERS_URL)


@app.post("/readers")
async def readers_create(request: Request):
    return _proxy("/readers", "POST", READERS_URL, await request.json())


@app.get("/books")
def books_list():
    return _proxy("/books", "GET", BOOKS_URL)


@app.post("/books")
async def books_create(request: Request):
    return _proxy("/books", "POST", BOOKS_URL, await request.json())


@app.get("/loans")
def loans_list():
    return _proxy("/loans", "GET", LOANS_URL)


@app.post("/loans")
async def loans_create(request: Request):
    return _proxy("/loans", "POST", LOANS_URL, await request.json())


@app.post("/loans/{loan_id}/return")
def loan_return(loan_id: str):
    return _proxy(f"/loans/{loan_id}/return", "POST", LOANS_URL)


@app.post("/demo/borrow-book")
async def demo_borrow(request: Request):
    """Агрегирующий сценарий: убедиться, что читатель существует, и выдать ему книгу.

    Сначала проверяем читателя через readers-service, затем создаём выдачу
    через loans-service. Агрегация нескольких сервисов в одном запросе.
    """
    body = await request.json()
    reader_id = body.get("reader_id")
    book_id = body.get("book_id")
    if not reader_id or not book_id:
        raise HTTPException(status_code=400, detail="требуются reader_id и book_id")
    try:
        _proxy(f"/readers/check/{reader_id}", "GET", READERS_URL)
        return _proxy("/loans", "POST", LOANS_URL, body)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"агрегация не удалась: {exc}")


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="127.0.0.1", port=port)