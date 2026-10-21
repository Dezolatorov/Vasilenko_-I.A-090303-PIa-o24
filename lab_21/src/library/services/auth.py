"""Сервис аутентификации и управления читателями."""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..auth import create_access_token, hash_password, verify_password
from ..exceptions import AuthenticationException, AuthorizationException, ConflictException
from ..models import Reader
from ..repositories import ReaderRepository
from ..schemas import LoginRequest, ReaderUpdate, UserRegister


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.readers = ReaderRepository(db)

    def register(self, data: UserRegister, role: str = "USER") -> Reader:
        self.readers.ensure_unique(data.username, data.email)
        reader = Reader(
            username=data.username,
            email=data.email,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
            role=role,
        )
        return self.readers.add(reader)

    def login(self, data: LoginRequest) -> Reader:
        reader = self.readers.get_by_username(data.username)
        if reader is None or not verify_password(data.password, reader.hashed_password):
            raise AuthenticationException("Неверный логин или пароль")
        if not reader.is_active:
            raise AuthorizationException("Учётная запись деактивирована")
        return reader

    def token_for(self, reader: Reader) -> str:
        return create_access_token(reader.id, reader.role)


class ReaderService:
    def __init__(self, db: Session):
        self.db = db
        self.readers = ReaderRepository(db)

    def get(self, reader_id: int) -> Reader:
        return self.readers.get(reader_id)

    def list_all(self) -> list[Reader]:
        return self.readers.list_all()

    def update(self, reader_id: int, data: ReaderUpdate, actor: Reader) -> Reader:
        reader = self.readers.get(reader_id)
        if actor.role != "ADMIN" and actor.id != reader_id:
            raise AuthorizationException("Можно редактировать только свою учётную запись")
        if data.email is not None and data.email != reader.email:
            existing = self.readers.get_by_email(data.email)
            if existing is not None and existing.id != reader.id:
                raise ConflictException("Пользователь с таким email уже зарегистрирован")
            reader.email = data.email
        if data.full_name is not None:
            reader.full_name = data.full_name
        self.db.flush()
        return reader

    def delete(self, reader_id: int, actor: Reader) -> None:
        if actor.id == reader_id:
            raise ConflictException("Нельзя удалить собственную учётную запись")
        reader = self.readers.get(reader_id)
        self.readers.delete(reader)