"""Unit-тесты хэширования паролей и JWT (без БД)."""
import pytest
import jwt as pyjwt

from src.library.auth import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from src.library.config import settings
from src.library.exceptions import AuthenticationException


def test_hash_password_returns_salt_and_digest():
    h = hash_password("secret")
    assert "$" in h
    digest, salt = h.split("$", 1)
    assert len(salt) == 32
    assert len(digest) > 0


def test_verify_password_correct():
    h = hash_password("secret")
    assert verify_password("secret", h) is True


def test_verify_password_wrong():
    h = hash_password("secret")
    assert verify_password("wrong", h) is False


@pytest.mark.parametrize("password", ["", "a", "пароль123", " "*8, "x"*128])
def test_hash_verify_roundtrip_various(password):
    # Пустые/короткие строки тоже должны проходить корректно на уровне функции
    h = hash_password(password)
    assert verify_password(password, h) is True
    assert verify_password(password + "z", h) is False


def test_hash_is_randomized():
    assert hash_password("same") != hash_password("same")


def test_verify_password_tampered_stored():
    h = hash_password("secret")
    # ломаем digest
    bad_digest, salt = h.split("$", 1)
    corrupted = ("0" * len(bad_digest)) + "$" + salt
    assert verify_password("secret", corrupted) is False


def test_create_access_token_contains_sub_and_role():
    token = create_access_token(7, "ADMIN")
    payload = pyjwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    assert payload["sub"] == "7"
    assert payload["role"] == "ADMIN"


def test_decode_token_valid():
    token = create_access_token(3, "USER")
    payload = decode_token(token)
    assert payload["sub"] == "3"


def test_decode_token_invalid_raises():
    with pytest.raises(AuthenticationException):
        decode_token("not.a.jwt")


def test_decode_token_tampered_raises():
    token = create_access_token(1, "USER")
    parts = token.split(".")
    parts[1] = "eyJzdWIiOiI5OTkifQ"  # подмена payload sub=999
    with pytest.raises(AuthenticationException):
        decode_token(".".join(parts))