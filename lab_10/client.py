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

    def create_book(self, payload: dict) -> tuple[int, object]:
        return self._request("POST", "/books", json=payload)

    def replace_book(self, book_id: int, payload: dict) -> tuple[int, object]:
        return self._request("PUT", f"/books/{book_id}", json=payload)

    def patch_book(self, book_id: int, payload: dict) -> tuple[int, object]:
        return self._request("PATCH", f"/books/{book_id}", json=payload)

    def delete_book(self, book_id: int) -> tuple[int, object]:
        return self._request("DELETE", f"/books/{book_id}")

    def search_by_author(self, author: str) -> tuple[int, object]:
        return self._request("GET", "/books/search", params={"author": author})


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
        for book in data["items"]:
            print(
                f"    #{book.get('id')} {book.get('title')} — {book.get('author')}, "
                f"{book.get('genre')}, {book.get('year')}, {book.get('price')} руб., "
                f"доступно: {book.get('available')}"
            )
        return
    if isinstance(data, dict):
        for key, value in data.items():
            print(f"  {key}: {value}")
        return
    if isinstance(data, list):
        if not data:
            print("  [] — список пуст")
        for book in data:
            if isinstance(book, dict):
                print(
                    f"  #{book.get('id')} {book.get('title')} — {book.get('author')}, "
                    f"{book.get('genre')}, {book.get('year')}, {book.get('price')} руб., "
                    f"доступно: {book.get('available')}"
                )
            else:
                print(f"  {book}")
        return
    print(data)


def read_id() -> int:
    return int(input("Идентификатор книги: ").strip())


def read_book_fields(partial: bool = False) -> dict:
    """Собрать поля книги из консольного ввода."""
    fields = [
        ("title", "Название", str),
        ("author", "Автор", str),
        ("genre", "Жанр", str),
        ("year", "Год издания", int),
        ("price", "Цена", float),
        ("available", "Доступно экземпляров", int),
    ]
    payload: dict = {}
    print("Введите значения (пустая строка — пропустить поле):")
    for name, label, cast in fields:
        raw = input(f"  {label}: ").strip()
        if not raw:
            continue
        payload[name] = cast(raw) if cast is not str else raw
    if not partial:
        missing = [label for name, label, _ in fields if name not in payload]
        if missing:
            print(f"Не заполнены обязательные поля: {', '.join(missing)}")
    return payload


def menu() -> None:
    client = ApiClient(parse_args().base_url)
    while True:
        print("=" * 25)
        print("       REST CLIENT")
        print("=" * 25)
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
        print("0. Выход")
        print()
        choice = input("Выберите действие: ").strip()

        if choice == "1":
            show(*client.list_books())
        elif choice == "2":
            show(*client.get_book(read_id()))
        elif choice == "3":
            show(*client.create_book(read_book_fields()))
        elif choice == "4":
            book_id = read_id()
            show(*client.replace_book(book_id, read_book_fields()))
        elif choice == "5":
            book_id = read_id()
            show(*client.patch_book(book_id, read_book_fields(partial=True)))
        elif choice == "6":
            show(*client.delete_book(read_id()))
        elif choice == "7":
            params = {}
            genre = input("Жанр (Enter — без фильтра): ").strip()
            if genre:
                params["genre"] = genre
            min_price = input("Минимальная цена (Enter — без фильтра): ").strip()
            if min_price:
                params["min_price"] = float(min_price)
            max_price = input("Максимальная цена (Enter — без фильтра): ").strip()
            if max_price:
                params["max_price"] = float(max_price)
            show(*client.list_books(**params))
        elif choice == "8":
            field = input("Поле сортировки (title/author/year/price): ").strip() or "title"
            order = input("Порядок (asc/desc): ").strip() or "asc"
            show(*client.list_books(sort=field, order=order))
        elif choice == "9":
            author = input("Автор: ").strip()
            show(*client.search_by_author(author))
        elif choice == "0":
            print("Завершение работы клиента.")
            return
        else:
            print("Неизвестная команда.")
        print()


def demo() -> None:
    """Сценарий демонстрации всех операций клиента без ручного ввода."""
    client = ApiClient(parse_args().base_url)

    print("=== 1. Список книг ===")
    show(*client.list_books())

    print("\n=== 2. Книга с id=1 ===")
    show(*client.get_book(1))

    print("\n=== 3. Создание книги ===")
    show(*client.create_book({
        "title": "Гарри Поттер и философский камень",
        "author": "Роулинг Дж.К.",
        "genre": "фэнтези",
        "year": 1997,
        "price": 890.0,
        "available": 5,
    }))

    print("\n=== 4. Полное изменение книги с id=6 (PUT) ===")
    show(*client.replace_book(6, {
        "title": "Гарри Поттер и Тайная комната",
        "author": "Роулинг Дж.К.",
        "genre": "фэнтези",
        "year": 1998,
        "price": 940.0,
        "available": 4,
    }))

    print("\n=== 5. Частичное изменение книги с id=6 (PATCH) ===")
    show(*client.patch_book(6, {"price": 899.0, "available": 7}))

    print("\n=== 6. Удаление книги с id=6 (DELETE) ===")
    show(*client.delete_book(6))

    print("\n=== 7. Фильтрация: жанр 'роман', цена от 700 до 1300 ===")
    show(*client.list_books(genre="роман", min_price=700, max_price=1300))

    print("\n=== 8. Сортировка: price, desc ===")
    show(*client.list_books(sort="price", order="desc"))

    print("\n=== 9. Поиск по автору: 'булгаков' ===")
    show(*client.search_by_author("булгаков"))

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
