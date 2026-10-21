"""Консольный HTTP-клиент для REST API библиотеки."""

import argparse
import sys

import requests

DEFAULT_URL = "http://127.0.0.1:5000"


class ApiClient:
    """Обёртка над requests: методы API и разбор ответов."""

    def __init__(self, base_url: str = DEFAULT_URL, timeout: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(self, method: str, path: str, **kwargs) -> tuple[int, object]:
        url = f"{self.base_url}{path}"
        try:
            response = requests.request(method, url, timeout=self.timeout, **kwargs)
        except requests.ConnectionError:
            return 0, {"error": f"Сервер недоступен по адресу {self.base_url}", "code": "CONNECTION_ERROR"}
        if response.status_code == 204:
            return 204, None
        try:
            return response.status_code, response.json()
        except ValueError:
            return response.status_code, response.text

    def list_books(self, **params) -> tuple[int, object]:
        return self._request("GET", "/books", params=params)

    def get_book(self, book_id: int) -> tuple[int, object]:
        return self._request("GET", f"/books/{book_id}")

    def get_details(self, book_id: int) -> tuple[int, object]:
        return self._request("GET", f"/books/{book_id}/details")

    def create_book(self, payload: dict) -> tuple[int, object]:
        return self._request("POST", "/books", json=payload)

    def replace_book(self, book_id: int, payload: dict) -> tuple[int, object]:
        return self._request("PUT", f"/books/{book_id}", json=payload)

    def patch_book(self, book_id: int, payload: dict) -> tuple[int, object]:
        return self._request("PATCH", f"/books/{book_id}", json=payload)

    def delete_book(self, book_id: int) -> tuple[int, object]:
        return self._request("DELETE", f"/books/{book_id}")

    def search(self, query: str) -> tuple[int, object]:
        return self._request("GET", "/books/search", params={"q": query})

    def search_history(self, limit: int = 5) -> tuple[int, object]:
        return self._request("GET", "/books/search-history", params={"limit": limit})

    def issue_loan(self, book_id: int, reader_id: int, days: int = 14) -> tuple[int, object]:
        return self._request("POST", "/loans", json={"book_id": book_id, "reader_id": reader_id, "days": days})

    def return_loan(self, loan_id: int) -> tuple[int, object]:
        return self._request("POST", f"/loans/{loan_id}/return")

    def list_loans(self) -> tuple[int, object]:
        return self._request("GET", "/loans")

    def overdue_loans(self) -> tuple[int, object]:
        return self._request("GET", "/loans/overdue")

    def stats(self) -> tuple[int, object]:
        return self._request("GET", "/stats")

    def cache_stats(self) -> tuple[int, object]:
        return self._request("GET", "/cache/stats")

    def cache_keys(self, pattern: str = "*") -> tuple[int, object]:
        return self._request("GET", "/cache/keys", params={"pattern": pattern})

    def health(self) -> tuple[int, object]:
        return self._request("GET", "/health")


def show_book(book: dict) -> None:
    print(
        f"  #{book.get('id')} {book.get('title')} — author_id={book.get('author_id')}, "
        f"{book.get('genre')}, {book.get('year')}, {book.get('price')} руб., "
        f"экземпляров: {book.get('available_copies')}/{book.get('total_copies')}"
    )


def show(status: int, data: object) -> None:
    """Печать кода ответа и тела в удобном виде."""
    print(f"HTTP {status}")
    if data is None:
        print("(тело ответа отсутствует)")
        return
    if isinstance(data, dict) and isinstance(data.get("items"), list):
        for key, value in data.items():
            if key != "items":
                print(f"  {key}: {value}")
        print("  items:")
        for item in data["items"]:
            if isinstance(item, dict) and "title" in item:
                show_book(item)
            else:
                print(f"    {item}")
        return
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, list):
                print(f"  {key}:")
                for element in value:
                    print(f"    {element}")
            else:
                print(f"  {key}: {value}")
        return
    if isinstance(data, list):
        if not data:
            print("  [] — список пуст")
        for item in data:
            if isinstance(item, dict) and "title" in item:
                show_book(item)
            else:
                print(f"  {item}")
        return
    print(data)


def read_id(label: str = "Идентификатор книги") -> int:
    return int(input(f"{label}: ").strip())


def menu() -> None:
    client = ApiClient(parse_args().base_url)
    while True:
        print("=" * 27)
        print("      REST CLIENT (БД)")
        print("=" * 27)
        print()
        print("1. Получить список")
        print("2. Получить объект")
        print("3. Создать")
        print("4. Изменить")
        print("5. Частично изменить")
        print("6. Удалить")
        print("7. Фильтрация")
        print("8. Сортировка")
        print("9. Специализированная операция")
        print("10. Выдать книгу (транзакция)")
        print("11. Вернуть книгу (транзакция)")
        print("12. Статистика кэша")
        print("0. Выход")
        print()
        choice = input("Выберите действие: ").strip()

        if choice == "1":
            show(*client.list_books())
        elif choice == "2":
            show(*client.get_book(read_id()))
        elif choice == "3":
            show(*client.create_book({
                "title": input("Название: ").strip(),
                "author_id": int(input("Идентификатор автора: ").strip()),
                "genre": input("Жанр: ").strip(),
                "year": int(input("Год издания: ").strip()),
                "price": float(input("Цена: ").strip()),
                "total_copies": int(input("Всего экземпляров: ").strip()),
            }))
        elif choice == "4":
            book_id = read_id()
            show(*client.replace_book(book_id, {
                "title": input("Название: ").strip(),
                "author_id": int(input("Идентификатор автора: ").strip() or 1),
                "genre": input("Жанр: ").strip() or "роман",
                "year": int(input("Год издания: ").strip() or 2000),
                "price": float(input("Цена: ").strip() or 500),
                "total_copies": int(input("Всего экземпляров: ").strip() or 1),
            }))
        elif choice == "5":
            book_id = read_id()
            show(*client.patch_book(book_id, {"price": float(input("Новая цена: ").strip())}))
        elif choice == "6":
            show(*client.delete_book(read_id()))
        elif choice == "7":
            params = {}
            genre = input("Жанр (Enter — без фильтра): ").strip()
            if genre:
                params["genre"] = genre
            available = input("Только доступные (true/false, Enter — без фильтра): ").strip()
            if available:
                params["available"] = available
            show(*client.list_books(**params))
        elif choice == "8":
            field = input("Поле сортировки (title/author/year/price): ").strip() or "title"
            order = input("Порядок (asc/desc): ").strip() or "asc"
            show(*client.list_books(sort=field, order=order))
        elif choice == "9":
            print("1. Поиск по названию  2. Детали книги  3. Просроченные выдачи  4. Статистика по жанрам")
            mode = input("Вид операции: ").strip()
            if mode == "1":
                show(*client.search(input("Запрос: ").strip()))
            elif mode == "2":
                show(*client.get_details(read_id()))
            elif mode == "3":
                show(*client.overdue_loans())
            else:
                show(*client.stats())
        elif choice == "10":
            show(*client.issue_loan(read_id(), read_id("Идентификатор читателя")))
        elif choice == "11":
            show(*client.return_loan(read_id("Идентификатор выдачи")))
        elif choice == "12":
            show(*client.cache_stats())
        elif choice == "0":
            print("Завершение работы клиента.")
            return
        else:
            print("Неизвестная команда.")
        print()


def demo() -> None:
    """Сценарий демонстрации всех операций клиента без ручного ввода."""
    client = ApiClient(parse_args().base_url)

    print("=== 1. Список книг (SELECT из SQLite) ===")
    show(*client.list_books())

    print("\n=== 2. Книга с id=1 (cache-aside, промах) ===")
    show(*client.get_book(1))

    print("\n=== 3. Книга с id=1 повторно (попадание в Redis) ===")
    show(*client.get_book(1))

    print("\n=== 4. Детали книги с id=1 (JOIN автора и тегов) ===")
    show(*client.get_details(1))

    print("\n=== 5. Создание книги (INSERT) ===")
    show(*client.create_book({
        "title": "Гарри Поттер и философский камень",
        "author_id": 6,
        "genre": "фэнтези",
        "year": 1997,
        "price": 890.0,
        "total_copies": 5,
    }))

    print("\n=== 6. Полное изменение книги с id=13 (PUT) ===")
    show(*client.replace_book(13, {
        "title": "Гарри Поттер и Тайная комната",
        "author_id": 6,
        "genre": "фэнтези",
        "year": 1998,
        "price": 940.0,
        "total_copies": 4,
    }))

    print("\n=== 7. Частичное изменение книги с id=13 (PATCH, инвалидация кэша) ===")
    show(*client.patch_book(13, {"price": 899.0}))

    print("\n=== 8. Удаление книги с id=13 (DELETE) ===")
    show(*client.delete_book(13))

    print("\n=== 9. Фильтрация: жанр 'роман', только доступные ===")
    show(*client.list_books(genre="роман", available="true"))

    print("\n=== 10. Сортировка: price desc ===")
    show(*client.list_books(sort="price", order="desc"))

    print("\n=== 11. Выдача книги (транзакция INSERT + UPDATE) ===")
    show(*client.issue_loan(2, 4))

    print("\n=== 12. Возврат книги (транзакция UPDATE + UPDATE) ===")
    show(*client.return_loan(9))

    print("\n=== 13. Поиск по названию (счётчик в Redis) ===")
    show(*client.search("война"))

    print("\n=== 14. История поиска из Redis ===")
    show(*client.search_history())

    print("\n=== 15. Статистика кэша Redis ===")
    show(*client.cache_stats())

    print("\n=== Ошибка 404: книга с id=999 ===")
    show(*client.get_book(999))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HTTP-клиент библиотеки")
    parser.add_argument("--base-url", default=DEFAULT_URL, help="адрес REST API")
    parser.add_argument("--demo", action="store_true", help="выполнить демонстрационный сценарий")
    return parser.parse_args()


if __name__ == "__main__":
    try:
        if parse_args().demo:
            demo()
        else:
            menu()
    except KeyboardInterrupt:
        print("\nПрервано пользователем.")
        sys.exit(0)
