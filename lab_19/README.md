# Лабораторная работа №19. Микросервисная архитектура Python-приложений

**Вариант 2 — «Библиотека» (микросервисы).**

Распределённое приложение на основе микросервисной архитектуры: каталог книг,
выдача книг и читатели, объединённые единым API Gateway.

## Выполнил
- **Василенко И.А**
- Группа: **ПИа-090303-о24**
- Дисциплина: Основы программирования на Python
- Дата выполнения: 18.10.2026

---

## 1. Предметная область

Библиотека. Пользователь (читатель) обращается к каталогу книг, выбирает книгу
и получает её на руки. Бизнес-процесс «выдача книги» требует:
- существование и активность читателя;
- наличие доступного экземпляра книги;
- регистрацию выдачи (событие) и возврат книги.

## 2. Выделенные микросервисы

| Сервис | Порт | Ответственность | Хранилище (Database per Service) |
|--------|------|-----------------|----------------------------------|
| **gateway** | 8000 | единая точка входа, агрегация, health-check системы | — (не хранит данные) |
| **readers-service** | 8001 | читатели, их активность | `data/readers.json` |
| **books-service** | 8002 | каталог книг, доступность экземпляров | `data/books.json` |
| **loans-service** | 8003 | выдача и возврат книг, оркестрация | `data/loans.json` |

### Обоснование границ
Сервисы выделены по зонам ответственности предметной области: читатели, каталог
книг и операции выдачи — это независимые агрегаты. Сервисы **не обращаются к
данным друг друга напрямую** — только через REST API (принцип *Database per
Service*).

## 3. Архитектурная схема

```
                         Client
                           │
                           ▼
                   ┌───────────────┐
                   │  API Gateway  │  :8000
                   └───────┬───────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
   ┌────────────┐   ┌────────────┐   ┌──────────────┐
   │  readers   │   │   books    │   │    loans     │
   │  Service   │   │  Service   │   │   Service    │
   │   :8001    │   │   :8002    │   │    :8003     │
   └─────┬──────┘   └─────┬──────┘   └──────┬───────┘
         │                │                 │
         ▼                ▼                 ▼
   readers.json     books.json         loans.json
                                     (Database per Service)
                                           │
        событие LoanCreated (Transactional Outbox)
                                           ▼
                              ┌──────────────────────┐
                              │ Файловая шина событий │
                              │  data/events/ (poll) │
                              └──────────────────────┘
                                           ▼
                              event-consumer (Notification/Audit)
```

## 4. Взаимодействие сервисов

### Синхронное — HTTP/REST
- **gateway → readers/books/loans**: маршрутизация и агрегация запросов клиента.
- **loans-service → readers-service**: `GET /readers/check/{id}` — проверка читателя.
- **loans-service → books-service**: `GET /books/check/{id}` (доступность),
  `POST /books/{id}/decrement` (резервирование), `POST /books/{id}/increment` (возврат).

### Асинхронное — событие через файловую шину (Transactional Outbox)
После успешной выдачи `loans-service` публикует событие **LoanCreated** в каталог
`data/events/`. Независимый процесс `event-consumer` опрашивает каталог (polling)
и выполняет действие (журналирование). Это честная замена брокера Kafka/RabbitMQ:
в учебной среде **отсутствуют Docker, Kafka и RabbitMQ**, поэтому вместо них
используется файловая шина (см. разд. 8 «Ограничения среды»).

## 5. Реализованные паттерны

| Паттерн | Где реализован |
|---------|----------------|
| **API Gateway** | `gateway/app.py` — единая точка входа, агрегация, `/health/system` |
| **Database per Service** | каждый сервис владеет собственным JSON-хранилищем |
| **Retry** | `shared/resilient_client.py` — ограниченные повторы, таймаут, exponential backoff |
| **Circuit Breaker** | `shared/resilient_client.py` — CLOSED → OPEN → HALF-OPEN |
| **Event-Driven Architecture** | событие LoanCreated / LoanReturned через файловую шину |
| **Transactional Outbox** | публикация события отделена от бизнес-транзакции (запись в outbox-каталог) |
| **Saga / компенсация** | `loans-service` при сбое публикации события возвращает экземпляр книги |

### Retry
При временной ошибке запрос повторяется до `max_retries=3` раз с нарастающей
задержкой (`0.3 · 2^(n-1)`). Повторяются только временные сбои (5xx, сетевые).

### Circuit Breaker
После `failure_threshold` неудач переходит в **OPEN** — запросы отклоняются без
обращения к сервису (защита от каскадного отказа). По истечении
`recovery_timeout` переходит в **HALF-OPEN** и пропускает пробный запрос.

## 6. Структура проекта

```
lab_19/
├── gateway/                  # API Gateway (порт 8000)
├── readers-service/          # читатели (порт 8001)
│   └── app/{models,schemas,repositories,services,api}
├── books-service/            # книги (порт 8002)
│   └── app/{models,schemas,repositories,services,api}
├── loans-service/            # выдача книг (порт 8003)
│   ├── app/{models,schemas,repositories,services,api}
│   └── event_delivery/consumer.py   # асинхронный consumer событий
├── shared/                   # общий код: ResilientClient, JsonStorage, FileEventBus
│   ├── resilient_client.py
│   ├── storage.py
│   └── event_bus.py
├── scripts/run_demo.py       # запуск всех сервисов + сценарий демонстрации
├── data/                     # JSON-хранилища и события (создаются при запуске)
├── requirements.txt
└── README.md
```

## 7. API сервисов

### REST (правильные HTTP-коды: 200/201/204/400/404/409/503)

**gateway** (`:8000`)
```
GET  /health                    — статус gateway
GET  /health/system             — health-check всей системы
GET  /readers                   — список читателей
POST /readers                   — создать читателя (201)
GET  /books                     — список книг
POST /books                     — добавить книгу (201)
GET  /loans                     — список выдач
POST /loans                     — выдать книгу (201)
POST /loans/{id}/return         — вернуть книгу
POST /demo/borrow-book          — агрегированный сценарий (проверка + выдача)
```

**readers-service** (`:8001`)
```
GET /health | GET/POST /readers | GET/PUT/DELETE /readers/{id}
GET /readers/check/{id}         — проверка существования и активности читателя
```

**books-service** (`:8002`)
```
GET /health | GET/POST /books | GET/PUT/DELETE /books/{id}
GET /books/check/{id}           — доступность книги
POST /books/{id}/decrement      — резервирование экземпляра (409, если нет)
POST /books/{id}/increment      — возврат экземпляра в фонд
```

**loans-service** (`:8003`)
```
GET /health | GET/POST /loans | GET /loans/{id}
POST /loans/{id}/return
GET /events                     — события файловой шины
```

Каждый сервис имеет `GET /health` (Health Check). Логирование ведётся в консоль
в формате: `timestamp service method endpoint status duration`.

## 8. Запуск и демонстрация

### Требования
- Python 3.11+ (в среде — Python 3.14)
- Установленные пакеты (см. `requirements.txt`): fastapi, uvicorn, httpx, pydantic, pytest

### Автоматический запуск всех сервисов и сценария
```bash
cd C:\elkin\lab_19
python scripts\run_demo.py
```
Скрипт:
1. запускает 4 сервиса отдельными процессами на портах 8000–8003;
2. выполняет полный сценарий через API Gateway (создать читателя → добавить книгу →
   проверить доступность → выдать → получить событие → вернуть);
3. останавливает books-service и демонстрирует работу Circuit Breaker / Retry;
4. сохраняет результаты в `lab19-report-data/` (`demo.txt`, `tests.txt`, `service-*.log`).

### Запуск вручную (отдельные процессы)
```bash
# терминал 1 — читатели
cd C:\elkin\lab_19\readers-service
$env:PYTHONPATH="C:\elkin\lab_19"; python -m app.main
# терминал 2 — книги  (порт 8002)
# терминал 3 — выдача (порт 8003, указывает на читателей и книги)
# терминал 4 — gateway (порт 8000)
```

### Запуск тестов
```bash
cd C:\elkin\lab_19\readers-service; python -m pytest tests -q
cd C:\elkin\lab_19\books-service;   python -m pytest tests -q
cd C:\elkin\lab_19\loans-service;   python -m pytest tests -q
```
Минимальный объём по методичке: 8 тестов на сервис (5 unit + 2 интеграционных +
1 межсервисной/недоступность) → 24 теста. В проекте: **31 тест** (10+10+11),
включая тесты недоступности сервиса и Circuit Breaker.

## 9. Ограничения среды (честное описание)

Методичка предписывает Docker Compose (`docker compose up --build`) и брокер
сообщений (Kafka/RabbitMQ). В учебной среде **отсутствуют Docker, mongod,
redis-сервер, Kafka и RabbitMQ**, поэтому:

1. **Вместо Docker Compose** сервисы запускаются независимыми Python-процессами
   на разных портах (это соответствует требованию «запускаемый независимо от
   других сервисов»). Такая замена не меняет архитектуру.
2. **Вместо Kafka/RabbitMQ** реализована файловая шина событий (Transactional
   Outbox): событие записывается в каталог `data/events/`, consumer опрашивает
   его. Это демонстрирует асинхронное взаимодействие Service → Broker → Consumer.
3. **Базы данных** — отдельные JSON-хранилища (по одному файлу на сервис) вместо
   PostgreSQL: принцип Database per Service соблюдён (изоляция данных), без
   внешних СУБД.

Все замены архитектурно эквивалентны и позволяют продемонстрировать требуемые
паттерны, не нарушая методику.