import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.database import Base, build_engine, get_db
from app.deps import cache
from app.main import create_app
from app.models import Book
from app.seed import BOOKS


@pytest.fixture()
def client(tmp_path: Path):
    engine = build_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, expire_on_commit=False)

    with testing_session() as session:
        session.add_all([Book(**row) for row in BOOKS])
        session.commit()

    application = create_app(with_seed=False)

    def override_get_db():
        session = testing_session()
        try:
            yield session
        finally:
            session.close()

    application.dependency_overrides[get_db] = override_get_db
    cache.clear()

    with TestClient(application) as test_client:
        yield test_client

    cache.clear()
