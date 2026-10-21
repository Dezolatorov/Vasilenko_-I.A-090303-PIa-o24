from __future__ import annotations

from decimal import Decimal, InvalidOperation
from time import perf_counter
from typing import Any, Dict, List, Optional

from app.cache import BookCache
from app.errors import NotFoundError, ValidationError
from app.models import STATUSES
from app.mongodb import MongoDatabase
from app.repository import InvalidBookId, MongoBookRepository


class LibraryService:
    def __init__(self, database: MongoDatabase, cache: BookCache) -> None:
        self.database = database
        self.cache = cache
        self.repository = MongoBookRepository(database)

    def prepare(self) -> List[str]:
        return self.repository.ensure_indexes()

    def add_book(self, data: Dict[str, Any]) -> Dict[str, Any]:
        document = self._validate(data)
        book_id = self.repository.insert(document)
        return self._serialize(self.repository.get(book_id) or document)

    def get_book(self, book_id: Any, use_cache: bool = True) -> Dict[str, Any]:
        key = str(book_id)

        if use_cache:
            cached = self.cache.get_book(key)
            if cached is not None:
                self.cache.record_hit()
                self.cache.register_view(key, cached.get("title", ""), self._main_genre(cached))
                return cached
            self.cache.record_miss()

        document = self.repository.get(book_id)
        if document is None:
            raise NotFoundError("Книга", book_id)

        payload = self._serialize(document)
        if use_cache:
            self.cache.put_book(key, payload)
        self.cache.register_view(key, payload["title"], self._main_genre(payload))
        return payload

    def find_by_title(self, title: str) -> Dict[str, Any]:
        if not title or not title.strip():
            raise ValidationError("Строка поиска не может быть пустой")
        query = title.strip()
        items = [self._serialize(item) for item in self.repository.find_by_title(query)]
        history = self.cache.record_search(query)
        return {"query": query, "count": len(items), "items": items, "history": history}

    def search(
        self,
        query: str = "",
        genre: Optional[str] = None,
        min_year: Optional[int] = None,
        available_only: bool = False,
        limit: int = 20,
    ) -> Dict[str, Any]:
        items = [
            self._serialize(item)
            for item in self.repository.search(
                query=query or "",
                genre=genre,
                min_year=min_year,
                available_only=available_only,
                limit=limit,
            )
        ]
        history = self.cache.record_search(query) if query else self.cache.search_history()
        return {
            "query": query,
            "genre": genre,
            "count": len(items),
            "items": items,
            "history": history,
        }

    def list_books(
        self,
        sort: str = "title",
        descending: bool = False,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        rows = self.repository.list(sort_field=sort, descending=descending, limit=limit)
        return [self._serialize(row) for row in rows]

    def by_genre(self, genre: str) -> List[Dict[str, Any]]:
        return [self._serialize(row) for row in self.repository.by_genre(genre)]

    def by_publisher_city(self, city: str) -> List[Dict[str, Any]]:
        return [self._serialize(row) for row in self.repository.by_publisher_city(city)]

    def by_reader(self, reader: str) -> List[Dict[str, Any]]:
        return [self._serialize(row) for row in self.repository.by_reader(reader)]

    def update_book(self, book_id: Any, fields: Dict[str, Any]) -> Dict[str, Any]:
        allowed = {"title", "authors", "publisher", "genres", "year", "status"}
        unknown = set(fields) - allowed - {"copies.total", "copies.available"}
        if unknown:
            raise ValidationError(f"Неизвестные поля: {', '.join(sorted(unknown))}")

        self._validate_update(fields)
        updated = self.repository.update(book_id, fields)
        if updated is None:
            raise NotFoundError("Книга", book_id)
        self.cache.invalidate_book(str(book_id))
        return self._serialize(updated)

    def delete_book(self, book_id: Any) -> None:
        if not self.repository.delete(book_id):
            raise NotFoundError("Книга", book_id)
        self.cache.invalidate_book(str(book_id))

    def borrow_book(self, book_id: Any, reader: str, days: int = 14) -> Dict[str, Any]:
        reader = (reader or "").strip()
        if not reader:
            raise ValidationError("Имя читателя обязательно")
        if not 1 <= days <= 90:
            raise ValidationError("Срок выдачи должен быть от 1 до 90 дней")

        updated = self.repository.borrow(book_id, reader, days)
        if updated is None:
            if self.repository.get(book_id) is None:
                raise NotFoundError("Книга", book_id)
            raise ValidationError("Свободных экземпляров нет")

        self.cache.invalidate_book(str(book_id))
        return self._serialize(updated)

    def return_book(self, book_id: Any, reader: str) -> Dict[str, Any]:
        reader = (reader or "").strip()
        if not reader:
            raise ValidationError("Имя читателя обязательно")

        updated = self.repository.give_back(book_id, reader)
        if updated is None:
            if self.repository.get(book_id) is None:
                raise NotFoundError("Книга", book_id)
            raise ValidationError("У этого читателя нет активной выдачи данной книги")

        self.cache.invalidate_book(str(book_id))
        return self._serialize(updated)

    def statistics(self) -> Dict[str, Any]:
        stats = self.repository.statistics()
        stats["by_status"] = self.repository.count_by_status()
        stats["by_genre"] = self.repository.count_by_genre()
        stats["top_authors"] = self.repository.top_authors()
        stats["cache"] = self.cache.hit_rate()
        return stats

    def cache_info(self) -> Dict[str, Any]:
        return self.cache.info()

    def popular_books(self, limit: int = 5) -> List[Dict[str, Any]]:
        return self.cache.popular_books(limit)

    def clear_cache(self) -> int:
        return self.cache.clear()

    def benchmark(self, sizes: tuple = (100, 1000, 10000), book_id: Optional[Any] = None) -> List[Dict[str, Any]]:
        books = self.repository.list(limit=1)
        if not books:
            raise ValidationError("В базе нет книг для теста производительности")

        target = str(book_id) if book_id is not None else str(books[0]["_id"])
        self.get_book(target)

        rows: List[Dict[str, Any]] = []
        for count in sizes:
            started = perf_counter()
            for _ in range(count):
                self.repository.get(target)
            mongo_ms = (perf_counter() - started) * 1000

            started = perf_counter()
            for _ in range(count):
                self.cache.get_book(target)
            redis_ms = (perf_counter() - started) * 1000

            rows.append(
                {
                    "count": count,
                    "mongo_ms": round(mongo_ms, 2),
                    "redis_ms": round(redis_ms, 2),
                    "mongo_avg_ms": round(mongo_ms / count, 4),
                    "redis_avg_ms": round(redis_ms / count, 4),
                }
            )
        return rows

    def _serialize(self, document: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(document)
        payload["_id"] = str(payload.get("_id", ""))
        payload["readers"] = [dict(item) for item in payload.get("readers", [])]
        return payload

    @staticmethod
    def _main_genre(document: Dict[str, Any]) -> Optional[str]:
        genres = document.get("genres") or []
        return genres[0] if genres else None

    @staticmethod
    def _validate(data: Dict[str, Any]) -> Dict[str, Any]:
        title = str(data.get("title") or "").strip()
        if not title:
            raise ValidationError("Название книги обязательно")

        authors = data.get("authors") or []
        if not isinstance(authors, list) or not authors:
            raise ValidationError("Укажите хотя бы одного автора (массив authors)")
        authors = [str(author).strip() for author in authors if str(author).strip()]
        if not authors:
            raise ValidationError("Укажите хотя бы одного автора (массив authors)")

        genres = data.get("genres") or []
        if not isinstance(genres, list) or not genres:
            raise ValidationError("Укажите хотя бы один жанр (массив genres)")
        genres = [str(genre).strip() for genre in genres if str(genre).strip()]
        if not genres:
            raise ValidationError("Укажите хотя бы один жанр (массив genres)")

        publisher = data.get("publisher") or {}
        if not isinstance(publisher, dict) or not str(publisher.get("name", "")).strip():
            raise ValidationError("Поле publisher должно содержать название издательства")

        try:
            year = int(data.get("year"))
        except (TypeError, ValueError) as error:
            raise ValidationError("Год издания должен быть целым числом") from error
        if not 1400 <= year <= 2100:
            raise ValidationError("Год издания должен быть в диапазоне 1400-2100")

        try:
            total = int(data.get("copies_total", data.get("copies", {}).get("total", 0)))
            available = int(
                data.get("copies_available", data.get("copies", {}).get("available", total))
            )
        except (TypeError, ValueError) as error:
            raise ValidationError("Количество экземпляров должно быть целым числом") from error
        if total < 0:
            raise ValidationError("Количество экземпляров не может быть отрицательным")
        if not 0 <= available <= total:
            raise ValidationError("Доступных экземпляров не может быть больше общего количества")

        status = str(data.get("status") or "available")
        if status not in STATUSES:
            raise ValidationError(f"Статус должен быть одним из: {', '.join(STATUSES)}")

        return {
            "title": title,
            "authors": authors,
            "publisher": {
                "name": str(publisher.get("name")).strip(),
                "city": str(publisher.get("city", "")).strip(),
                "year": int(publisher.get("year", year) or year),
            },
            "genres": genres,
            "year": year,
            "copies": {"total": total, "available": available},
            "readers": [],
            "status": status,
        }

    @staticmethod
    def _validate_update(fields: Dict[str, Any]) -> None:
        if "year" in fields and not 1400 <= int(fields["year"]) <= 2100:
            raise ValidationError("Год издания должен быть в диапазоне 1400-2100")
        if "status" in fields and fields["status"] not in STATUSES:
            raise ValidationError(f"Статус должен быть одним из: {', '.join(STATUSES)}")
        if "copies.available" in fields and int(fields["copies.available"]) < 0:
            raise ValidationError("Доступных экземпляров не может быть меньше нуля")
        if "copies.total" in fields and int(fields["copies.total"]) < 0:
            raise ValidationError("Общее количество экземпляров не может быть отрицательным")
