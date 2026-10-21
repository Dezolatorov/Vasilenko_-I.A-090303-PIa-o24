from __future__ import annotations

from datetime import date, timedelta

from django import forms
from django.core.exceptions import ValidationError

from library.models import Book, Loan


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            "title",
            "author",
            "genres",
            "year",
            "isbn",
            "price",
            "copies_total",
            "copies_available",
            "description",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "genres": forms.SelectMultiple(attrs={"size": 5}),
        }

    def clean_isbn(self) -> str:
        isbn = (self.cleaned_data["isbn"] or "").strip()
        if not isbn.isdigit() or len(isbn) not in (10, 13):
            raise ValidationError("ISBN должен содержать 10 или 13 цифр")
        return isbn

    def clean(self):
        cleaned = super().clean()
        total = cleaned.get("copies_total")
        available = cleaned.get("copies_available")
        if total is not None and available is not None and available > total:
            self.add_error("copies_available", "Доступных экземпляров не может быть больше общего числа")
        return cleaned


class LoanForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ["reader", "due_date"]
        widgets = {"due_date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, book: Book, **kwargs):
        super().__init__(*args, **kwargs)
        self.book = book
        self.fields["due_date"].initial = date.today() + timedelta(days=14)

    def clean_due_date(self):
        due_date = self.cleaned_data["due_date"]
        if due_date < date.today():
            raise ValidationError("Срок возврата не может быть в прошлом")
        return due_date

    def clean(self):
        cleaned = super().clean()
        if self.book.copies_available <= 0:
            raise ValidationError("Свободных экземпляров нет")
        reader = cleaned.get("reader")
        if reader and self.book.loans.filter(reader=reader, return_date__isnull=True).exists():
            raise ValidationError("Эта книга уже выдана данному читателю")
        return cleaned
