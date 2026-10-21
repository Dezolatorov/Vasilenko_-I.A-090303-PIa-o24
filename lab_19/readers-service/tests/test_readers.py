"""Тесты readers-service: 5 unit + 2 интеграционных + 1 межсервисной/недоступность."""

import pytest

from app.models import Reader
from app.repositories import ReaderRepository
from app.schemas.schemas import ReaderCreate, ReaderUpdate
from app.services import ReadersService
from shared.storage import JsonStorage


@pytest.fixture()
def service(tmp_path):
    storage = JsonStorage(str(tmp_path / "readers.json"))
    repo = ReaderRepository(storage)
    return ReadersService(repo)


# ---------- 5 unit-тестов ----------
def test_unit_create_reader(service):
    reader = service.create_reader(ReaderCreate(full_name="Иван Петров", email="ivan@test.ru", phone="+7"))
    assert reader.id
    assert reader.active is True


def test_unit_get_reader(service):
    created = service.create_reader(ReaderCreate(full_name="Анна", email="anna@test.ru"))
    got = service.get_reader(created.id)
    assert got is not None and got.full_name == "Анна"


def test_unit_duplicate_email_raises(service):
    service.create_reader(ReaderCreate(full_name="А", email="dup@test.ru"))
    with pytest.raises(ValueError):
        service.create_reader(ReaderCreate(full_name="Б", email="dup@test.ru"))


def test_unit_update_reader(service):
    created = service.create_reader(ReaderCreate(full_name="А", email="a@test.ru"))
    updated = service.update_reader(created.id, ReaderUpdate(full_name="Б", phone="+7"))
    assert updated is not None and updated["full_name"] == "Б"


def test_unit_delete_reader(service):
    created = service.create_reader(ReaderCreate(full_name="А", email="c@test.ru"))
    assert service.delete_reader(created.id) is True
    assert service.get_reader(created.id) is None


def test_unit_check_reader(service):
    created = service.create_reader(ReaderCreate(full_name="А", email="ch@test.ru"))
    info = service.check_reader(created.id)
    assert info["exists"] is True and info["active"] is True
    assert service.check_reader("nonexistent")["exists"] is False


# ---------- 2 интеграционных теста (через HTTP TestClient) ----------
@pytest.fixture()
def client(tmp_path, monkeypatch):
    from app.api import routes
    routes.init_service(str(tmp_path / "readers.json"))
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)


def test_integration_create_and_list(client):
    r = client.post("/readers", json={"full_name": "Игорь", "email": "igor@test.ru", "phone": "+7900"})
    assert r.status_code == 201
    rid = r.json()["id"]
    rlist = client.get("/readers")
    assert rlist.status_code == 200
    assert any(c["id"] == rid for c in rlist.json())


def test_integration_health_and_404(client):
    assert client.get("/health").json()["status"] == "healthy"
    r = client.get("/readers/does-not-exist")
    assert r.status_code == 404


# ---------- 1 тест недоступности/взаимодействия ----------
def test_interaction_check_reader_endpoint(client):
    created = client.post("/readers", json={"full_name": "Проверка", "email": "p@test.ru"}).json()
    r = client.get(f"/readers/check/{created['id']}")
    assert r.status_code == 200 and r.json()["exists"] is True


def test_unavailability_duplicate_conflict(client):
    client.post("/readers", json={"full_name": "Д", "email": "dup@test.ru"})
    r = client.post("/readers", json={"full_name": "Е", "email": "dup@test.ru"})
    assert r.status_code == 409