# Лабораторная работа №14. REST API на FastAPI

Вариант 2 — «Библиотека», основная сущность `Book`.
REST API: CRUD, поиск, фильтрация, сортировка, пагинация, статистика, кэш Redis, OpenAPI.

## Запуск

```powershell
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- OpenAPI: http://127.0.0.1:8000/openapi.json
- Проверка: http://127.0.0.1:8000/health

Тесты:

```powershell
python -m pytest          # 21 тест
```

## Переменные окружения

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `DATABASE_URL` | `sqlite:///library_api.db` | строка подключения SQLAlchemy |
| `REDIS_URL` | `redis://localhost:6379/0` | адрес Redis |
| `APP_ENV` | `development` | окружение |
| `CACHE_TTL` | `60` | TTL кэша книги, секунд |

Если Redis недоступен, автоматически используется `fakeredis` с тем же API.

## Endpoints

| Метод | URL | Назначение | Код |
|---|---|---|---|
| GET | `/books` | список с фильтрацией, сортировкой и пагинацией | 200 |
| GET | `/books/{id}` | книга по идентификатору (кэш Redis) | 200 / 404 |
| GET | `/books/search?q=` | поиск по названию, автору, издательству, жанру | 200 |
| GET | `/books/statistics` | статистика фонда | 200 |
| POST | `/books` | создание | 201 / 409 / 422 |
| PUT | `/books/{id}` | полное обновление | 200 / 404 |
| PATCH | `/books/{id}` | частичное обновление | 200 / 404 / 422 |
| DELETE | `/books/{id}` | удаление | 204 / 404 |

Параметры списка: `genre`, `author`, `min_rating`, `sort` (`title|author|year|rating`),
`order` (`asc|desc`), `limit` (1–100), `offset`.

## Архитектура

```
Client -> FastAPI router (app/routers/books.py)
             -> BookService (app/services/book.py)
                  -> BookRepository (app/repositories/book.py)
                       -> SQLAlchemy -> SQLite/PostgreSQL
                  -> BookCache -> Redis (или fakeredis)
```

Слои разделены, SQL находится только в репозитории, зависимости передаются через `Depends()`,
настройки читаются из переменных окружения. `GET /books` реализован асинхронно
(`async def` + `run_in_threadpool`), остальные endpoints синхронные.

## Docker

```powershell
docker compose up --build
```

Поднимает API, PostgreSQL и Redis; адрес строки подключения задаётся в `docker-compose.yml`.
