# Lab 20 — Контейнеризация, CI/CD и эксплуатация Python-приложения

**Вариант 2: Библиотека** — контейнеризация приложения библиотеки и PostgreSQL,
healthcheck БД.

## Назначение приложения

REST API библиотеки: каталог книг, авторы, выдача и возврат книг, статистика.
Реализовано на **FastAPI** + **SQLAlchemy** + **PostgreSQL** (в Docker) /
**SQLite** (для локальной разработки без Docker).

## Архитектура

```
             Docker Compose
                   │
      ┌────────────┴────────────┐
      ▼                          ▼
 ┌───────────┐            ┌────────────┐
 │  Python   │            │ PostgreSQL │
 │   App     │───────────►│     DB     │
 │  FastAPI  │   network  └────────────┘
 └───────────┘            (volume postgres_data)
```

Сервисы общаются по сети Docker по имени сервиса (не `localhost`):
приложение подключается к БД по адресу `db:5432`.

## Структура проекта

```
lab_20/
├── src/
│   ├── api/            маршрутизаторы (health.py, books.py, schemas.py)
│   ├── models/         SQLAlchemy-модели (Author, Book, Loan)
│   ├── services/       бизнес-логика
│   ├── repositories/   доступ к данным
│   ├── config.py       конфигурация из переменных окружения
│   ├── database.py     engine, session, init_db
│   ├── logging_config.py  настройка системы логирования
│   └── main.py         точка входа FastAPI (lifespan)
├── tests/
│   ├── unit/           тесты бизнес-логики
│   └── integration/    тесты API
├── Dockerfile          multi-stage, non-root
├── docker-compose.yml  app + PostgreSQL (volume, healthcheck, env)
├── .dockerignore
├── .env.example        шаблон переменных окружения
├── .gitignore
├── requirements.txt
├── pytest.ini
├── pyproject.toml      настройки ruff
└── .github/workflows/ci.yml   GitHub Actions: lint → test → build
```

## Требования

- Python 3.12+ (локальный запуск) либо **Docker** + **Docker Compose**.
- Рекомендуемая версия для контейнера — `python:3.12-slim`.

## Переменные окружения

| Переменная           | Описание                                     | Пример по умолчанию   |
|----------------------|----------------------------------------------|-----------------------|
| `DATABASE_HOST`      | хост БД (`db` внутри Docker)                 | `db`                  |
| `DATABASE_PORT`      | порт БД                                      | `5432`                |
| `DATABASE_NAME`      | имя базы                                     | `library`             |
| `DATABASE_USER`      | пользователь БД                              | `library`             |
| `DATABASE_PASSWORD`  | пароль БД (**секрет**)                       | `library_password`    |
| `USE_SQLITE`         | `true` — использовать SQLite вместо PostgreSQL| `false`              |
| `LOG_LEVEL`          | уровень логирования (DEBUG..CRITICAL)        | `INFO`                |
| `SECRET_KEY`         | секрет приложения (**секрет**)               | `change-me-in-production` |

Секреты **не хранятся в исходном коде**: они задаются через окружение, файл
`.env` (только локально) или Secrets CI. Файл `.env` исключён из Git и из
`Dockerfile` контекста через `.dockerignore`.

## Запуск локально (без Docker)

```bash
python -m venv .venv
.venv\Scripts\activate            # или linux: source .venv/bin/activate
pip install -r requirements.txt

# для локального запуска без PostgreSQL используем SQLite
copy .env.example .env            # и установите USE_SQLITE=true
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000
```

Приложение будет доступно на `http://127.0.0.1:8000`, документация — на
`http://127.0.0.1:8000/docs`.

## Запуск тестов

```bash
pytest --cov=src --cov-report=term-missing
```

Тесты используют SQLite (в памяти), поэтому PostgreSQL (Docker) не требуется.

## Сборка Docker-образа

```bash
cd lab_20
cp .env.example .env       # задайте реальные значения
docker build -t library-app:latest .
docker compose build       # или через compose
```

Образ собирается в два этапа (**multi-stage**): в `builder` в отдельном
виртуальном окружении ставятся зависимости, в `runtime` копируется только готовое
окружение и код; запуск происходит от **непривилегированного пользователя** `appuser`.

## Запуск всей системы (app + PostgreSQL)

```bash
cd lab_20
cp .env.example .env
docker compose up --build
```

- Приложение: `http://localhost:8000`
- Health check приложения: `http://localhost:8000/health`
- Остановка: `docker compose down`
- Полное удаление (вместе с данными БД): `docker compose down -v`

Данные PostgreSQL хранятся в **именованном volume** `postgres_data`, поэтому
`docker compose down` / `docker compose up` их сохраняет.

## Health Check

- `GET /health` (в приложении) — возвращает `{"status":"healthy","database":"ok"}`,
  проверяет выполнение `SELECT 1` к БД.
- В `docker compose` настроены healthcheck'и и для **PostgreSQL** (`pg_isready`),
  и для **приложения** (Python-скрипт через urllib, т.к. `curl` в slim-образе отсутствует).
- Приложение стартует только после того, как БД станет `healthy` (`depends_on.condition=service_healthy`).

## Логирование

Используется стандартный модуль `logging` с уровнями DEBUG/INFO/WARNING/ERROR/CRITICAL.
Логи выводятся в stdout: время, уровень, имя логгера, сообщение.

```
2026-10-18 12:57:29 | INFO | library.service | book created: #1 Война и мир
```

Просмотр логов контейнера: `docker compose logs -f app`.

## CI/CD (GitHub Actions)

Workflow `.github/workflows/ci.yml` запускается при `push` и `pull_request`
и содержит этапы:

```
Checkout → Install → Ruff (lint) → Pytest (test, покрытие ≥ 70%) → Docker Build
```

- `lint`: `ruff check src tests`
- `test`: `pytest --cov=src --cov-fail-under=70`
- `build`: сборка образа `library-app:ci-<sha>` (запускается только после lint+test)

Если тесты завершаются ошибкой, следующие этапы (в т.ч. сборка образа)
не выполняются.

## Описание API

| Метод | Путь                     | Описание                          |
|-------|--------------------------|-----------------------------------|
| GET   | `/health`                | health check приложения и БД      |
| GET   | `/api/books`             | каталог книг (`?q=`, `?available=true`) |
| GET   | `/api/books/{id}`        | карточка книги                    |
| POST  | `/api/books`             | создание книги (автор создаётся при необходимости) |
| POST  | `/api/books/{id}/borrow` | выдача книги читателю             |
| GET   | `/api/authors`           | список авторов                    |
| GET   | `/api/stats`             | статистика (книги, авторы, выдачи)|
| GET   | `/api/loans`             | выдачи (`?active=true`)           |

## Примечание о локальной проверке

На этой машине **Docker не установлен**, поэтому:

- Проверено **локально**: запуск приложения (uvicorn + SQLite), все эндпоинты,
  health check, логирование, `ruff`, `pytest` (10 тестов, покрытие 92%).
- `Dockerfile`, `docker-compose.yml` и `ci.yml` — **готовые конфигурации** для
  окружения с Docker/CI; их корректность не проверялась реальной сборкой.
  Для проверки достаточно выполнить `docker compose up --build` на машине с Docker.