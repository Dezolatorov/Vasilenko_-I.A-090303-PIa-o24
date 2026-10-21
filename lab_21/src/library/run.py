"""Точка запуска dev-сервера: python -m src.library.run"""
import uvicorn

from .config import settings

if __name__ == "__main__":
    uvicorn.run(
        "src.library.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )