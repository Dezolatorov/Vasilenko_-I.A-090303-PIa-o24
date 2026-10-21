"""Сквозной демонстрационный сценарий (по методичке, раздел 30).

Регистрация -> авторизация -> каталог -> добавление автора/книги (ADMIN)
-> выдача книги (USER) -> возврат -> фильтрация/сортировка -> бизнес-правила.

Запуск: python -m src.library.demo  (из корня проекта)
Все вызовы идут через TestClient к реальному приложению.
"""
from __future__ import annotations

import io
import logging
import os
import sys
import tempfile
from contextlib import redirect_stdout
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from src.library.database import Base, get_session  # noqa: E402
from src.library.main import app  # noqa: E402


def run_demo() -> str:
    buf = io.StringIO()
    # Отключим вывод логов приложения, чтобы в отчёте был чистый сценарий
    logging.disable(logging.WARNING)
    try:
        with redirect_stdout(buf):
            return _run(buf)
    finally:
        logging.disable(logging.NOTSET)


def _run(buf: io.StringIO) -> str:
    fd, tmp = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    engine = create_engine(f"sqlite:///{tmp}",
                           connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def _override():
        db = factory()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    app.dependency_overrides[get_session] = _override
    client = TestClient(app)

    print(f"Демонстрация запущена: {date.today().isoformat()}")
    print("=" * 62)
    print("ШАГ 1. Регистрация пользователя (USER) и администратора (ADMIN)")
    print("-" * 62)
    r = client.post("/auth/register", json={
        "username": "petrov", "email": "petrov@lib.ru",
        "full_name": "Иван Петров", "password": "petrov_1"})
    user_token = r.json()["access_token"]
    print(f"  POST /auth/register petrov -> {r.status_code}, роль USER, токен получен")

    r = client.post("/auth/register", json={
        "username": "librarian", "email": "lib@lib.ru",
        "full_name": "Библиотекарь", "password": "librarian_1"})
    # Библиотекарь по умолчанию USER; для ADMIN-операций ниже используем отдельный
    # инъекцию: проще создать ADMIN прямо в БД.
    from src.library.auth import hash_password  # noqa: E402
    from src.library.models import Reader  # noqa: E402
    db = factory()
    admin = Reader(username="admin", email="admin@lib.ru", full_name="Админ",
                   hashed_password=hash_password("admin_1"), role="ADMIN")
    db.add(admin)
    db.commit()
    db.close()
    r = client.post("/auth/login", json={"username": "admin", "password": "admin_1"})
    admin_token = r.json()["access_token"]
    print(f"  POST /auth/register librarian -> {r.status_code}")
    print(f"  POST /auth/login admin -> {r.status_code}, роль ADMIN")

    print()
    print("ШАГ 2. Каталог книг (до добавления) + фильтрация доступности")
    print("-" * 62)
    r = client.get("/books", headers={"Authorization": f"Bearer {user_token}"})
    print(f"  GET /books -> {r.status_code}, найдено книг: {len(r.json())}")

    print()
    print("ШАГ 3. ADMIN добавляет авторов и книги")
    print("-" * 62)
    h = {"Authorization": f"Bearer {admin_token}"}
    a1 = client.post("/authors", headers=h, json={"name": "Александр Пушкин", "birth_year": 1799}).json()
    a2 = client.post("/authors", headers=h, json={"name": "Михаил Лермонтов", "birth_year": 1814}).json()
    b1 = client.post("/books", headers=h, json={
        "title": "Евгений Онегин", "author_id": a1["id"], "year": 1833, "total_copies": 3}).json()
    b2 = client.post("/books", headers=h, json={
        "title": "Герой нашего времени", "author_id": a2["id"], "year": 1840, "total_copies": 2}).json()
    print(f"  POST /authors Пушкин -> id={a1['id']}")
    print(f"  POST /authors Лермонтов -> id={a2['id']}")
    print(f"  POST /books 'Евгений Онегин' -> id={b1['id']}, copies={b1['total_copies']}")
    print(f"  POST /books 'Герой нашего времени' -> id={b2['id']}, copies={b2['total_copies']}")

    print()
    print("ШАГ 4. Поиск и сортировка в каталоге")
    print("-" * 62)
    r = client.get("/books", params={"title": "Онегин"},
                   headers={"Authorization": f"Bearer {user_token}"})
    print(f"  GET /books?title=Онегин -> {r.status_code}, найдено: {len(r.json())}")
    r = client.get("/books", params={"sort_by": "year", "descending": "true"},
                   headers={"Authorization": f"Bearer {user_token}"})
    titles = [b["title"] for b in r.json()]
    print(f"  GET /books?sort_by=year&desc=true (по годам убыв.) -> {titles}")

    print()
    print("ШАГ 5. USER выдаёт себе книгу (бизнес-правило: выдача)")
    print("-" * 62)
    r = client.post("/loans", json={"book_id": b1["id"]},
                    headers={"Authorization": f"Bearer {user_token}"})
    loan = r.json()
    print(f"  POST /loans book={b1['id']} -> {r.status_code}, loan_id={loan['id']}, "
          f"due={loan['due_date']}")
    r = client.get(f"/books/{b1['id']}", headers={"Authorization": f"Bearer {user_token}"})
    print(f"  GET /books/{b1['id']} -> available_copies={r.json()['available_copies']} (было 3)")

    print()
    print("ШАГ 6. Демонстрация бизнес-правила: нет свободных экземпляров")
    print("-" * 62)
    # Создаём книгу с 1 экземпляром и выдаём дважды
    b3 = client.post("/books", headers=h, json={
        "title": "Одна копия", "author_id": a1["id"], "year": 1999, "total_copies": 1}).json()
    client.post("/loans", json={"book_id": b3["id"]},
                headers={"Authorization": f"Bearer {user_token}"})
    r = client.post("/loans", json={"book_id": b3["id"]},
                    headers={"Authorization": f"Bearer {user_token}"})
    print(f"  POST /loans (повтор книги с 1 копией) -> {r.status_code}: "
          f"{r.json()['message']}")

    print()
    print("ШАГ 7. USER возвращает книгу")
    print("-" * 62)
    r = client.post(f"/loans/{loan['id']}/return", json={},
                    headers={"Authorization": f"Bearer {user_token}"})
    print(f"  POST /loans/{loan['id']}/return -> {r.status_code}, returned={r.json()['returned']}")
    r = client.get(f"/books/{b1['id']}", headers={"Authorization": f"Bearer {user_token}"})
    print(f"  GET /books/{b1['id']} -> available_copies вернулось к {r.json()['available_copies']}")

    print()
    print("ШАГ 8. Демонстрация ролей и ошибок")
    print("-" * 62)
    r = client.post("/books", json={"title": "X", "author_id": a1["id"], "year": 2000},
                    headers={"Authorization": f"Bearer {user_token}"})
    print(f"  USER пытается создать книгу (POST /books) -> {r.status_code} (должно быть 403)")
    r = client.get("/readers", headers={"Authorization": f"Bearer {user_token}"})
    print(f"  USER запрашивает список всех читателей (GET /readers) -> {r.status_code} (403)")
    r = client.get(f"/books/999999", headers={"Authorization": f"Bearer {user_token}"})
    print(f"  GET /books/999999 -> {r.status_code}: {r.json()['error']} (404)")

    print()
    print("ШАГ 9. Health check и завершение")
    print("-" * 62)
    r = client.get("/health")
    print(f"  GET /health -> {r.status_code}: {r.json()['status']}")
    print("Демонстрация завершена успешно.")
    app.dependency_overrides.clear()
    return buf.getvalue()


if __name__ == "__main__":
    print(run_demo())