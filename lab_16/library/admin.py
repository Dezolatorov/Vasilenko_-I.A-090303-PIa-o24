from __future__ import annotations

from django.contrib import admin

from library.models import Author, Book, Genre, Loan, Reader


class LoanInline(admin.TabularInline):
    model = Loan
    extra = 0
    fields = ("reader", "loan_date", "due_date", "return_date")
    readonly_fields = ("loan_date",)


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("full_name", "country", "birth_year", "books_count")
    search_fields = ("full_name", "country")
    list_filter = ("country",)
    ordering = ("full_name",)

    @admin.display(description="книг")
    def books_count(self, obj: Author) -> int:
        return obj.books.count()


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name", "books_count")
    search_fields = ("name",)
    ordering = ("name",)

    @admin.display(description="книг")
    def books_count(self, obj: Genre) -> int:
        return obj.books.count()


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "author",
        "year",
        "price",
        "copies_total",
        "copies_available",
        "is_available",
    )
    list_filter = ("genres", "author", "year")
    search_fields = ("title", "isbn", "author__full_name")
    list_editable = ("price",)
    ordering = ("title",)
    inlines = [LoanInline]
    filter_horizontal = ("genres",)
    list_select_related = ("author",)
    fieldsets = (
        ("Основное", {"fields": ("title", "author", "genres")}),
        ("Издание", {"fields": ("year", "isbn", "price")}),
        ("Фонд", {"fields": ("copies_total", "copies_available", "description")}),
    )

    @admin.display(boolean=True, description="в наличии")
    def is_available(self, obj: Book) -> bool:
        return obj.is_available


@admin.register(Reader)
class ReaderAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "phone", "registered_at", "loans_count")
    search_fields = ("full_name", "email")
    list_filter = ("registered_at",)
    ordering = ("full_name",)

    @admin.display(description="выдач")
    def loans_count(self, obj: Reader) -> int:
        return obj.loans.count()


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ("book", "reader", "loan_date", "due_date", "return_date", "is_overdue")
    list_filter = ("return_date", "due_date")
    search_fields = ("book__title", "reader__full_name")
    date_hierarchy = "loan_date"
    list_select_related = ("book", "reader")

    @admin.display(boolean=True, description="просрочена")
    def is_overdue(self, obj: Loan) -> bool:
        return obj.is_overdue
