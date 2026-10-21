from __future__ import annotations

from datetime import date

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from library.forms import BookForm, LoanForm
from library.models import Book, Genre, Loan, Reader

SORT_FIELDS = {
    "title": "title",
    "year": "year",
    "price": "price",
    "author": "author__full_name",
}


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self) -> bool:
        return self.request.user.is_staff


def index(request):
    context = {
        "books_count": Book.objects.count(),
        "authors_count": Book.objects.values("author").distinct().count(),
        "readers_count": Reader.objects.count(),
        "active_loans": Loan.objects.filter(return_date__isnull=True).count(),
        "latest": Book.objects.select_related("author").order_by("-year")[:5],
    }
    return render(request, "library/index.html", context)


class BookListView(ListView):
    model = Book
    template_name = "library/book_list.html"
    context_object_name = "books"
    paginate_by = 10

    def get_queryset(self):
        queryset = Book.objects.select_related("author").prefetch_related("genres")
        query = self.request.GET.get("q", "").strip()
        genre = self.request.GET.get("genre", "")
        available = self.request.GET.get("available") == "1"
        sort = self.request.GET.get("sort", "title")
        order = self.request.GET.get("order", "asc")

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(author__full_name__icontains=query)
                | Q(isbn__icontains=query)
            )
        if genre:
            queryset = queryset.filter(genres__name=genre)
        if available:
            queryset = queryset.filter(copies_available__gt=0)

        column = SORT_FIELDS.get(sort, "title")
        prefix = "-" if order == "desc" else ""
        return queryset.order_by(f"{prefix}{column}", "id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "q": self.request.GET.get("q", ""),
                "genre": self.request.GET.get("genre", ""),
                "available": self.request.GET.get("available") == "1",
                "sort": self.request.GET.get("sort", "title"),
                "order": self.request.GET.get("order", "asc"),
                "genres": Genre.objects.all(),
                "total": self.get_queryset().count(),
            }
        )
        return context


class BookDetailView(DetailView):
    model = Book
    template_name = "library/book_detail.html"
    context_object_name = "book"

    def get_queryset(self):
        return Book.objects.select_related("author").prefetch_related("genres", "loans__reader")


class BookCreateView(StaffRequiredMixin, CreateView):
    model = Book
    form_class = BookForm
    template_name = "library/book_form.html"
    success_url = reverse_lazy("library:book_list")


class BookUpdateView(StaffRequiredMixin, UpdateView):
    model = Book
    form_class = BookForm
    template_name = "library/book_form.html"

    def get_success_url(self):
        return reverse_lazy("library:book_detail", kwargs={"pk": self.object.pk})


class BookDeleteView(StaffRequiredMixin, DeleteView):
    model = Book
    template_name = "library/book_confirm_delete.html"
    success_url = reverse_lazy("library:book_list")


@staff_member_required
def borrow_book(request, pk: int):
    book = get_object_or_404(Book, pk=pk)
    form = LoanForm(request.POST or None, book=book)

    if request.method == "POST" and form.is_valid():
        loan = form.save(commit=False)
        loan.book = book
        loan.loan_date = date.today()
        book.copies_available -= 1
        book.save()
        loan.save()
        messages.success(request, f"Книга выдана: {loan.reader.full_name}")
        return redirect("library:book_detail", pk=book.pk)

    return render(request, "library/loan_form.html", {"book": book, "form": form})


@staff_member_required
def return_loan(request, pk: int):
    loan = get_object_or_404(Loan.objects.select_related("book"), pk=pk)
    if request.method == "POST" and loan.return_date is None:
        loan.return_date = date.today()
        loan.save()
        book = loan.book
        book.copies_available = min(book.copies_total, book.copies_available + 1)
        book.save()
        messages.success(request, "Книга возвращена")
    return redirect("library:book_detail", pk=loan.book_id)


def statistics(request):
    context = {
        "total_books": Book.objects.count(),
        "avg_price": Book.objects.aggregate(value=Avg("price"))["value"] or 0,
        "available_books": Book.objects.filter(copies_available__gt=0).count(),
        "overdue_loans": Loan.objects.filter(
            return_date__isnull=True, due_date__lt=date.today()
        ).count(),
        "readers_count": Reader.objects.count(),
        "by_genre": Genre.objects.annotate(books_count=Count("books")).order_by("-books_count"),
        "top_reader": Reader.objects.annotate(loans_count=Count("loans")).order_by("-loans_count").first(),
        "expensive": Book.objects.order_by("-price").first(),
    }
    return render(request, "library/statistics.html", context)


def readers(request):
    context = {"readers": Reader.objects.prefetch_related("loans")}
    return render(request, "library/readers.html", context)


def reader_detail(request, pk: int):
    reader = get_object_or_404(Reader, pk=pk)
    context = {
        "reader": reader,
        "loans": reader.loans.select_related("book").order_by("-loan_date"),
    }
    return render(request, "library/reader_detail.html", context)
