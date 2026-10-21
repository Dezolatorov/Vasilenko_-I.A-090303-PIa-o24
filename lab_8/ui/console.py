from models.entities import Reader
from models.enums import ItemType, ReaderCategory
from services.library_service import LibraryService


class ConsoleUI:
    def __init__(self, service: LibraryService):
        self.service = service

    def run(self) -> None:
        while True:
            self._print_menu()
            choice = input("Выберите действие: ").strip()
            try:
                if choice == "1":
                    self._add_item()
                elif choice == "2":
                    self._list_items()
                elif choice == "3":
                    self._issue()
                elif choice == "4":
                    self._return()
                elif choice == "5":
                    self._reserve()
                elif choice == "6":
                    self._search()
                elif choice == "7":
                    self._statistics()
                elif choice == "8":
                    self._loans()
                elif choice == "0":
                    print("Выход.")
                    return
                else:
                    print("Неизвестная команда.")
            except ValueError as e:
                print(f"Ошибка: {e}")

    @staticmethod
    def _print_menu() -> None:
        print("\n===== БИБЛИОТЕКА =====")
        print("1. Добавить издание")
        print("2. Показать все издания")
        print("3. Выдать издание")
        print("4. Вернуть издание")
        print("5. Забронировать издание")
        print("6. Поиск по автору/названию")
        print("7. Статистика")
        print("8. История выдач")
        print("0. Выход")

    def _add_item(self) -> None:
        print("Тип: 1 — печатная книга, 2 — электронная, 3 — журнал")
        t = input("Тип: ").strip()
        mapping = {"1": ItemType.PRINTED_BOOK,
                   "2": ItemType.EBOOK,
                   "3": ItemType.MAGAZINE}
        if t not in mapping:
            print("Неверный тип.")
            return
        item_id = int(input("ID: "))
        title = input("Название: ").strip()
        author = input("Автор: ").strip()
        year = int(input("Год: "))
        item = self.service.add_item(mapping[t], id=item_id,
                                     title=title, author=author, year=year)
        print(f"Добавлено: {item}")

    def _list_items(self) -> None:
        items = self.service.list_items()
        if not items:
            print("Фонд пуст.")
            return
        for i in items:
            print(i)

    def _issue(self) -> None:
        item_id = int(input("ID издания: "))
        reader_id = int(input("ID читателя: "))
        name = input("Имя читателя: ").strip()
        print("Категория: 1 — студент, 2 — преподаватель, 3 — льготная")
        cat = {"1": ReaderCategory.STUDENT,
               "2": ReaderCategory.TEACHER,
               "3": ReaderCategory.PREFERENTIAL}[input("Категория: ").strip()]
        reader = Reader(id=reader_id, name=name, category=cat)
        print(self.service.issue(item_id, reader))

    def _return(self) -> None:
        item_id = int(input("ID издания: "))
        print(self.service.return_item(item_id))

    def _reserve(self) -> None:
        item_id = int(input("ID издания: "))
        print(self.service.reserve(item_id))

    def _search(self) -> None:
        mode = input("Искать по (1 — автор, 2 — название): ").strip()
        q = input("Запрос: ").strip()
        results = (self.service.find_by_author(q) if mode == "1"
                   else self.service.find_by_title(q))
        if not results:
            print("Ничего не найдено.")
        for r in results:
            print(r)

    def _statistics(self) -> None:
        s = self.service.statistics()
        print(f"Всего: {s['total']}")
        print(f"Доступно: {s['available']}")
        print(f"Выдано: {s['issued']}")
        print(f"Забронировано: {s['reserved']}")

    def _loans(self) -> None:
        records = self.service.loan_history()
        if not records:
            print("История выдач пуста.")
            return
        for r in records:
            state = "возвращено" if r.returned else "активна"
            print(f"Издание {r.item_id} → читатель {r.reader_id} | "
                  f"выдано {r.issued_at} | до {r.due_at} | {state}")