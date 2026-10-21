"""API-тесты аутентификации, ролей и доступа."""
import pytest

from tests.conftest import api_headers, register_and_token


def test_register_returns_token(client):
    token = register_and_token(client, username="newuser", email="new@test.ru")
    assert isinstance(token, str) and len(token) > 20


def test_register_duplicate_username_conflict(client):
    register_and_token(client, username="dup", email="a@test.ru")
    r = client.post("/auth/register", json={
        "username": "dup", "email": "b@test.ru", "full_name": "Другой",
        "password": "secret1",
    })
    assert r.status_code == 409
    assert r.json()["error"] == "CONFLICT"


def test_register_duplicate_email_conflict(client):
    register_and_token(client, username="ema_1", email="same@test.ru")
    r = client.post("/auth/register", json={
        "username": "ema_2", "email": "same@test.ru", "full_name": "Другой",
        "password": "secret1",
    })
    assert r.status_code == 409


@pytest.mark.parametrize("field,bad_value", [
    ("username", "a"),               # слишком короткий
    ("password", "123"),             # слишком короткий пароль
    ("email", "не-почта"),           # невалидный email
    ("username", "имя с пробелом"),  # недопустимые символы
])
def test_register_invalid_data_422(client, field, bad_value):
    data = {"username": "valid_user", "email": "ok@test.ru",
            "full_name": "Нормальный", "password": "secret1"}
    data[field] = bad_value
    r = client.post("/auth/register", json=data)
    assert r.status_code == 422


def test_login_success(client):
    token = register_and_token(client, username="logusr", email="log@test.ru")
    r = client.post("/auth/login", json={"username": "logusr", "password": "secret1"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_wrong_password(client):
    register_and_token(client, username="loguser2", email="log2@test.ru")
    r = client.post("/auth/login", json={"username": "loguser2", "password": "wrongpass"})
    assert r.status_code == 401
    assert r.json()["error"] == "AUTHENTICATION_FAILED"


def test_login_unknown_user(client):
    r = client.post("/auth/login", json={"username": "nobody", "password": "secret1"})
    assert r.status_code == 401


def test_unauthorized_protected_route(client):
    # Без токена - 401
    r = client.get("/books")
    assert r.status_code == 401


def test_invalid_token(client):
    r = client.get("/books", headers=api_headers("bad.token.here"))
    assert r.status_code == 401


def test_get_me(client):
    token = register_and_token(client, username="meuser", email="me@test.ru")
    r = client.get("/readers/me", headers=api_headers(token))
    assert r.status_code == 200
    assert r.json()["username"] == "meuser"
    assert r.json()["role"] == "USER"


def test_user_cannot_list_all_readers_forbidden(client):
    token = register_and_token(client, username="norole", email="nr@test.ru")
    r = client.get("/readers", headers=api_headers(token))
    assert r.status_code == 403


def test_user_cannot_create_book_forbidden(client):
    token = register_and_token(client, username="nobook", email="nb@test.ru")
    r = client.post("/books", headers=api_headers(token),
                    json={"title": "X", "author_id": 1, "year": 2000})
    assert r.status_code == 403


def test_get_missing_reader_404(client):
    token = register_and_token(client, username="readerA", email="a@test.ru")
    r = client.get("/readers/999999", headers=api_headers(token))
    assert r.status_code == 404
    assert r.json()["error"] == "ENTITY_NOT_FOUND"