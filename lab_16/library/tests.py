from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from library.models import Author, Book, Genre, Loan, Reader


class LibraryTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = Author.objects.create(full_name="Пушкин А.С.", country="Россия")
        cls.author2 = Author.objects.create(full_name="Толстой Л.Н.", country="Россия")
        cls.genre = Genre.objects.create(name="Роман")
        cls.poem = Genre.objects.create(name="Поэма")
        cls.reader = Reader.objects.create(full_name="Иванов И.И.", email="ivanov@mail.ru")

        cls.books = []
        for index in range(12):
            book = Book.objects.create(
                title=f"Книга {index:02d}",
                author=cls.author if index % 2 == 0 else cls.author2,
                year=1900 + index,
                isbn=f"9785000001{index:03d}",
                price=Decimal(100 + index),
                copies_total=2,
                copies_available=2,
            )
            book.genres.add(cls.genre)
            cls.books.append(book)
        cls.books[0].genres.add(cls.poem)

        cls.staff = get_user_model().objects.create_user(
            "admin", password="admin12345", is_staff=True
        )
        cls.superuser = get_user_model().objects.create_superuser(
            "root", "root@example.com", "root12345"
        )
        cls.regular = get_user_model().objects.create_user("reader", password="reader12345")

        today = date.today()
        cls.loan = Loan.objects.create(
            book=cls.books[0],
            reader=cls.reader,
            loan_date=today - timedelta(days=5),
            due_date=today - timedelta(days=1),
        )
        cls.books[0].copies_available = 1
        cls.books[0].save(update_fields=["copies_available"])
        cls.books[11].copies_available = 0
        cls.books[11].save(update_fields=["copies_available"])


class PagesTests(LibraryTestBase):
    def test_index_page(self):
        response = self.client.get(reverse("library:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "12")
        self.assertContains(response, "Библиотека")

    def test_book_list_page(self):
        response = self.client.get(reverse("library:book_list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["books"]), 10)

    def test_pagination_second_page(self):
        response = self.client.get(reverse("library:book_list"), {"page": 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["books"]), 2)

    def test_book_detail_page(self):
        response = self.client.get(reverse("library:book_detail", args=[self.books[0].pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Книга 00")
        self.assertContains(response, "Иванов И.И.")

    def test_book_detail_404(self):
        response = self.client.get(reverse("library:book_detail", args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_search_by_title(self):
        response = self.client.get(reverse("library:book_list"), {"q": "Книга 03"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["books"]), 1)

    def test_search_by_author(self):
        response = self.client.get(reverse("library:book_list"), {"q": "Толстой"})
        self.assertEqual(len(response.context["books"]), 6)

    def test_filter_by_genre(self):
        response = self.client.get(reverse("library:book_list"), {"genre": "Поэма"})
        self.assertEqual(len(response.context["books"]), 1)

    def test_filter_available(self):
        response = self.client.get(reverse("library:book_list"), {"available": "1"})
        self.assertEqual(response.context["total"], 11)
        self.assertTrue(
            all(book.copies_available > 0 for book in response.context["books"])
        )

    def test_sorting(self):
        response = self.client.get(reverse("library:book_list"), {"sort": "price", "order": "desc"})
        prices = [book.price for book in response.context["books"]]
        self.assertEqual(prices, sorted(prices, reverse=True))

    def test_statistics_page(self):
        response = self.client.get(reverse("library:statistics"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Статистика")
        self.assertEqual(response.context["total_books"], 12)
        self.assertEqual(response.context["overdue_loans"], 1)

    def test_readers_pages(self):
        response = self.client.get(reverse("library:readers"))
        self.assertEqual(response.status_code, 200)
        detail = self.client.get(reverse("library:reader_detail", args=[self.reader.pk]))
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, "Книга 00")


class CrudTests(LibraryTestBase):
    def payload(self, **overrides):
        data = {
            "title": "Новая книга",
            "author": self.author.pk,
            "genres": [self.genre.pk],
            "year": 2000,
            "isbn": "9785000009999",
            "price": "500.00",
            "copies_total": 3,
            "copies_available": 3,
            "description": "",
        }
        data.update(overrides)
        return data

    def test_create_requires_login(self):
        response = self.client.get(reverse("library:book_create"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_create_forbidden_for_regular_user(self):
        self.client.force_login(self.regular)
        response = self.client.get(reverse("library:book_create"))
        self.assertEqual(response.status_code, 403)

    def test_create_by_staff(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse("library:book_create"), self.payload())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Book.objects.filter(title="Новая книга").exists())

    def test_create_validation_error(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("library:book_create"), self.payload(copies_total=2, copies_available=5)
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "не может быть больше")

    def test_update_by_staff(self):
        self.client.force_login(self.staff)
        url = reverse("library:book_edit", args=[self.books[1].pk])
        response = self.client.post(url, self.payload(title="Изменённая книга", isbn=self.books[1].isbn))
        self.assertEqual(response.status_code, 302)
        self.books[1].refresh_from_db()
        self.assertEqual(self.books[1].title, "Изменённая книга")

    def test_delete_by_staff(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse("library:book_delete", args=[self.books[2].pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Book.objects.filter(pk=self.books[2].pk).exists())


class LoanTests(LibraryTestBase):
    def test_borrow_book_by_staff(self):
        self.client.force_login(self.staff)
        url = reverse("library:book_borrow", args=[self.books[3].pk])
        before = Loan.objects.count()
        response = self.client.post(
            url, {"reader": self.reader.pk, "due_date": (date.today() + timedelta(days=14)).isoformat()}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Loan.objects.count(), before + 1)
        self.books[3].refresh_from_db()
        self.assertEqual(self.books[3].copies_available, 1)

    def test_return_loan_by_staff(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse("library:loan_return", args=[self.loan.pk]))
        self.assertEqual(response.status_code, 302)
        self.loan.refresh_from_db()
        self.assertIsNotNone(self.loan.return_date)
        self.books[0].refresh_from_db()
        self.assertEqual(self.books[0].copies_available, 2)

    def test_borrow_requires_staff(self):
        self.client.force_login(self.regular)
        response = self.client.get(reverse("library:book_borrow", args=[self.books[3].pk]))
        self.assertEqual(response.status_code, 302)


class ModelTests(LibraryTestBase):
    def test_relations(self):
        self.assertEqual(self.books[0].genres.count(), 2)
        self.assertEqual(self.reader.loans.count(), 1)
        self.assertEqual(self.books[0].loans.count(), 1)

    def test_overdue_flag(self):
        self.assertTrue(self.loan.is_overdue)

    def test_admin_changelist(self):
        self.client.force_login(self.superuser)
        response = self.client.get("/admin/library/book/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Книга 00")
