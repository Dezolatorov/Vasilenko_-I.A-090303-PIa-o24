from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from bson import ObjectId
from bson.errors import InvalidId

from app.errors import AppError
from app.mongodb import MongoDatabase


class InvalidBookId(AppError):
    code = "INVALID_ID"

    def __init__(self, value: Any) -> None:
        super().__init__(f"Некорректный идентификатор книги: {value!r}")


def to_object_id(value: Any) -> ObjectId:
    try:
        return ObjectId(str(value))
    except (InvalidId, TypeError) as error:
        raise InvalidBookId(value) from error


class MongoBookRepository:
    def __init__(self, database: MongoDatabase) -> None:
        self.database = database
        self.collection = database.books

    def insert(self, document: Dict[str, Any]) -> str:
        result = self.collection.insert_one(document)
        return str(result.inserted_id)

    def get(self, book_id: Any) -> Optional[Dict[str, Any]]:
        return self.collection.find_one({"_id": to_object_id(book_id)})

    def list(self, sort_field: str = "title", descending: bool = False, limit: int = 50):
        direction = -1 if descending else 1
        return list(self.collection.find().sort(sort_field, direction).limit(limit))

    def find_by_title(self, title: str) -> List[Dict[str, Any]]:
        return list(self.collection.find({"title": {"$regex": title, "$options": "i"}}))

    def search(
        self,
        query: str = "",
        genre: Optional[str] = None,
        min_year: Optional[int] = None,
        available_only: bool = False,
        limit: int = 20,
        descending_year: bool = True,
    ) -> List[Dict[str, Any]]:
        conditions: List[Dict[str, Any]] = []
        if query:
            conditions.append(
                {
                    "$or": [
                        {"title": {"$regex": query, "$options": "i"}},
                        {"authors": {"$regex": query, "$options": "i"}},
                        {"publisher.name": {"$regex": query, "$options": "i"}},
                    ]
                }
            )
        if genre:
            conditions.append({"genres": genre})
        if min_year is not None:
            conditions.append({"year": {"$gte": min_year}})
        if available_only:
            conditions.append({"copies.available": {"$gt": 0}})

        query_filter = {"$and": conditions} if conditions else {}
        direction = -1 if descending_year else 1
        return list(self.collection.find(query_filter).sort("year", direction).limit(limit))

    def by_genre(self, genre: str) -> List[Dict[str, Any]]:
        return list(self.collection.find({"genres": genre}).sort("title", 1))

    def by_publisher_city(self, city: str) -> List[Dict[str, Any]]:
        return list(self.collection.find({"publisher.city": city}).sort("title", 1))

    def by_reader(self, reader_name: str) -> List[Dict[str, Any]]:
        return list(self.collection.find({"readers.reader": reader_name}).sort("title", 1))

    def update(self, book_id: Any, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        oid = to_object_id(book_id)
        if not fields:
            return self.get(book_id)
        self.collection.update_one({"_id": oid}, {"$set": fields})
        return self.collection.find_one({"_id": oid})

    def delete(self, book_id: Any) -> bool:
        result = self.collection.delete_one({"_id": to_object_id(book_id)})
        return result.deleted_count > 0

    def borrow(self, book_id: Any, reader: str, days: int = 14) -> Optional[Dict[str, Any]]:
        oid = to_object_id(book_id)
        today = date.today()
        entry = {
            "reader": reader,
            "loan_date": today.isoformat(),
            "due_date": (today + timedelta(days=days)).isoformat(),
            "returned": False,
        }
        result = self.collection.find_one_and_update(
            {"_id": oid, "copies.available": {"$gt": 0}},
            {
                "$inc": {"copies.available": -1},
                "$push": {"readers": entry},
                "$set": {"status": "loaned"},
            },
            return_document=True,
        )
        return result

    def give_back(self, book_id: Any, reader: str) -> Optional[Dict[str, Any]]:
        oid = to_object_id(book_id)
        document = self.collection.find_one({"_id": oid})
        if document is None:
            return None

        readers = document.get("readers", [])
        updated = False
        for entry in readers:
            if entry.get("reader") == reader and not entry.get("returned"):
                entry["returned"] = True
                updated = True
                break
        if not updated:
            return None

        copies = document.get("copies", {"total": 0, "available": 0})
        copies["available"] = min(copies.get("total", 0), copies.get("available", 0) + 1)
        status = "available" if copies["available"] > 0 else "archived"

        self.collection.update_one(
            {"_id": oid},
            {"$set": {"readers": readers, "copies": copies, "status": status}},
        )
        return self.collection.find_one({"_id": oid})

    def count_by_status(self) -> List[Dict[str, Any]]:
        pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        return list(self.collection.aggregate(pipeline))

    def count_by_genre(self) -> List[Dict[str, Any]]:
        pipeline = [
            {"$unwind": "$genres"},
            {"$group": {"_id": "$genres", "books": {"$sum": 1}}},
            {"$sort": {"books": -1}},
        ]
        return list(self.collection.aggregate(pipeline))

    def top_authors(self, limit: int = 5) -> List[Dict[str, Any]]:
        pipeline = [
            {"$unwind": "$authors"},
            {
                "$group": {
                    "_id": "$authors",
                    "books": {"$sum": 1},
                    "copies": {"$sum": "$copies.total"},
                }
            },
            {"$sort": {"copies": -1, "books": -1}},
            {"$limit": limit},
        ]
        return list(self.collection.aggregate(pipeline))

    def statistics(self) -> Dict[str, Any]:
        total = self.collection.count_documents({})
        available = self.collection.count_documents({"copies.available": {"$gt": 0}})
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "copies": {"$sum": "$copies.total"},
                    "available": {"$sum": "$copies.available"},
                    "min_year": {"$min": "$year"},
                    "max_year": {"$max": "$year"},
                }
            }
        ]
        aggregated = list(self.collection.aggregate(pipeline))
        row = aggregated[0] if aggregated else {}
        return {
            "books": total,
            "available_books": available,
            "copies_total": int(row.get("copies", 0)),
            "copies_available": int(row.get("available", 0)),
            "min_year": int(row.get("min_year", 0) or 0),
            "max_year": int(row.get("max_year", 0) or 0),
        }

    def ensure_indexes(self) -> List[str]:
        return self.database.create_indexes()
