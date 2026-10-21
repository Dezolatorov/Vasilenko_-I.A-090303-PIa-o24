from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from app.redis_client import RedisCache

BOOK_KEY = "book"
HISTORY_KEY = "search:history"
POPULAR_KEY = "popular:books"
GENRE_KEY = "stats:genres"
HITS_KEY = "cache:hits"
MISSES_KEY = "cache:misses"
DEFAULT_TTL = 300
HISTORY_TTL = 3600


class BookCache:
    def __init__(self, redis: RedisCache, ttl: int = DEFAULT_TTL) -> None:
        self.redis = redis
        self.ttl = ttl

    def get_book(self, book_id: str) -> Optional[Dict[str, Any]]:
        return self.redis.get_json(f"{BOOK_KEY}:{book_id}")

    def put_book(self, book_id: str, document: Dict[str, Any]) -> None:
        payload = dict(document)
        payload["_id"] = str(payload.get("_id", book_id))
        self.redis.set_json(f"{BOOK_KEY}:{book_id}", payload, ttl=self.ttl)

    def invalidate_book(self, book_id: str) -> bool:
        return self.redis.delete(f"{BOOK_KEY}:{book_id}")

    def book_ttl(self, book_id: str) -> int:
        return self.redis.ttl(f"{BOOK_KEY}:{book_id}")

    def record_hit(self) -> int:
        return self.redis.incr(HITS_KEY)

    def record_miss(self) -> int:
        return self.redis.incr(MISSES_KEY)

    def hit_rate(self) -> Dict[str, int]:
        hits = self.redis.get_int(HITS_KEY)
        misses = self.redis.get_int(MISSES_KEY)
        return {"hits": hits, "misses": misses, "total": hits + misses}

    def record_search(self, query: str) -> List[str]:
        self.redis.lpush_trim(HISTORY_KEY, query, max_len=10, ttl=HISTORY_TTL)
        self.redis.incr(f"search:count:{query}")
        return self.search_history()

    def search_history(self, limit: int = 10) -> List[str]:
        return self.redis.lrange(HISTORY_KEY, 0, limit - 1)

    def register_view(self, book_id: str, title: str, genre: Optional[str] = None) -> None:
        self.redis.zincrby(POPULAR_KEY, title, 1)
        if genre:
            self.redis.hincrby(GENRE_KEY, genre, 1)

    def popular_books(self, limit: int = 5) -> List[Dict[str, Any]]:
        rows = self.redis.zrevrange(POPULAR_KEY, 0, limit - 1, withscores=True)
        return [{"title": title, "views": int(score)} for title, score in rows]

    def genre_views(self) -> Dict[str, str]:
        return self.redis.hgetall(GENRE_KEY)

    def info(self) -> Dict[str, Any]:
        keys = self.redis.keys()
        book_keys = [key for key in keys if ":book:" in key]
        return {
            "mode": self.redis.mode,
            "keys_total": len(keys),
            "book_keys": len(book_keys),
            "keys": keys[:10],
            "history": self.search_history(),
            "hits": self.hit_rate(),
        }

    def clear(self) -> int:
        return self.redis.clear()
