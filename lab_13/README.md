# Лабораторная работа №13. MongoDB и Redis

Вариант 2 — «Библиотека»: документы книг в MongoDB, Redis для кэша книги, истории поиска
и рейтинга популярных книг.

## Запуск

```powershell
pip install -r requirements.txt

python -m app.main                        # интерактивное меню
python -m app.main --demo --reset         # демонстрационный сценарий и заполнение базы
python -m app.main --benchmark            # только сравнение MongoDB и Redis
python -m pytest                          # 26 тестов
```

Серверы (необязательно, но именно они используются при наличии):

```powershell
docker compose up -d
```

Если MongoDB и Redis недоступны, приложение автоматически переходит на их
программные аналоги (`mongomock`, `fakeredis`) с тем же API — код при этом не меняется.
Режим виден в выводе демонстрации: `MongoDB=mongodb|mongomock`, `Redis=redis|fakeredis`.

## Структура

```
app/
├── models.py          документ книги и вложенной выдачи
├── mongodb.py         подключение к MongoDB и индексы
├── redis_client.py    подключение к Redis, обёртка над структурами
├── repository.py      MongoBookRepository: CRUD, запросы, агрегации
├── cache.py           BookCache: кэш книги, история, популярные книги, статистика жанров
├── service.py         бизнес-логика, Cache-Aside, инвалидирование, benchmark
├── seed.py            21 документ тестовых данных
└── main.py            CLI и режим --demo
tests/                 26 тестов: MongoDB, Redis, кэш и его инвалидирование
```

## Что реализовано

- документы с вложенным объектом `publisher`, массивами `authors`, `genres` и `readers`, статусом;
- CRUD через MongoDB, три индекса (`title`, `genres + year`, `publisher.city`);
- 12 запросов: фильтрация, сортировки, ограничение выборки, вложенные поля, элементы массивов;
- агрегации `$group`, `$unwind`, `$sum`, `$min`, `$max`, `$sort`, `$limit`;
- Redis: String (кэш JSON, счётчики), List (история поиска), Hash (просмотры жанров), Sorted Set (популярные книги);
- Cache-Aside с TTL 300 с и инвалидированием кэша при изменении и удалении;
- benchmark: 100 / 1 000 / 10 000 запросов MongoDB против Redis.
