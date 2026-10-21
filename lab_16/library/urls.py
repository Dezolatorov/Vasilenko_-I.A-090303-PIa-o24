from __future__ import annotations

from django.urls import path

from library import views

app_name = "library"

urlpatterns = [
    path("", views.index, name="index"),
    path("books/", views.BookListView.as_view(), name="book_list"),
    path("books/create/", views.BookCreateView.as_view(), name="book_create"),
    path("books/<int:pk>/", views.BookDetailView.as_view(), name="book_detail"),
    path("books/<int:pk>/edit/", views.BookUpdateView.as_view(), name="book_edit"),
    path("books/<int:pk>/delete/", views.BookDeleteView.as_view(), name="book_delete"),
    path("books/<int:pk>/borrow/", views.borrow_book, name="book_borrow"),
    path("loans/<int:pk>/return/", views.return_loan, name="loan_return"),
    path("readers/", views.readers, name="readers"),
    path("readers/<int:pk>/", views.reader_detail, name="reader_detail"),
    path("statistics/", views.statistics, name="statistics"),
]
