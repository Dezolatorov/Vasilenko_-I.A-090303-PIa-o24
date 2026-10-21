from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from library.models import Author, Book, Genre, Loan, Reader

AUTHORS = (
    ("Пушкин А.С.", "Россия", 1799),
    ("Толстой Л.Н.", "Россия", 1828),
    ("Достоевский Ф.М.", "Россия", 1821),
    ("Чехов А.П.", "Россия", 1860),
    ("Булгаков М.А.", "Россия", 1891),
)

GENRES = ("Роман", "Повесть", "Поэма", "Рассказ", "Фантастика")

READERS = (
    ("Иванов И.И.", "ivanov@mail.ru", "+7-900-100-10-01"),
    ("Петрова А.С.", "petrova@mail.ru", "+7-900-100-10-02"),
    ("Сидоров П.П.", "sidorov@mail.ru", "+7-900-100-10-03"),
    ("Кузнецова М.В.", "kuznetsova@mail.ru", "+7-900-100-10-04"),
    ("Смирнов Д.А.", "smirnov@mail.ru", "+7-900-100-10-05"),
    ("Орлова Е.К.", "orlova@mail.ru", "+7-900-100-10-06"),
)

BOOKS = (
    ("Евгений Онегин", 1, "Поэма", 1833, "9785000000001", "450.00", 3, 2),
    ("Капитанская дочка", 1, "Повесть", 1836, "9785000000002", "380.00", 2, 2),
    ("Дубровский", 1, "Повесть", 1841, "9785000000003", "360.00", 2, 2),
    ("Война и мир", 2, "Роман", 1869, "9785000000004", "1200.00", 4, 3),
    ("Анна Каренина", 2, "Роман", 1877, "9785000000005", "990.00", 3, 3),
    ("Воскресение", 2, "Роман", 1899, "9785000000006", "870.00", 2, 2),
    ("Преступление и наказание", 3, "Роман", 1866, "9785000000007", "850.00", 3, 2),
    ("Идиот", 3, "Роман", 1869, "9785000000008", "780.00", 2, 1),
    ("Братья Карамазовы", 3, "Роман", 1880, "9785000000009", "910.00", 2, 2),
    ("Палата № 6", 4, "Повесть", 1892, "9785000000010", "320.00", 2, 2),
    ("Дама с собачкой", 4, "Рассказ", 1899, "9785000000011", "260.00", 1, 1),
    ("Вишнёвый сад", 4, "Повесть", 1903, "9785000000012", "300.00", 2, 2),
    ("Мастер и Маргарита", 5, "Роман", 1967, "9785000000013", "950.00", 5, 4),
    ("Собачье сердце", 5, "Повесть", 1925, "9785000000014", "410.00", 2, 2),
    ("Белая гвардия", 5, "Роман", 1925, "9785000000015", "520.00", 2, 2),
    ("Дюна", 5, "Фантастика", 1965, "9785000000016", "1100.00", 3, 3),
    ("Солярис", 5, "Фантастика", 1961, "9785000000017", "640.00", 2, 2),
    ("Пикник на обочине", 5, "Фантастика", 1972, "9785000000018", "560.00", 2, 1),
    ("Трудно быть богом", 5, "Фантастика", 1964, "9785000000019", "540.00", 2, 2),
    ("Понедельник начинается в субботу", 5, "Фантастика", 1965, "9785000000020", "610.00", 3, 3),
    ("1984", 5, "Роман", 1949, "9785000000021", "730.00", 3, 2),
    ("Скотный двор", 5, "Повесть", 1945, "9785000000022", "390.00", 2, 2),
)


class Command(BaseCommand):
    help = "Заполняет базу демонстрационными данными библиотеки"

    def handle(self, *args, **options):
        if Book.objects.exists():
            self.stdout.write("База уже заполнена, данные не добавлены")
        else:
            self._seed()
            self.stdout.write(self.style.SUCCESS("База заполнена: 22 книги, 6 читателей, 12 выдач"))
        self._users()

    def _seed(self) -> None:
        authors = [Author.objects.create(full_name=name, country=country, birth_year=year) for name, country, year in AUTHORS]
        genres = {name: Genre.objects.create(name=name) for name in GENRES}
        readers = [Reader.objects.create(full_name=name, email=email, phone=phone) for name, email, phone in READERS]

        books = []
        for title, author_index, genre, year, isbn, price, total, available in BOOKS:
            book = Book.objects.create(
                title=title,
                author=authors[author_index - 1],
                year=year,
                isbn=isbn,
                price=Decimal(price),
                copies_total=total,
                copies_available=available,
            )
            book.genres.add(genres[genre])
            if genre != "Роман":
                book.genres.add(genres["Роман"])
            books.append(book)

        today = date.today()
        for index, book in enumerate(books[:12]):
            reader = readers[index % len(readers)]
            returned = index % 4 == 0
            loan = Loan.objects.create(
                book=book,
                reader=reader,
                loan_date=today - timedelta(days=10 + index),
                due_date=today + timedelta(days=4 - index),
                return_date=today - timedelta(days=2) if returned else None,
            )
            if not returned:
                book.copies_available = max(0, book.copies_available - 1)
                book.save(update_fields=["copies_available"])

    def _users(self) -> None:
        user_model = get_user_model()
        if not user_model.objects.filter(username="admin").exists():
            user_model.objects.create_superuser("admin", "admin@example.com", "admin12345")
        if not user_model.objects.filter(username="reader").exists():
            user_model.objects.create_user("reader", "reader@example.com", "reader12345")
