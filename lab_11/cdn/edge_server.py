"""Edge-сервер CDN: кэширует статику из origin и отдаёт её клиенту.

Запуск: python cdn/edge_server.py --port 8081 --origin http://127.0.0.1:8080
"""

import argparse
import time
from dataclasses import dataclass, field

import requests
from flask import Flask, Response

DEFAULT_ORIGIN = "http://127.0.0.1:8080"


@dataclass
class CacheEntry:
    """Копия ресурса на edge-сервере."""

    body: bytes
    content_type: str
    cache_control: str
    stored_at: float
    max_age: int
    etag: str = ""

    @property
    def age(self) -> int:
        return int(time.time() - self.stored_at)

    @property
    def is_fresh(self) -> bool:
        return self.max_age > 0 and self.age < self.max_age


@dataclass
class EdgeCache:
    """Кэш edge-сервера с учётом Cache-Control от origin."""

    entries: dict[str, CacheEntry] = field(default_factory=dict)
    stats: dict[str, int] = field(default_factory=lambda: {"hit": 0, "miss": 0, "revalidate": 0})

    def get(self, path: str) -> CacheEntry | None:
        entry = self.entries.get(path)
        if entry is None:
            self.stats["miss"] += 1
            return None
        if not entry.is_fresh:
            self.stats["revalidate"] += 1
            self.entries.pop(path, None)
            return None
        self.stats["hit"] += 1
        return entry

    def put(self, path: str, entry: CacheEntry) -> None:
        if entry.max_age > 0:
            self.entries[path] = entry


def parse_max_age(cache_control: str) -> int:
    """Извлечь max-age из заголовка Cache-Control."""
    for directive in cache_control.split(","):
        directive = directive.strip()
        if directive.startswith("max-age="):
            try:
                return int(directive.split("=", 1)[1])
            except ValueError:
                return 0
    return 0


def create_edge(origin: str = DEFAULT_ORIGIN) -> Flask:
    app = Flask(__name__, static_folder=None)
    cache = EdgeCache()
    app.extensions["edge_cache"] = cache

    @app.get("/<path:asset>")
    def serve(asset: str) -> Response:
        path = f"/{asset}"
        entry = cache.get(path)

        if entry is not None:
            response = Response(entry.body)
            response.headers["Content-Type"] = entry.content_type
            response.headers["Cache-Control"] = entry.cache_control
            response.headers["Age"] = str(entry.age)
            response.headers["X-Cache"] = "HIT"
            response.headers["X-Served-By"] = "edge-moscow"
            if entry.etag:
                response.headers["ETag"] = entry.etag
            return response

        upstream = requests.get(f"{origin}{path}", timeout=5)
        if upstream.status_code != 200:
            return Response(upstream.text, status=upstream.status_code)

        cache_control = upstream.headers.get("Cache-Control", "no-store")
        entry = CacheEntry(
            body=upstream.content,
            content_type=upstream.headers.get("Content-Type", "application/octet-stream"),
            cache_control=cache_control,
            stored_at=time.time(),
            max_age=parse_max_age(cache_control),
            etag=upstream.headers.get("ETag", ""),
        )
        cache.put(path, entry)

        response = Response(entry.body)
        response.headers["Content-Type"] = entry.content_type
        response.headers["Cache-Control"] = cache_control
        response.headers["Age"] = "0"
        response.headers["X-Cache"] = "MISS"
        response.headers["X-Served-By"] = "edge-moscow"
        if entry.etag:
            response.headers["ETag"] = entry.etag
        return response

    @app.get("/__edge/stats")
    def stats():
        return {
            "cached_objects": len(cache.entries),
            "hit": cache.stats["hit"],
            "miss": cache.stats["miss"],
            "revalidate": cache.stats["revalidate"],
            "objects": {
                path: {"age": entry.age, "max_age": entry.max_age, "cache_control": entry.cache_control}
                for path, entry in cache.entries.items()
            },
        }

    @app.get("/__edge/purge")
    def purge() -> dict:
        cache.entries.clear()
        cache.stats.update({"hit": 0, "miss": 0, "revalidate": 0})
        return {"purged": True}

    return app


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CDN edge-сервер")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8081)
    parser.add_argument("--origin", default=DEFAULT_ORIGIN)
    args = parser.parse_args()
    print(f"CDN edge: http://{args.host}:{args.port}/ (origin {args.origin})")
    create_edge(args.origin).run(host=args.host, port=args.port, threaded=True)
