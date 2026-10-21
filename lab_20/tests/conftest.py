import pathlib
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.database import Base, get_db  # noqa: E402
from src.main import create_app  # noqa: E402
from src.models import Author, Book  # noqa: E402


@pytest.fixture
def db_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    TestingSession = sessionmaker(bind=db_engine, autocommit=False, autoflush=False)
    session = TestingSession()
    yield session
    session.close()
    db_engine.dispose()


@pytest.fixture
def client(db_engine):
    TestingSession = sessionmaker(bind=db_engine, autocommit=False, autoflush=False)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    # без `with` lifespan не запускается, поэтому таблицы уже созданы фикстурой
    return TestClient(app)


@pytest.fixture
def seeded(db_session):
    author = Author(full_name="Лев Толстой")
    db_session.add(author)
    db_session.flush()
    book = Book(
        title="Война и мир",
        author_id=author.id,
        year=1869,
        isbn="9785171180989",
        copies_total=2,
        copies_available=2,
        description="роман-эпопея",
    )
    db_session.add(book)
    db_session.commit()
    db_session.refresh(book)
    return {"author": author, "book": book}
