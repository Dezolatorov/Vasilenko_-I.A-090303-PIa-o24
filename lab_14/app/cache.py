from __future__ import annotations

import json
from typing import Any, Dict, Optional

from app.config import settings


class BookCache:
    def __init__(
        self,
        url: Optional[str] = None,
        ttl: Optional[int] = None,
        force_mock: bool = False,
    ) -> None:
        self.default_ttl = ttl if ttl is not None else settings.cache_ttl
        self.client, self.mode = self._connect(url or settings.redis_url, force_mock)

    @staticmethod
    def _connect(url: str, force_mock: bool):
        if not force_mock:
            try:
                import redis

                client = redis.Redis.from_url(
                    url,
                    socket_connect_timeout=0.3,
                    socket_timeout=0.5,
                    decode_responses=True,
                )
                client.ping()
                return client, "redis"
            except Exception:
                pass

        import fakeredis

        return fakeredis.FakeStrictRedis(decode_responses=True), "fakeredis"

    def _key(self, book_id: int) -> str:
        return f"book:{book_id}"

    def get(self, book_id: int) -> Optional[Dict[str, Any]]:
        raw = self.client.get(self._key(book_id))
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    def set(self, book_id: int, payload: Dict[str, Any]) -> None:
        self.client.set(
            self._key(book_id),
            json.dumps(payload, ensure_ascii=False, default=str),
            ex=self.default_ttl,
        )

    def delete(self, book_id: int) -> None:
        self.client.delete(self._key(book_id))

    def ttl(self, book_id: int) -> int:
        return int(self.client.ttl(self._key(book_id)))

    def info(self) -> Dict[str, Any]:
        keys = sorted(self.client.keys("book:*"))
        return {"mode": self.mode, "keys": len(keys), "ttl": self.default_ttl}

    def clear(self) -> int:
        keys = list(self.client.keys("book:*"))
        if keys:
            self.client.delete(*keys)
        return len(keys)
