"""Origin-сервер: отдаёт статические ресурсы напрямую (без CDN).

Запуск: python cdn/origin_server.py --port 8080
"""

import argparse
import mimetypes
from pathlib import Path

from flask import Flask, Response, request

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

# Политика кэширования origin-сервера: сколько секунд ресурс считается свежим.
CACHE_POLICY: dict[str, str] = {
    ".png": "public, max-age=86400",
    ".jpg": "public, max-age=86400",
    ".css": "public, max-age=3600",
    ".js": "public, max-age=3600",
}


def create_origin() -> Flask:
    app = Flask(__name__, static_folder=None)

    @app.get("/<path:asset>")
    def serve_asset(asset: str) -> Response:
        path = (STATIC_DIR / asset).resolve()
        if not str(path).startswith(str(STATIC_DIR)) or not path.is_file():
            return Response("Not found", status=404)

        content_type, _ = mimetypes.guess_type(path.name)
        cache_control = CACHE_POLICY.get(path.suffix.lower(), "no-store")
        body = path.read_bytes()
        response = Response(body, mimetype=content_type or "application/octet-stream")
        response.headers["Cache-Control"] = cache_control
        response.headers["ETag"] = f"\"{path.stat().st_mtime_ns}\""
        response.headers["Last-Modified"] = "Mon, 19 Oct 2026 06:00:00 GMT"
        response.headers["X-Served-By"] = "origin"
        return response

    @app.get("/")
    def index() -> Response:
        return Response(f"Origin server, ресурсов: {len(list(STATIC_DIR.rglob('*.*')))}")

    return app


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Origin-сервер статики")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    print(f"Origin: http://{args.host}:{args.port}/ (каталог {STATIC_DIR})")
    create_origin().run(host=args.host, port=args.port, threaded=True)
