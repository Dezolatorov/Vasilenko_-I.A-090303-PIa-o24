"""Сервис авторов."""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..exceptions import ConflictException, EntityNotFoundException, ValidationException
from ..models import Author
from ..repositories import AuthorRepository
from ..schemas import AuthorCreate, AuthorUpdate


class AuthorService:
    def __init__(self, db: Session):
        self.db = db
        self.authors = AuthorRepository(db)

    def create(self, data: AuthorCreate) -> Author:
        if data.birth_year and data.birth_year > 2026:
            raise ValidationException("birth_year не может быть в будущем")
        author = Author(name=data.name, birth_year=data.birth_year, biography=data.biography)
        return self.authors.add(author)

    def get(self, author_id: int) -> Author:
        return self.authors.get(author_id)

    def search(self, name: str | None = None) -> list[Author]:
        return self.authors.search(name)

    def update(self, author_id: int, data: AuthorUpdate) -> Author:
        author = self.authors.get(author_id)
        if data.name is not None:
            author.name = data.name
        if data.birth_year is not None:
            author.birth_year = data.birth_year
        if data.biography is not None:
            author.biography = data.biography
        self.db.flush()
        return author

    def delete(self, author_id: int) -> None:
        author = self.authors.get(author_id)
        if author.books:
            raise ConflictException(
                "Нельзя удалить автора, у которого есть книги"
            )
        self.authors.delete(author)