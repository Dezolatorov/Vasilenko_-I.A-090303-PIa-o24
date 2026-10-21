from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


class RedisUnavailable(RuntimeError):
    """Redis недоступен и резервное хранилище не подключено."""


def create_redis(url: Optional[str] = None, force_mock: bool = False):
    if not force_mock:
        try:
            import redis

            client = redis.Redis.from_url(
                url or REDIS_URL,
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


class RedisCache:
    def __init__(
        self,
        url: Optional[str] = None,
        force_mock: bool = False,
        prefix: str = "library",
    ) -> None:
        self.client, self.mode = create_redis(url, force_mock)
        self.prefix = prefix

    def _key(self, name: str) -> str:
        return f"{self.prefix}:{name}"

    def ping(self) -> bool:
        try:
            return bool(self.client.ping())
        except Exception:
            return False

    def set_json(self, name: str, value: Any, ttl: Optional[int] = None) -> None:
        self.client.set(self._key(name), json.dumps(value, ensure_ascii=False), ex=ttl)

    def get_json(self, name: str) -> Optional[Any]:
        raw = self.client.get(self._key(name))
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            return None

    def delete(self, name: str) -> bool:
        return bool(self.client.delete(self._key(name)))

    def exists(self, name: str) -> bool:
        return bool(self.client.exists(self._key(name)))

    def ttl(self, name: str) -> int:
        return int(self.client.ttl(self._key(name)))

    def expire(self, name: str, seconds: int) -> bool:
        return bool(self.client.expire(self._key(name), seconds))

    def incr(self, name: str, amount: int = 1) -> int:
        return int(self.client.incrby(self._key(name), amount))

    def get_int(self, name: str) -> int:
        value = self.client.get(self._key(name))
        return int(value) if value is not None else 0

    def lpush_trim(self, name: str, value: str, max_len: int, ttl: Optional[int] = None) -> int:
        key = self._key(name)
        size = int(self.client.lpush(key, value))
        self.client.ltrim(key, 0, max_len - 1)
        if ttl:
            self.client.expire(key, ttl)
        return size

    def lrange(self, name: str, start: int = 0, end: int = -1) -> List[str]:
        return list(self.client.lrange(self._key(name), start, end))

    def hincrby(self, name: str, field: str, amount: int = 1) -> int:
        return int(self.client.hincrby(self._key(name), field, amount))

    def hgetall(self, name: str) -> Dict[str, str]:
        return dict(self.client.hgetall(self._key(name)))

    def zincrby(self, name: str, member: str, amount: float = 1) -> float:
        return float(self.client.zincrby(self._key(name), amount, member))

    def zrevrange(self, name: str, start: int = 0, end: int = -1, withscores: bool = True):
        return self.client.zrevrange(self._key(name), start, end, withscores=withscores)

    def sadd(self, name: str, member: str) -> int:
        return int(self.client.sadd(self._key(name), member))

    def smembers(self, name: str) -> List[str]:
        return sorted(self.client.smembers(self._key(name)))

    def keys(self) -> List[str]:
        return sorted(self.client.keys(f"{self.prefix}:*"))

    def dbsize(self) -> int:
        return len(self.keys())

    def clear(self) -> int:
        keys = self.keys()
        if keys:
            self.client.delete(*keys)
        return len(keys)
