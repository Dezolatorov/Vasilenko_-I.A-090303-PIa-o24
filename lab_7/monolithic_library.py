# monolithic_library.py
from datetime import datetime, timedelta

class EmailSender:
    def send_email(self, email: str, message: str):
        # Жестко прописанная отправка email
        print(f"[EMAIL NOTIFICATION Sent to {email}]: {message}")

class LibraryManager:
    """
    ПЛОХОЙ КЛАСС: Нарушает SRP, OCP, DIP.
    Сам хранит данные, сам отправляет email, жестко связан с консолью.
    """
    def __init__(self):
        self.books = [
            {"id": 1, "title": "1984", "author": "George Orwell", "is_borrowed": False},
            {"id": 2, "title": "Brave New World", "author": "Aldous Huxley", "is_borrowed": True}
        ]
        self.readers = [
            {"id": 101, "name": "Ivanov", "email": "ivanov@mail.ru"},
            {"id": 102, "name": "Petrov", "email": "petrov@mail.ru"}
        ]
        self.loans = [
            {"book_id": 2, "reader_id": 102, "due_date": datetime.now() - timedelta(days=1)}
        ]
        self.email_sender = EmailSender() # Жесткая зависимость (Нарушение DIP)

    def process_menu(self):
        """Прямая работа с консолью внутри бизнес-логики (Нарушение SRP)"""
        while True:
            print("\n=== НАИВНАЯ БИБЛИОТЕКА ===")
            print("1. Выдать книгу")
            print("2. Показать просроченные")
            print("0. Выход")
            choice = input("Выберите действие: ")

            if choice == "1":
                book_id = int(input("ID книги: "))
                reader_id = int(input("ID читателя: "))
                
                # Нарушение OCP: Если логика усложнится, придется переписывать этот if/elif
                book = next((b for b in self.books if b["id"] == book_id), None)
                if book and not book["is_borrowed"]:
                    book["is_borrowed"] = True
                    due_date = datetime.now() + timedelta(days=14)
                    self.loans.append({"book_id": book_id, "reader_id": reader_id, "due_date": due_date})
                    
                    # Жесткое уведомление (Нарушение SRP и DIP)
                    reader = next((r for r in self.readers if r["id"] == reader_id), None)
                    if reader:
                        self.email_sender.send_email(reader["email"], f"Вы взяли книгу '{book['title']}'")
                    print("Книга успешно выдана!")
                else:
                    print("Ошибка: Книга недоступна!")

            elif choice == "2":
                print("--- Просроченные выдачи ---")
                for loan in self.loans:
                    if loan["due_date"] < datetime.now():
                        reader = next((r for r in self.readers if r["id"] == loan["reader_id"]), None)
                        book = next((b for b in self.books if b["id"] == loan["book_id"]), None)
                        if reader and book:
                            print(f"Читатель {reader['name']} просрочил книгу '{book['title']}'!")
                            # Нарушение OCP: Извещение только по Email. 
                            # Если захотим добавить SMS, придется менять код здесь.
                            self.email_sender.send_email(reader["email"], f"Верните книгу '{book['title']}'!")
            elif choice == "0":
                break

if __name__ == "__main__":
    manager = LibraryManager()
    manager.process_menu()
