# console_ui.py
from services import LibraryService

class ConsoleUI:
    def __init__(self, service: LibraryService):
        self.service = service

    def run(self):
        while True:
            print("\n=== СИСТЕМА УПРАВЛЕНИЯ БИБЛИОТЕКОЙ ===")
            print("1. Выдать книгу читателю")
            print("2. Оформить возврат книги")
            print("3. Забронировать книгу")
            print("4. Отменить бронирование")
            print("5. Проверить и уведомить должников")
            print("0. Выйти")
            choice = input("Выберите действие: ")

            if choice == "1":
                self._handle_action(self.service.borrow_book, "выдачи книги")
            elif choice == "2":
                self._handle_action(self.service.return_book, "возврата книги")
            elif choice == "3":
                self._handle_action(self.service.reserve_book, "бронирования книги")
            elif choice == "4":
                self._handle_action(self.service.cancel_reservation, "отмены бронирования")
            elif choice == "5":
                print("\n--- Сканирование просроченных задолженностей ---")
                overdues = self.service.check_overdue_loans()
                if not overdues:
                    print("Задолженностей не обнаружено.")
                else:
                    for reader, book in overdues:
                        print(f"Должник: {reader.name} | Книга: '{book.title}' [Уведомлен]")
            elif choice == "0":
                print("Завершение работы.")
                break

    def _handle_action(self, action_func, action_name):
        try:
            book_id = int(input("Введите ID книги: "))
            reader_id = int(input("Введите ID читателя: "))
            success = action_func(book_id, reader_id)
            if success:
                print(f"Успех: Операция {action_name} зарегистрирована.")
            else:
                print(f"Ошибка: Не удалось выполнить операцию {action_name}.")
        except ValueError:
            print("Ошибка: Вводите числовые ID!")
