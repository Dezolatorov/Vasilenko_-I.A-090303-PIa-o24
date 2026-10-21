from __future__ import annotations

import argparse
import sys
from typing import Any, Dict, List, Optional

from app.cache import BookCache
from app.errors import AppError
from app.mongodb import MongoDatabase
from app.redis_client import RedisCache
from app.seed import seed_database
from app.service import LibraryService

MENU = """
Библиотека - лабораторная работа №13 (MongoDB + Redis)
 1. Add (добавить книгу)
 2. Find (найти по названию)
 3. List (список книг)
 4. Search (поиск по условию)
 5. Update (изменить книгу)
 6. Delete (удалить книгу)
 7. Statistics (статистика и агрегации)
 8. Cache status (состояние кэша)
 9. Clear cache (очистить кэш)
10. Benchmark (MongoDB против Redis)
11. Borrow (выдать книгу)
12. Return (вернуть книгу)
 0. Exit
"""


def print_book(book: Dict[str, Any]) -> None:
    copies = book.get("copies", {})
    publisher = book.get("publisher", {})
    readers = book.get("readers", [])
    active = sum(1 for entry in readers if not entry.get("returned"))
    print(
        f"  {book['_id']} {book['title']} — {', '.join(book.get('authors', []))} "
        f"({book.get('genres', [])}, {book.get('year')}) | {publisher.get('name')}, {publisher.get('city')} | "
        f"экз. {copies.get('available')}/{copies.get('total')} | {book.get('status')} | выдач: {active}"
    )


def print_books(books: List[Dict[str, Any]], empty: str = "Ничего не найдено") -> None:
    if not books:
        print(f"  {empty}")
        return
    for book in books:
        print_book(book)


def show_error(error: AppError) -> None:
    print(f"  Ошибка [{error.code}]: {error}")


def demo(service: LibraryService) -> None:
    print("=" * 96)
    print("ДЕМОНСТРАЦИЯ РАБОТЫ: MongoDB + Redis + Cache-Aside")
    print("=" * 96)

    print(f"\n[1] Подключение: MongoDB={service.database.mode}, Redis={service.cache.redis.mode}")
    print(f"    индексы: {', '.join(service.prepare())}")

    print("\n[2] Список книг, сортировка по названию (первые 5)")
    print_books(service.list_books(limit=5))

    print("\n[3] Поиск по названию: 'Онегин'")
    result = service.find_by_title("Онегин")
    print(f"    найдено: {result['count']}, история поиска: {result['history']}")
    print_books(result["items"])

    print("\n[4] Фильтрация по жанру 'Фантастика', сортировка по году (убывание)")
    print_books(service.search(genre="Фантастика", limit=5)["items"])

    print("\n[5] Запрос по вложенному полю publisher.city = 'Санкт-Петербург'")
    print_books(service.by_publisher_city("Санкт-Петербург")[:3])

    print("\n[6] Запрос по элементу массива readers.reader = 'Петрова А.С.'")
    print_books(service.by_reader("Петрова А.С."))

    print("\n[7] Агрегации MongoDB")
    stats = service.statistics()
    print(f"    книг: {stats['books']}, доступных: {stats['available_books']}, "
          f"экземпляров: {stats['copies_total']} (свободно {stats['copies_available']})")
    print(f"    по статусам: {[(row['_id'], row['count']) for row in stats['by_status']]}")
    print(f"    по жанрам (топ-5): {[(row['_id'], row['books']) for row in stats['by_genre'][:5]]}")
    print(f"    топ авторов по числу экземпляров: "
          f"{[(row['_id'], row['copies']) for row in stats['top_authors'][:3]]}")

    first_id = service.list_books(limit=1)[0]["_id"]

    print("\n[8] Cache-Aside: первый запрос идёт в MongoDB, второй - из Redis")
    service.clear_cache()
    service.get_book(first_id)
    for extra in service.list_books(limit=4)[1:]:
        service.get_book(extra["_id"])
    print(f"    после 1-го запроса: TTL={service.cache.book_ttl(first_id)} c, "
          f"ключей в кэше {service.cache_info()['keys_total']}")
    service.get_book(first_id)
    service.get_book(first_id)
    hits = service.cache.hit_rate()
    print(f"    попадания/промахи: {hits['hits']}/{hits['misses']}")

    print("\n[9] Изменение книги и инвалидирование кэша")
    service.update_book(first_id, {"status": "archived"})
    print(f"    кэш после изменения существует: {service.cache.redis.exists('book:' + first_id)}")
    refreshed = service.get_book(first_id)
    print(f"    повторное чтение из MongoDB, статус: {refreshed['status']}")

    print("\n[10] Выдача и возврат книги")
    target = service.list_books(sort="title", limit=3)[2]
    borrowed = service.borrow_book(target["_id"], "Кузнецова М.В.", days=14)
    print(f"    выдана: {borrowed['title']}, свободно экземпляров: {borrowed['copies']['available']}")
    returned = service.return_book(target["_id"], "Кузнецова М.В.")
    print(f"    возвращена: {returned['title']}, свободно экземпляров: {returned['copies']['available']}")

    print("\n[11] Структуры Redis: ZSet (популярные книги), Hash (просмотры жанров), List (история)")
    service.find_by_title("Дюна")
    service.search(query="Толстой", limit=3)
    print(f"    популярные: {service.popular_books(3)}")
    print(f"    жанры: {service.cache.genre_views()}")
    print(f"    история поиска: {service.cache.search_history()}")

    print("\n[12] Benchmark: MongoDB против Redis")
    rows = service.benchmark((100, 1000, 10000))
    print(f"    {'запросов':>10} | {'MongoDB, мс':>12} | {'Redis, мс':>10} | {'MongoDB/запрос':>15} | {'Redis/запрос':>13}")
    for row in rows:
        print(
            f"    {row['count']:>10} | {row['mongo_ms']:>12.2f} | {row['redis_ms']:>10.2f} | "
            f"{row['mongo_avg_ms']:>15.4f} | {row['redis_avg_ms']:>13.4f}"
        )

    print("\n[13] Обработка ошибок")
    for action in (
        lambda: service.get_book("не-идентификатор"),
        lambda: service.get_book("64b7f0c2a1b2c3d4e5f60718"),
        lambda: service.add_book({"title": "", "authors": ["Автор"], "publisher": {"name": "АСТ"}, "genres": ["Роман"], "year": 2000, "copies_total": 1}),
        lambda: service.borrow_book(service.list_books(limit=1)[0]["_id"], ""),
    ):
        try:
            action()
        except AppError as error:
            show_error(error)

    print("\nДемонстрация завершена.")


def interactive(service: LibraryService) -> None:
    actions = {
        "1": lambda: add_book(service),
        "2": lambda: print_books(service.find_by_title(ask("Название или его часть: "))["items"]),
        "3": lambda: print_books(service.list_books(sort=ask("Поле сортировки [title]: ", str, "title"), limit=10)),
        "4": lambda: print_books(service.search(query=ask("Строка поиска (Enter - пропустить): "), genre=ask("Жанр (Enter - пропустить): ") or None)["items"]),
        "5": lambda: update_book(service),
        "6": lambda: delete_book(service),
        "7": lambda: print_statistics(service),
        "8": lambda: print_cache(service),
        "9": lambda: print(f"  очищено ключей: {service.clear_cache()}"),
        "10": lambda: print_benchmark(service),
        "11": lambda: borrow(service),
        "12": lambda: give_back(service),
    }

    while True:
        print(MENU)
        choice = input("Выберите пункт: ").strip()
        if choice == "0":
            print("Выход.")
            return
        action = actions.get(choice)
        if action is None:
            print("Неизвестный пункт меню.")
            continue
        try:
            action()
        except AppError as error:
            show_error(error)
        except (ValueError, EOFError) as error:
            print(f"  Некорректный ввод: {error}")


def ask(prompt: str, cast=str, default=None):
    raw = input(prompt).strip()
    if not raw and default is not None:
        return default
    return cast(raw)


def add_book(service: LibraryService) -> None:
    data = {
        "title": ask("Название: "),
        "authors": [item.strip() for item in ask("Авторы через запятую: ").split(",") if item.strip()],
        "publisher": {
            "name": ask("Издательство: "),
            "city": ask("Город: "),
            "year": int(ask("Год издания издательства: ", int, 2020)),
        },
        "genres": [item.strip() for item in ask("Жанры через запятую: ").split(",") if item.strip()],
        "year": ask("Год написания: ", int),
        "copies_total": ask("Всего экземпляров: ", int),
    }
    print_book(service.add_book(data))


def update_book(service: LibraryService) -> None:
    book_id = ask("id книги: ")
    field = ask("Поле (title/year/status/copies.available): ")
    raw = ask("Новое значение: ")
    value: Any = int(raw) if field in {"year", "copies.available"} else raw
    print_book(service.update_book(book_id, {field: value}))


def delete_book(service: LibraryService) -> None:
    book_id = ask("id книги: ")
    service.delete_book(book_id)
    print(f"  книга {book_id} удалена")


def borrow(service: LibraryService) -> None:
    book = service.borrow_book(ask("id книги: "), ask("Читатель: "), ask("Срок, дней [14]: ", int, 14))
    print(f"  выдана «{book['title']}», свободно {book['copies']['available']}")


def give_back(service: LibraryService) -> None:
    book = service.return_book(ask("id книги: "), ask("Читатель: "))
    print(f"  возвращена «{book['title']}», свободно {book['copies']['available']}")


def print_statistics(service: LibraryService) -> None:
    stats = service.statistics()
    print(f"  книг: {stats['books']}, экземпляров: {stats['copies_total']}, свободно: {stats['copies_available']}")
    print(f"  по статусам: {[(row['_id'], row['count']) for row in stats['by_status']]}")
    print(f"  по жанрам: {[(row['_id'], row['books']) for row in stats['by_genre'][:5]]}")
    print(f"  топ авторов: {[(row['_id'], row['copies']) for row in stats['top_authors'][:5]]}")


def print_cache(service: LibraryService) -> None:
    info = service.cache_info()
    print(f"  режим: {info['mode']}, ключей: {info['keys_total']}, кэшей книг: {info['book_keys']}")
    print(f"  попадания/промахи: {info['hits']}, история: {info['history']}")


def print_benchmark(service: LibraryService) -> None:
    for row in service.benchmark((100, 1000, 10000)):
        print(
            f"  {row['count']:>6} запросов: MongoDB {row['mongo_ms']:>8.2f} мс "
            f"({row['mongo_avg_ms']:.4f} мс/запрос), Redis {row['redis_ms']:>8.2f} мс "
            f"({row['redis_avg_ms']:.4f} мс/запрос)"
        )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Библиотека: MongoDB + Redis")
    parser.add_argument("--demo", action="store_true", help="демонстрационный сценарий")
    parser.add_argument("--reset", action="store_true", help="пересоздать коллекцию")
    parser.add_argument("--benchmark", action="store_true", help="только тест производительности")
    parser.add_argument("--force-mock", action="store_true", help="использовать mongomock и fakeredis")
    args = parser.parse_args(argv)

    database = MongoDatabase(force_mock=args.force_mock)
    cache = BookCache(RedisCache(force_mock=args.force_mock))
    service = LibraryService(database, cache)

    if args.reset or not service.repository.list(limit=1):
        count = seed_database(database)
        print(f"Коллекция заполнена: {count} документов (MongoDB={database.mode}, Redis={cache.redis.mode})")
    else:
        service.prepare()

    if args.demo:
        demo(service)
        return 0

    if args.benchmark:
        print_benchmark(service)
        return 0

    try:
        interactive(service)
    except (KeyboardInterrupt, EOFError):
        print("\nРабота завершена.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
