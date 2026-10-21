"""Авторизация: хэширование паролей, JWT-токены, FastAPI-зависимости.

Пароль хэшируется солью стандартным модулем hashlib (PBKDF2-HMAC-SHA256) -
без внешних зависимостей bcrypt/passlib в среде без них.
Авторизация выполнена на уровне, достаточном для учебного проекта.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .config import settings
from .database import get_session
from .exceptions import AuthenticationException
from .models import Reader

_bearer = HTTPBearer(auto_error=False)

PBKDF2_ITERATIONS = 120_000


def hash_password(password: str) -> str:
    """Возвращает строку digest$salt с PBKDF2-SHA256."""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS
    )
    return f"{digest.hex()}${salt}"


def verify_password(password: str, stored: str) -> bool:
    try:
        digest_hex, salt = stored.split("$", 1)
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS
    )
    return hmac.compare_digest(digest.hex(), digest_hex)


def create_access_token(reader_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(reader_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(
            token, settings.secret_key, algorithms=[settings.jwt_algorithm]
        )
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationException("Токен истёк") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthenticationException("Недействительный токен") from exc


def get_current_reader(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_session),
) -> Reader:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не предоставлен токен авторизации",
        )
    try:
        payload = decode_token(credentials.credentials)
    except AuthenticationException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный или истёкший токен",
        )
    reader = db.get(Reader, int(payload["sub"]))
    if reader is None or not reader.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден или деактивирован",
        )
    return reader


def require_role(*roles: str):
    """Зависимость, требующая одну из переданных ролей."""

    def _dep(reader: Reader = Depends(get_current_reader)) -> Reader:
        if reader.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для операции",
            )
        return reader

    return _dep


require_admin = require_role("ADMIN")
require_user = require_role("USER", "ADMIN")