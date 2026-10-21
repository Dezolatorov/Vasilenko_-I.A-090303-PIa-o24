from __future__ import annotations

from datetime import date

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Genre(models.Model):
    name = models.CharField("название", max_length=60, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Жанр"
        verbose_name_plural = "Жанры"

    def __str__(self) -> str:
        return self.name


class Author(models.Model):
    full_name = models.CharField("ФИО", max_length=120, unique=True)
    country = models.CharField("страна", max_length=60, default="Россия")
    birth_year = models.PositiveIntegerField("год рождения", null=True, blank=True)

    class Meta:
        ordering = ["full_name"]
        verbose_name = "Автор"
        verbose_name_plural = "Авторы"

    def __str__(self) -> str:
        return self.full_name


class Reader(models.Model):
    full_name = models.CharField("ФИО", max_length=120)
    email = models.EmailField("e-mail", unique=True)
    phone = models.CharField("телефон", max_length=30, blank=True)
    registered_at = models.DateField("дата регистрации", default=date.today)

    class Meta:
        ordering = ["full_name"]
        verbose_name = "Читатель"
        verbose_name_plural = "Читатели"

    def __str__(self) -> str:
        return f"{self.full_name} ({self.email})"


class Book(models.Model):
    title = models.CharField("название", max_length=200, db_index=True)
    author = models.ForeignKey(
        Author,
        verbose_name="автор",
        on_delete=models.CASCADE,
        related_name="books",
    )
    genres = models.ManyToManyField(Genre, verbose_name="жанры", related_name="books", blank=True)
    year = models.PositiveIntegerField(
        "год издания",
        validators=[MinValueValidator(1400), MaxValueValidator(2100)],
    )
    isbn = models.CharField("ISBN", max_length=13, unique=True)
    price = models.DecimalField(
        "цена",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0,
    )
    copies_total = models.PositiveIntegerField("всего экземпляров", default=1)
    copies_available = models.PositiveIntegerField("доступно", default=1)
    description = models.TextField("описание", blank=True)

    class Meta:
        ordering = ["title"]
        verbose_name = "Книга"
        verbose_name_plural = "Книги"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(year__gte=1400, year__lte=2100),
                name="ck_book_year",
            ),
            models.CheckConstraint(
                condition=models.Q(copies_available__lte=models.F("copies_total")),
                name="ck_book_copies",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.title} — {self.author.full_name}"

    @property
    def is_available(self) -> bool:
        return self.copies_available > 0

    def save(self, *args, **kwargs):
        if self.copies_available is None or self.copies_available > self.copies_total:
            self.copies_available = self.copies_total
        super().save(*args, **kwargs)


class Loan(models.Model):
    book = models.ForeignKey(
        Book,
        verbose_name="книга",
        on_delete=models.CASCADE,
        related_name="loans",
    )
    reader = models.ForeignKey(
        Reader,
        verbose_name="читатель",
        on_delete=models.CASCADE,
        related_name="loans",
    )
    loan_date = models.DateField("дата выдачи", default=date.today)
    due_date = models.DateField("срок возврата")
    return_date = models.DateField("дата возврата", null=True, blank=True)

    class Meta:
        ordering = ["-loan_date", "-id"]
        verbose_name = "Выдача"
        verbose_name_plural = "Выдачи"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(due_date__gte=models.F("loan_date")),
                name="ck_loan_dates",
            )
        ]

    def __str__(self) -> str:
        return f"{self.book.title} → {self.reader.full_name}"

    @property
    def is_overdue(self) -> bool:
        return self.return_date is None and self.due_date < date.today()
