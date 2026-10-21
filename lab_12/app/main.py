from __future__ import annotations

import argparse
import sys
from decimal import Decimal, InvalidOperation
from typing import Callable, Optional

from app.database import Database
from app.errors import AppError
from app.seed import seed_database
from app.services.services import LibraryService

MENU = """
Библиотека - лабораторная работа №12 (SQLAlchemy ORM)
 1. Каталог книг (сортировка по названию)
 2. Сортировка по цене (по убыванию)
 3. Фильтр: книги до 600 руб. в наличии
 4. Поиск по названию, автору или жанру
 5. Книга по id
 6. Добавить книгу
 7. Изменить цену книги
 8. Удалить книгу
 9. Список читателей
10. Добавить читателя
11. Выдать книгу
12. Вернуть книгу
13. Выдачи читателя
14. Просроченные выдачи
15. Статистика
 0. Выход
"""


def money(value: Decimal) -> str:
    return f"{value:.2f}"


def print_book(book) -> None:
    print(
        f"  #{book.id:<3} {book.title} - {book.author} ({book.genre}, {book.year}) | "
        f"{money(book.price)} руб. | экз. {book.copies_available}/{book.copies_total}"
    )


def print_books(books, empty: str = "Ничего не найдено") -> None:
    if not books:
        print(f"  {empty}")
        return
    for book in books:
        print_book(book)


def print_loan_row(row: dict) -> None:
    returned = row["return_date"].isoformat() if row["return_date"] else "не возвращена"
    print(
        f"  выдача #{row['id']}: {row['book']} | читатель {row['reader']} | "
        f"выдана {row['loan_date']} | срок {row['due_date']} | {returned}"
    )


def show_error(error: AppError) -> None:
    print(f"  Ошибка [{error.code}]: {error}")


def ask(prompt: str, cast: Callable[[str], object] = str, default=None):
    raw = input(prompt).strip()
    if not raw and default is not None:
        return default
    return cast(raw)


def demo(service: LibraryService) -> None:
    print("=" * 78)
    print("ДЕМОНСТРАЦИЯ РАБОТЫ ПРИЛОЖЕНИЯ")
    print("=" * 78)

    print("\n[1] Каталог книг, сортировка по названию")
    print_books(service.list_books())

    print("\n[2] Сортировка по цене (по убыванию)")
    print_books(service.list_books(sort="price", descending=True)[:3])

    print("\n[3] Фильтрация: книги до 600 руб., которые есть в наличии")
    print_books(service.list_books(max_price=Decimal("600"), available_only=True))

    print("\n[4] Поиск по автору: 'Пушкин'")
    print_books(service.search_books("Пушкин"))

    print("\n[5] Получение книги по id = 3")
    print_book(service.get_book(3))

    print("\n[6] Связанные объекты: выдачи читателя #2")
    for row in service.reader_loans(2):
        print_loan_row(row)

    print("\n[7] Транзакция: выдача книги #3 читателю #4")
    before = service.get_book(3).copies_available
    loan = service.issue_book(3, 4, days=14)
    after = service.get_book(3).copies_available
    print(f"  до выдачи доступно экземпляров: {before}")
    print(
        f"  создана выдача #{loan.id}: книга #{loan.book_id}, читатель #{loan.reader_id}, "
        f"срок {loan.due_date}"
    )
    print(f"  после выдачи доступно экземпляров: {after}")

    print("\n[8] Возврат книги")
    returned = service.return_loan(loan.id)
    print(f"  выдача #{returned.id} закрыта {returned.return_date}, доступно экземпляров: {service.get_book(3).copies_available}")

    print("\n[9] Обработка ошибок")
    try:
        service.get_book(999)
    except AppError as error:
        show_error(error)

    try:
        service.add_reader("Иванов И.И.", "ivanov@mail.ru")
    except AppError as error:
        show_error(error)

    try:
        service.add_book("Книга с ошибкой", "Автор", "Роман", 1200, "100.00", 1)
    except AppError as error:
        show_error(error)

    print("  Попытка выдать книгу #6, у которой 0 свободных экземпляров:")
    try:
        service.issue_book(6, 1)
    except AppError as error:
        show_error(error)
    print(f"  остаток после отката транзакции: {service.get_book(6).copies_available} экземпляров")

    try:
        service.return_loan(1)
    except AppError as error:
        show_error(error)

    print("\n[10] Просроченные выдачи")
    for row in service.overdue_loans():
        print_loan_row(row)

    print("\n[11] Изменение книги #7 (цена 320 -> 359.90)")
    updated = service.update_book(7, price=Decimal("359.90"))
    print_book(updated)

    print("\n[12] Добавление и удаление книги")
    temporary = service.add_book("Временная книга", "Тестовый автор", "Рассказ", 2020, "199.00", 1)
    print_book(temporary)
    service.delete_book(temporary.id)
    print(f"  книга #{temporary.id} удалена, всего книг: {service.statistics()['books']}")

    print("\n[13] Статистика")
    stats = service.statistics()
    print(
        f"  книг: {stats['books']}, читателей: {stats['readers']}, "
        f"экземпляров: {stats['copies_total']} (доступно {stats['copies_available']})"
    )
    print(
        f"  цена: средняя {money(stats['avg_price'])}, "
        f"минимум {money(stats['min_price'])}, максимум {money(stats['max_price'])} руб."
    )
    print(
        f"  активных выдач: {stats['active_loans']}, просрочено: {stats['overdue_loans']}"
    )
    print("\nДемонстрация завершена.")


def interactive(service: LibraryService) -> None:
    actions = {
        "1": lambda: print_books(service.list_books()),
        "2": lambda: print_books(service.list_books(sort="price", descending=True)),
        "3": lambda: print_books(
            service.list_books(max_price=Decimal("600"), available_only=True)
        ),
        "4": lambda: print_books(service.search_books(ask("Строка поиска: "))),
        "5": lambda: print_book(service.get_book(ask("id книги: ", int))),
        "6": lambda: print_book(
            service.add_book(
                ask("Название: "),
                ask("Автор: "),
                ask("Жанр: "),
                ask("Год: ", int),
                save_money(ask("Цена: ")),
                ask("Всего экземпляров: ", int),
            )
        ),
        "7": lambda: print_book(
            service.update_book(ask("id книги: ", int), price=save_money(ask("Новая цена: ")))
        ),
        "8": lambda: delete_book(service),
        "9": lambda: print_readers(service),
        "10": lambda: print(
            f"  добавлен читатель #{service.add_reader(ask('ФИО: '), ask('E-mail: '), ask('Телефон: ') or None).id}"
        ),
        "11": lambda: issue(service),
        "12": lambda: print(
            f"  выдача #{service.return_loan(ask('id выдачи: ', int)).id} закрыта"
        ),
        "13": lambda: print_loans(service.reader_loans(ask("id читателя: ", int))),
        "14": lambda: print_loans(service.overdue_loans()),
        "15": lambda: print_stats(service),
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
        except ValueError as error:
            print(f"  Некорректный ввод: {error}")
        except EOFError:
            return


def save_money(raw: str) -> Decimal:
    try:
        return Decimal(str(raw).replace(",", "."))
    except InvalidOperation as error:
        raise ValueError("цена должна быть числом") from error


def delete_book(service: LibraryService) -> None:
    book_id = ask("id книги: ", int)
    service.delete_book(book_id)
    print(f"  книга #{book_id} удалена")


def issue(service: LibraryService) -> None:
    loan = service.issue_book(
        ask("id книги: ", int),
        ask("id читателя: ", int),
        ask("срок, дней [14]: ", int, 14),
    )
    print(f"  создана выдача #{loan.id}, срок возврата {loan.due_date}")


def print_readers(service: LibraryService) -> None:
    for reader in service.list_readers():
        print(f"  #{reader.id:<3} {reader.full_name} | {reader.email} | {reader.phone or '-'}")


def print_loans(rows) -> None:
    if not rows:
        print("  выдач нет")
        return
    for row in rows:
        print_loan_row(row)


def print_stats(service: LibraryService) -> None:
    stats = service.statistics()
    print(
        f"  книг: {stats['books']}, читателей: {stats['readers']}, "
        f"средняя цена: {money(stats['avg_price'])} руб., "
        f"активных выдач: {stats['active_loans']}, просрочено: {stats['overdue_loans']}"
    )


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Библиотека: приложение на SQLAlchemy 2.x")
    parser.add_argument("--demo", action="store_true", help="выполнить сценарий демонстрации")
    parser.add_argument("--reset", action="store_true", help="пересоздать базу данных")
    parser.add_argument("--database-url", default=None, help="строка подключения SQLAlchemy")
    args = parser.parse_args(argv)

    database = Database(args.database_url)
    if args.reset:
        database.drop_all()
    database.create_all()

    service = LibraryService(database)
    if not service.list_books():
        seeded = seed_database(database)
        print(
            f"База данных заполнена: книг {seeded['books']}, "
            f"читателей {seeded['readers']}, выдач {seeded['loans']}"
        )

    if args.demo:
        demo(service)
        return 0

    try:
        interactive(service)
    except (KeyboardInterrupt, EOFError):
        print("\nРабота завершена.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
