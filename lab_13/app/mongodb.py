from __future__ import annotations

import os
from typing import Any, List, Optional

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "library")


class MongoUnavailable(RuntimeError):
    """MongoDB недоступна и резервное хранилище не подключено."""


def create_client(url: Optional[str] = None, force_mock: bool = False) -> tuple[Any, str]:
    if not force_mock:
        try:
            from pymongo import MongoClient

            client = MongoClient(url or MONGO_URL, serverSelectionTimeoutMS=800)
            client.admin.command("ping")
            return client, "mongodb"
        except Exception:
            pass

    import mongomock

    return mongomock.MongoClient(), "mongomock"


class MongoDatabase:
    def __init__(
        self,
        url: Optional[str] = None,
        db_name: str = MONGO_DB,
        force_mock: bool = False,
    ) -> None:
        self.client, self.mode = create_client(url, force_mock)
        self.name = db_name
        self.db = self.client[db_name]

    @property
    def books(self):
        return self.db["books"]

    def ping(self) -> bool:
        try:
            if self.mode == "mongodb":
                self.client.admin.command("ping")
            else:
                self.db.list_collection_names()
            return True
        except Exception:
            return False

    def create_indexes(self) -> List[str]:
        collection = self.books
        collection.create_index([("title", 1)], name="idx_title")
        collection.create_index([("genres", 1), ("year", -1)], name="idx_genres_year")
        collection.create_index([("publisher.city", 1)], name="idx_publisher_city")
        return sorted(collection.index_information().keys())

    def drop(self) -> None:
        self.books.drop()

    def close(self) -> None:
        try:
            self.client.close()
        except Exception:
            pass
