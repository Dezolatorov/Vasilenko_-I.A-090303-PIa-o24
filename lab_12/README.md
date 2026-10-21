# Лабораторная работа №12. SQLAlchemy 2.x и ORM

Вариант 2 — «Библиотека»: сущности `Reader`, `Book`, `Loan`, операции выдачи и возврата книги.

## Запуск

```powershell
pip install -r requirements.txt

python -m app.main                 # интерактивное меню
python -m app.main --demo          # демонстрационный сценарий
python -m app.main --demo --reset  # пересоздать БД и заполнить тестовыми данными
```

По умолчанию используется SQLite (`sqlite:///library.db`). Для PostgreSQL задайте строку подключения:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/library"
python -m app.main
```

Смена СУБД не требует правок в коде: модели и запросы одинаковы.
Журнал SQL включается переменной `SQL_ECHO=1`.

## Структура

```
app/
├── database.py            Engine, DeclarativeBase, фабрика сессий
├── errors.py              доменные исключения
├── seed.py                тестовые данные (8 книг, 5 читателей, 3 выдачи)
├── main.py                консольное меню и режим --demo
├── models/entities.py     ORM-модели Reader, Book, Loan
├── repositories/          доступ к данным через select()/Session
└── services/              бизнес-логика, валидация, транзакции
```

Слои: `main → LibraryService → Repository → Session → БД`. Прямой SQL для основных операций не используется.

## Что реализовано

- CRUD книг и читателей через ORM;
- получение книги по id и списка книг;
- поиск по названию, автору и жанру (`ilike`, `or_`);
- фильтрация по цене и наличию экземпляров;
- две сортировки: по названию и по цене (ASC/DESC);
- связи: выдачи читателя, активные и просроченные выдачи (`relationship`, `selectinload`);
- транзакция выдачи книги (`UPDATE books` + `INSERT loans`) и возврата с `rollback()` при ошибке;
- агрегаты: `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`;
- обработка ошибок: отсутствие объекта, дубликат e-mail, нарушение FK, ошибка транзакции, некорректные данные.
