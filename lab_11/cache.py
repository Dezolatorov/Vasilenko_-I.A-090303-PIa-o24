"""Кэш на Redis: паттерн cache-aside, TTL и инвалидация."""

from typing import Any

import redis

import config
from exceptions import ApiError


class CacheUnavailableError(ApiError):
    """Кэш недоступен: приложение продолжает работать с основной БД."""

    status_code = 503
    code = "CACHE_UNAVAILABLE"
    message = "Cache is unavailable"


class RedisCache:
    """Обёртка над redis-py: строковые ключи, счётчики, TTL, статистика."""

    def __init__(
        self,
        host: str = config.REDIS_HOST,
        port: int = config.REDIS_PORT,
        prefix: str = config.CACHE_PREFIX,
        ttl: int = config.CACHE_TTL,
    ) -> None:
        self.prefix = prefix
        self.ttl = ttl
        self.hits = 0
        self.misses = 0
        self.client = redis.Redis(
            host=host,
            port=port,
            decode_responses=True,
            socket_timeout=2.0,
            protocol=2,
        )

    # --- служебные операции -------------------------------------------------
    def ping(self) -> bool:
        try:
            return bool(self.client.ping())
        except redis.RedisError:
            return False

    def _key(self, name: str) -> str:
        return f"{self.prefix}:{name}"

    # --- базовые команды Redis ---------------------------------------------
    def get(self, name: str) -> str | None:
        try:
            return self.client.get(self._key(name))
        except redis.RedisError:
            return None

    def set(self, name: str, value: str, ttl: int | None = None) -> None:
        try:
            self.client.set(self._key(name), value, ex=ttl if ttl is not None else self.ttl)
        except redis.RedisError:
            pass

    def delete(self, *names: str) -> int:
        try:
            return int(self.client.delete(*[self._key(name) for name in names]))
        except redis.RedisError:
            return 0

    def expire(self, name: str, ttl: int) -> bool:
        try:
            return bool(self.client.expire(self._key(name), ttl))
        except redis.RedisError:
            return False

    def ttl_of(self, name: str) -> int:
        try:
            return int(self.client.ttl(self._key(name)))
        except redis.RedisError:
            return -2

    def incr(self, name: str) -> int:
        try:
            return int(self.client.incr(self._key(name)))
        except redis.RedisError:
            return 0

    def keys(self, pattern: str = "*") -> list[str]:
        try:
            found = self.client.keys(self._key(pattern))
        except redis.RedisError:
            return []
        return sorted(key[len(self.prefix) + 1:] for key in found)

    def stats(self) -> dict[str, Any]:
        total = self.hits + self.misses
        return {
            "backend": "redis",
            "prefix": self.prefix,
            "default_ttl": self.ttl,
            "hits": self.hits,
            "misses": self.misses,
            "hit_ratio": round(self.hits / total, 3) if total else 0.0,
            "keys": len(self.keys("*")),
        }

    # --- предметные операции кэша ------------------------------------------
    def get_product_json(self, name: str) -> str | None:
        """Прочитать значение и учесть попадание/промах."""
        value = self.get(name)
        if value is None:
            self.misses += 1
        else:
            self.hits += 1
        return value

    def record_search(self, query: str, ttl: int = 3600) -> int:
        """INCR по ключу поиска и EXPIRE — история поиска живёт час."""
        name = f"search:count:{query.strip().lower()}"
        counter = self.incr(name)
        self.expire(name, ttl)
        return counter

    def search_history(self, limit: int = 5) -> list[dict[str, Any]]:
        """Популярные поисковые запросы: KEYS + GET + сортировка по счётчику."""
        history: list[dict[str, Any]] = []
        for name in self.keys("search:count:*"):
            query = name.split("search:count:", 1)[-1]
            raw = self.get(name)
            if raw is None:
                continue
            history.append({"query": query, "count": int(raw), "ttl": self.ttl_of(name)})
        history.sort(key=lambda item: (-item["count"], item["query"]))
        return history[:limit]
