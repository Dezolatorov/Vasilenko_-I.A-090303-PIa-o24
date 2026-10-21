import sys
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.cache import BookCache
from app.mongodb import MongoDatabase
from app.redis_client import RedisCache
from app.seed import seed_database
from app.service import LibraryService


@pytest.fixture()
def database() -> MongoDatabase:
    db = MongoDatabase(db_name="library_test", force_mock=True)
    seed_database(db)
    return db


@pytest.fixture()
def cache() -> BookCache:
    return BookCache(RedisCache(force_mock=True, prefix="test"), ttl=300)


@pytest.fixture()
def service(database: MongoDatabase, cache: BookCache) -> LibraryService:
    return LibraryService(database, cache)
