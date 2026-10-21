# Лабораторная работа №15. Веб-приложение на Flask

Вариант 2 — «Библиотека»: сущности `Author`, `Book`, `Reader`, выдача книг через `Loan`.
Приложение сочетает HTML-интерфейс (Jinja2) и REST API.

## Запуск

```powershell
pip install -r requirements.txt
python run.py
```

- Интерфейс: http://127.0.0.1:5001
- REST API: http://127.0.0.1:5001/api/books

Тесты: `python -m pytest` (дополнительное задание, не выполнялось).

## Страницы

| URL | Назначение |
|---|---|
| `/` | главная: статистика, последние поступления, жанры |
| `/books` | каталог с поиском, фильтром по жанру и наличию, сортировкой |
| `/books/<id>` | карточка книги и её выдачи |
| `/books/create` | форма создания |
| `/books/<id>/edit` | форма редактирования |
| `/books/<id>/borrow` | выдача книги читателю |
| `/readers`, `/readers/<id>` | читатели и история выдач |

## REST API

| Метод | URL | Код |
|---|---|---|
| GET | `/api/books` | 200 |
| GET | `/api/books/<id>` | 200 / 404 |
| GET | `/api/books/search?q=` | 200 / 400 |
| GET | `/api/statistics` | 200 |
| POST | `/api/books` | 201 / 400 / 409 |
| PUT | `/api/books/<id>` | 200 / 404 |
| PATCH | `/api/books/<id>` | 200 / 404 |
| DELETE | `/api/books/<id>` | 204 / 404 |

## Структура

```
app/
├── __init__.py        create_app, логирование, обработчики ошибок
├── config.py          настройки из переменных окружения
├── database.py        engine, Session, Base
├── models/models.py   Author, Book, Reader, Loan
├── repositories/      доступ к данным через SQLAlchemy
├── services/          бизнес-логика, валидация, транзакции выдачи/возврата
├── routes/web.py      HTML-страницы
├── routes/api.py      JSON API
├── templates/         base, index, list, detail, form, borrow, readers, 404
└── static/css/        оформление
```

Настройки: `DATABASE_URL`, `SECRET_KEY`, `FLASK_ENV`, `PAGE_SIZE` (см. `.env.example`).
По умолчанию используется SQLite; для PostgreSQL достаточно изменить `DATABASE_URL`.
