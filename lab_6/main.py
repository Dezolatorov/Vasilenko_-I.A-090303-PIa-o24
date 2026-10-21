from datetime import date, timedelta
from models import Book, Magazine, DigitalEdition, LibraryStatus
from services import LibraryService, inspect_object
from context import transaction_mode
from exceptions import LibraryError

def main() -> None:
    service = LibraryService()

    # Предустановка данных (Тест 1)
    service.add_edition(Book(id=1, title="Капитанская дочка", author="А.С. Пушкин", pages=224))
    service.add_edition(Magazine(id=2, title="Наука и Жизнь", issue_number=12, publish_month="Декабрь"))
    
    # Имитируем просроченное издание для демонстрации работы поиска (Тест 3 - граничные значения)
    overdue_book = Book(id=3, title="Старая книга", author="Неизвестен", pages=100)
    overdue_book.status = LibraryStatus.ISSUED
    overdue_book.due_date = date.today() - timedelta(days=5)  # Дата сдачи была 5 дней назад
    service.add_edition(overdue_book)

    while True:
        print("\n===== МЕНЮ БИБЛИОТЕКИ =====")
        print("1. Добавить книгу")
        print("2. Добавить журнал")
        print("3. Добавить электронное издание")
        print("4. Удалить издание")
        print("5. Найти издание по ID")
        print("6. Показать все издания (Protocol)")
        print("7. Выдать издание читателю")
        print("8. Вернуть издание в фонд")
        print("9. Показать ПРОСРОЧЕННЫЕ выдачи")
        print("10. Получить статистику")
        print("11. Выполнить интроспекцию сервиса")
        print("12. Демонстрация контекстного менеджера")
        print("13. Зарезервировать издание")
        print("14. Отменить бронирование")
        print("0. Выход")
        
        choice = input("Выберите действие: ").strip()

        try:
            if choice == "1":
                id_ = int(input("Введите уникальный ID: "))
                title = input("Введите название книги: ")
                author = input("Введите автора: ")
                pages = int(input("Введите количество страниц: "))
                service.add_edition(Book(id=id_, title=title, author=author, pages=pages))
                print("Книга успешно добавлена!")

            elif choice == "2":
                id_ = int(input("Введите уникальный ID: "))
                title = input("Введите название журнала: ")
                num = int(input("Введите номер выпуска: "))
                month = input("Введите месяц публикации: ")
                service.add_edition(Magazine(id=id_, title=title, issue_number=num, publish_month=month))
                print("Журнал успешно добавлен!")

            elif choice == "3":
                id_ = int(input("Введите уникальный ID: "))
                title = input("Введите название электронного издания: ")
                fmt = input("Введите формат (PDF/EPUB/FB2): ")
                size = float(input("Введите размер файла (МБ): "))
                service.add_edition(DigitalEdition(id=id_, title=title, file_format=fmt, file_size_mb=size))
                print("Электронное издание успешно добавлено!")

            elif choice == "4":
                id_ = int(input("Введите ID для удаления: "))
                service.delete_edition(id_)
                print("Издание удалено.")

            elif choice == "5":
                id_ = int(input("Введите ID для поиска: "))
                ed = service.find_by_id(id_)
                print(f"Найдено: {ed}")

            elif choice == "6":
                service.print_protocol_reports(service.editions)

            elif choice == "7":
                id_ = int(input("Введите ID издания для выдачи: "))
                days = int(input("На сколько дней выдать? (по умолчанию 14): ") or 14)
                msg = service.issue_edition(id_, days)
                print(msg)

            elif choice == "8":
                id_ = int(input("Введите ID возвращаемого издания: "))
                msg = service.return_edition(id_)
                print(msg)

            elif choice == "9":
                print("\n--- ПОИСК ПРОСРОЧЕННЫХ ВЫДАЧ ---")
                overdue = service.find_overdue_editions()
                if not overdue:
                    print("Просроченных изданий нет.")
                for ed in overdue:
                    print(f"ID {ed.id}: '{ed.title}' (Должно быть возвращено: {ed.due_date})")

            elif choice == "10":
                stats = service.get_statistics()
                print("\n--- СТАТИСТИКА БИБЛИОТЕКИ ---")
                for k, v in stats.items():
                    print(f"{k}: {v}")

            elif choice == "11":
                inspect_object(service)

            elif choice == "12":
                with transaction_mode("Каталог Библиотеки"):
                    service.add_edition(Book(id=20, title="Транзакционная Книга", author="Тест", pages=150))
                    fail = input("Вызвать ошибку для проверки отката? (y/n): ").lower()
                    if fail == 'y':
                        raise ValueError("Имитация критического сбоя.")

            elif choice == "13":
                id_ = int(input("Введите ID издания для бронирования: "))
                days = int(input("На сколько дней забронировать? (по умолчанию 3): ") or 3)
                msg = service.reserve_edition(id_, days)
                print(msg)

            elif choice == "14":
                id_ = int(input("Введите ID издания для отмены брони: "))
                msg = service.cancel_reservation(id_)
                print(msg)

            elif choice == "0":
                print("Программа завершена.")
                break
            else:
                print("Ошибка: Неизвестный пункт меню.")

        except LibraryError as le:
            print(f"[ОШИБКА БИЗНЕС-ЛОГИКИ]: {le}")
        except ValueError as ve:
            print(f"[ОШИБКА ВВОДА ДАННЫХ]: Проверьте типы вводимых значений. Детали: {ve}")
        except Exception as e:
            print(f"[НЕПРЕДВИДЕННАЯ ОШИБКА]: {type(e).__name__}: {e}")

if __name__ == "__main__":
    main()
