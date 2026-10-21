"""Этап 1. Первоначальная («наивная») реализация без паттернов.

Используется как отправная точка для рефакторинга в ЛР8:
вся логика выдачи, возврата и бронирования собрана в одном классе
и построена на цепочках if/elif по строковому статусу.
"""


class NaiveLibrary:
    def __init__(self) -> None:
        self.items: dict[int, dict] = {}
        self.next_id = 1

    def add_item(self, item_type: str, title: str, author: str, year: int) -> int:
        item_id = self.next_id
        self.next_id += 1
        self.items[item_id] = {
            "id": item_id,
            "type": item_type,
            "title": title,
            "author": author,
            "year": year,
            "status": "available",
            "days": 14,
            "reader": None,
        }
        return item_id

    def process(self, action: str, item_id: int, reader: str = "") -> str:
        item = self.items.get(item_id)
        if item is None:
            return f"Издание {item_id} не найдено"

        if action == "issue":
            if item["status"] == "available":
                if item["type"] == "printed":
                    item["days"] = 14
                elif item["type"] == "electronic":
                    item["days"] = 7
                elif item["type"] == "magazine":
                    item["days"] = 3
                else:
                    return "Неизвестный тип издания"
                item["status"] = "issued"
                item["reader"] = reader
                return f"Выдано «{item['title']}» на {item['days']} дн."
            elif item["status"] == "issued":
                return "Издание уже выдано"
            elif item["status"] == "reserved":
                return "Издание забронировано другим читателем"
            else:
                return "Недопустимый статус"

        elif action == "return":
            if item["status"] == "issued":
                item["status"] = "available"
                item["reader"] = None
                return f"Возвращено «{item['title']}»"
            elif item["status"] == "available":
                return "Издание не выдавалось"
            else:
                return "Недопустимый статус"

        elif action == "reserve":
            if item["status"] == "available":
                item["status"] = "reserved"
                item["reader"] = reader
                return f"Забронировано «{item['title']}»"
            elif item["status"] == "issued":
                return "Издание выдано, бронь невозможна"
            else:
                return "Издание уже забронировано"

        else:
            return "Неизвестная операция"


if __name__ == "__main__":
    library = NaiveLibrary()
    book_id = library.add_item("printed", "Война и мир", "Л. Толстой", 1869)
    print(library.process("issue", book_id, "Иванов"))
    print(library.process("issue", book_id, "Петров"))
    print(library.process("return", book_id))
