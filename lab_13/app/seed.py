from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List

from app.mongodb import MongoDatabase
from app.repository import MongoBookRepository

TODAY = date.today()


def _publisher(name: str, city: str, year: int) -> Dict[str, Any]:
    return {"name": name, "city": city, "year": year}


def _loan(reader: str, days_ago: int, days_left: int, returned: bool = False) -> Dict[str, Any]:
    return {
        "reader": reader,
        "loan_date": (TODAY - timedelta(days=days_ago)).isoformat(),
        "due_date": (TODAY + timedelta(days=days_left)).isoformat(),
        "returned": returned,
    }


BOOKS: List[Dict[str, Any]] = [
    {
        "title": "Евгений Онегин",
        "authors": ["Пушкин А.С."],
        "publisher": _publisher("Эксмо", "Москва", 2020),
        "genres": ["Поэма", "Классика"],
        "year": 1833,
        "copies": {"total": 3, "available": 2},
        "readers": [_loan("Иванов И.И.", 47, -33, returned=True)],
        "status": "available",
    },
    {
        "title": "Капитанская дочка",
        "authors": ["Пушкин А.С."],
        "publisher": _publisher("АСТ", "Москва", 2019),
        "genres": ["Повесть", "Классика"],
        "year": 1836,
        "copies": {"total": 2, "available": 2},
        "readers": [],
        "status": "available",
    },
    {
        "title": "Война и мир",
        "authors": ["Толстой Л.Н."],
        "publisher": _publisher("Эксмо", "Москва", 2021),
        "genres": ["Роман", "Классика"],
        "year": 1869,
        "copies": {"total": 4, "available": 3},
        "readers": [],
        "status": "available",
    },
    {
        "title": "Анна Каренина",
        "authors": ["Толстой Л.Н."],
        "publisher": _publisher("АСТ", "Москва", 2018),
        "genres": ["Роман", "Классика"],
        "year": 1877,
        "copies": {"total": 3, "available": 3},
        "readers": [],
        "status": "available",
    },
    {
        "title": "Преступление и наказание",
        "authors": ["Достоевский Ф.М."],
        "publisher": _publisher("Азбука", "Санкт-Петербург", 2020),
        "genres": ["Роман", "Классика"],
        "year": 1866,
        "copies": {"total": 3, "available": 2},
        "readers": [],
        "status": "available",
    },
    {
        "title": "Идиот",
        "authors": ["Достоевский Ф.М."],
        "publisher": _publisher("Азбука", "Санкт-Петербург", 2019),
        "genres": ["Роман", "Классика"],
        "year": 1869,
        "copies": {"total": 2, "available": 0},
        "readers": [_loan("Петрова А.С.", 10, 4)],
        "status": "loaned",
    },
    {
        "title": "Братья Карамазовы",
        "authors": ["Достоевский Ф.М."],
        "publisher": _publisher("Эксмо", "Москва", 2022),
        "genres": ["Роман", "Классика"],
        "year": 1880,
        "copies": {"total": 2, "available": 2},
        "readers": [],
        "status": "available",
    },
    {
        "title": "Палата № 6",
        "authors": ["Чехов А.П."],
        "publisher": _publisher("АСТ", "Москва", 2017),
        "genres": ["Повесть", "Классика"],
        "year": 1892,
        "copies": {"total": 2, "available": 2},
        "readers": [],
        "status": "available",
    },
    {
        "title": "Дама с собачкой",
        "authors": ["Чехов А.П."],
        "publisher": _publisher("Азбука", "Санкт-Петербург", 2016),
        "genres": ["Рассказ", "Классика"],
        "year": 1899,
        "copies": {"total": 1, "available": 1},
        "readers": [],
        "status": "available",
    },
    {
        "title": "Мастер и Маргарита",
        "authors": ["Булгаков М.А."],
        "publisher": _publisher("АСТ", "Москва", 2023),
        "genres": ["Роман", "Мистика"],
        "year": 1967,
        "copies": {"total": 5, "available": 4},
        "readers": [_loan("Сидоров П.П.", 28, -14)],
        "status": "loaned",
    },
    {
        "title": "Собачье сердце",
        "authors": ["Булгаков М.А."],
        "publisher": _publisher("Эксмо", "Москва", 2020),
        "genres": ["Повесть", "Фантастика"],
        "year": 1925,
        "copies": {"total": 2, "available": 2},
        "readers": [],
        "status": "available",
    },
    {
        "title": "Понедельник начинается в субботу",
        "authors": ["Стругацкий А.Н.", "Стругацкий Б.Н."],
        "publisher": _publisher("АСТ", "Москва", 2021),
        "genres": ["Фантастика"],
        "year": 1965,
        "copies": {"total": 3, "available": 3},
        "readers": [],
        "status": "available",
    },
    {
        "title": "Трудно быть богом",
        "authors": ["Стругацкий А.Н.", "Стругацкий Б.Н."],
        "publisher": _publisher("Азбука", "Санкт-Петербург", 2019),
        "genres": ["Фантастика"],
        "year": 1964,
        "copies": {"total": 2, "available": 1},
        "readers": [],
        "status": "available",
    },
    {
        "title": "Пикник на обочине",
        "authors": ["Стругацкий А.Н.", "Стругацкий Б.Н."],
        "publisher": _publisher("АСТ", "Москва", 2018),
        "genres": ["Фантастика"],
        "year": 1972,
        "copies": {"total": 2, "available": 2},
        "readers": [],
        "status": "available",
    },
    {
        "title": "Дюна",
        "authors": ["Герберт Ф."],
        "publisher": _publisher("Питер", "Санкт-Петербург", 2022),
        "genres": ["Фантастика", "Эпопея"],
        "year": 1965,
        "copies": {"total": 4, "available": 3},
        "readers": [],
        "status": "available",
    },
    {
        "title": "1984",
        "authors": ["Оруэлл Дж."],
        "publisher": _publisher("АСТ", "Москва", 2020),
        "genres": ["Роман", "Антиутопия"],
        "year": 1949,
        "copies": {"total": 3, "available": 2},
        "readers": [],
        "status": "available",
    },
    {
        "title": "Скотный двор",
        "authors": ["Оруэлл Дж."],
        "publisher": _publisher("Эксмо", "Москва", 2019),
        "genres": ["Повесть", "Антиутопия"],
        "year": 1945,
        "copies": {"total": 2, "available": 2},
        "readers": [],
        "status": "available",
    },
    {
        "title": "Убийство в «Восточном экспрессе»",
        "authors": ["Кристи А."],
        "publisher": _publisher("Эксмо", "Москва", 2023),
        "genres": ["Детектив"],
        "year": 1934,
        "copies": {"total": 3, "available": 3},
        "readers": [],
        "status": "available",
    },
    {
        "title": "Десять негритят",
        "authors": ["Кристи А."],
        "publisher": _publisher("АСТ", "Москва", 2022),
        "genres": ["Детектив"],
        "year": 1939,
        "copies": {"total": 2, "available": 2},
        "readers": [],
        "status": "available",
    },
    {
        "title": "Краткая история времени",
        "authors": ["Хокинг С."],
        "publisher": _publisher("МИФ", "Москва", 2021),
        "genres": ["Наука"],
        "year": 1988,
        "copies": {"total": 2, "available": 2},
        "readers": [],
        "status": "available",
    },
    {
        "title": "Сапиенс. Краткая история человечества",
        "authors": ["Харари Ю.Н."],
        "publisher": _publisher("МИФ", "Москва", 2020),
        "genres": ["История", "Наука"],
        "year": 2011,
        "copies": {"total": 3, "available": 1},
        "readers": [_loan("Иванов И.И.", 5, 9)],
        "status": "loaned",
    },
]


def seed_database(database: MongoDatabase) -> int:
    repository = MongoBookRepository(database)
    repository.collection.delete_many({})
    for document in BOOKS:
        repository.insert(dict(document))
    repository.ensure_indexes()
    return len(BOOKS)
