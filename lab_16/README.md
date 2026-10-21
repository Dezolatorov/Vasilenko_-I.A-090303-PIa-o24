# Лабораторная работа №16. Веб-приложение на Django

Вариант 2 — «Библиотека»: модели `Book`, `Author`, `Reader`, `Loan` (+ `Genre` со связью many-to-many).

## Запуск

```powershell
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

- Сайт: http://127.0.0.1:8000/
- Админка: http://127.0.0.1:8000/admin/
- Демо-доступ: `admin / admin12345` (администратор), `reader / reader12345` (читатель)

Тесты:

```powershell
python manage.py test
```

## Возможности

- каталог книг: поиск (название, автор, ISBN), фильтры по жанру и наличию, сортировка по названию, году, цене, автору;
- пагинация по 10 книг;
- карточка книги с историей выдач и отметкой просрочки;
- CRUD книг (создание, изменение, удаление) — только для администратора;
- выдача и возврат книги с изменением количества доступных экземпляров;
- страницы читателей и история выдач;
- статистика: количество книг, доступных, средняя цена, просроченные выдачи, распределение по жанрам;
- авторизация средствами Django, разграничение доступа (is_staff), CSRF в формах;
- админ-панель с настройкой list_display, search_fields, list_filter, inline-выдачами.

## Структура

```
lab_16/
├── manage.py
├── config/            settings, urls, wsgi
├── library/
│   ├── models.py      Author, Genre, Book, Reader, Loan
│   ├── forms.py       BookForm, LoanForm с валидацией
│   ├── views.py       FBV + CBV (ListView, DetailView, Create/Update/Delete)
│   ├── urls.py
│   ├── admin.py
│   ├── tests.py       21 тест
│   └── management/commands/seed_demo.py
├── templates/         base, index, список, карточка, формы, статистика, читатели
└── static/css/style.css
```

База по умолчанию — SQLite; для PostgreSQL достаточно изменить `DATABASES` в `config/settings.py`.
