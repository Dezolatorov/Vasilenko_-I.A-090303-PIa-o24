from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.database import get_session
from app.services.services import ConflictError, LibraryService, NotFoundError, ValidationError

web = Blueprint("web", __name__)


def service() -> LibraryService:
    return LibraryService(get_session())


@web.route("/")
def index():
    library = service()
    stats = library.statistics()
    latest = library.list_books(sort="year", order="desc")[:4]
    return render_template("index.html", stats=stats, latest=latest)


@web.route("/books")
def books():
    library = service()
    search = request.args.get("search", "").strip()
    genre = request.args.get("genre") or None
    sort = request.args.get("sort", "title")
    order = request.args.get("order", "asc")
    available = request.args.get("available") == "1"

    items = library.list_books(
        search=search or None,
        genre=genre,
        available_only=available,
        sort=sort,
        order=order,
    )
    return render_template(
        "list.html",
        books=items,
        genres=library.genres(),
        search=search,
        genre=genre,
        sort=sort,
        order=order,
        available=available,
    )


@web.route("/books/<int:book_id>")
def book_detail(book_id: int):
    try:
        book = service().get_book(book_id)
    except NotFoundError:
        return render_template("404.html"), 404
    return render_template("detail.html", book=book)


@web.route("/books/create", methods=["GET", "POST"])
def book_create():
    library = service()
    authors = library.authors.list()

    if request.method == "POST":
        try:
            book = library.create_book(request.form.to_dict())
            flash("Книга добавлена в каталог", "success")
            return redirect(url_for("web.book_detail", book_id=book.id))
        except (ValidationError, ConflictError) as error:
            flash(str(error), "error")
            return (
                render_template("form.html", authors=authors, book=request.form, mode="create"),
                400,
            )

    return render_template("form.html", authors=authors, book={}, mode="create")


@web.route("/books/<int:book_id>/edit", methods=["GET", "POST"])
def book_edit(book_id: int):
    library = service()
    authors = library.authors.list()

    try:
        book = library.get_book(book_id)
    except NotFoundError:
        return render_template("404.html"), 404

    if request.method == "POST":
        try:
            library.update_book(book_id, request.form.to_dict())
            flash("Изменения сохранены", "success")
            return redirect(url_for("web.book_detail", book_id=book_id))
        except (ValidationError, ConflictError) as error:
            flash(str(error), "error")
            return (
                render_template(
                    "form.html",
                    authors=authors,
                    book=request.form,
                    mode="edit",
                    book_id=book_id,
                ),
                400,
            )

    return render_template("form.html", authors=authors, book=book, mode="edit", book_id=book_id)


@web.route("/books/<int:book_id>/delete", methods=["POST"])
def book_delete(book_id: int):
    try:
        service().delete_book(book_id)
        flash("Книга удалена", "success")
    except NotFoundError:
        return render_template("404.html"), 404
    return redirect(url_for("web.books"))


@web.route("/books/<int:book_id>/borrow", methods=["GET", "POST"])
def book_borrow(book_id: int):
    library = service()

    try:
        book = library.get_book(book_id)
    except NotFoundError:
        return render_template("404.html"), 404

    if request.method == "POST":
        try:
            library.issue_book(
                book_id,
                int(request.form.get("reader_id", 0)),
                int(request.form.get("days", 14)),
            )
            flash("Книга выдана читателю", "success")
            return redirect(url_for("web.book_detail", book_id=book_id))
        except (ValidationError, NotFoundError) as error:
            flash(str(error), "error")

    return render_template("borrow.html", book=book, readers=library.readers.list())


@web.route("/loans/<int:loan_id>/return", methods=["POST"])
def loan_return(loan_id: int):
    try:
        loan = service().return_book(loan_id)
    except (ValidationError, NotFoundError) as error:
        flash(str(error), "error")
        return redirect(url_for("web.readers"))

    flash("Книга возвращена", "success")
    return redirect(url_for("web.reader_detail", reader_id=loan.reader_id))


@web.route("/readers")
def readers():
    return render_template("readers.html", readers=service().readers.list())


@web.route("/readers/<int:reader_id>")
def reader_detail(reader_id: int):
    library = service()
    reader = library.readers.get(reader_id)
    if reader is None:
        return render_template("404.html"), 404
    return render_template(
        "reader_detail.html",
        reader=reader,
        loans=library.reader_loans(reader_id),
    )
