from __future__ import annotations

import argparse
import mimetypes
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, Tuple

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("image/jpeg", ".jpg")


def make_handler(root: Path, role: str, max_age: int = 60):
    root = root.resolve()
    cache: Dict[str, Tuple[bytes, float, str]] = {}

    class StaticHandler(BaseHTTPRequestHandler):
        server_version = "LibraryCDN/1.0"
        protocol_version = "HTTP/1.1"

        def do_GET(self) -> None:
            self._serve(send_body=True)

        def do_HEAD(self) -> None:
            self._serve(send_body=False)

        def _serve(self, send_body: bool) -> None:
            relative = self.path.split("?", 1)[0].lstrip("/") or "index.html"
            target = (root / relative).resolve()

            if root != target and root not in target.parents:
                self.send_error(403, "Forbidden")
                return
            if not target.is_file():
                self.send_error(404, "Not Found")
                return

            now = time.time()
            cached = cache.get(relative) if role == "cdn" else None

            if cached is None:
                body = target.read_bytes()
                content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
                cache[relative] = (body, now, content_type)
                age = 0
                cache_state = "MISS"
            else:
                body, stored_at, content_type = cached
                age = int(now - stored_at)
                cache_state = "HIT"

            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))

            if role == "cdn":
                self.send_header("Cache-Control", f"public, max-age={max_age}")
                self.send_header("Age", str(age))
                self.send_header("X-Cache", cache_state)
                self.send_header("X-Served-By", "local-cdn-edge")
            else:
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Cache", "BYPASS")
                self.send_header("X-Served-By", "origin")

            self.end_headers()
            if send_body:
                self.wfile.write(body)

        def log_message(self, format: str, *args) -> None:
            return

    return StaticHandler


def create_server(role: str, port: int, root: Path = STATIC_DIR, max_age: int = 60) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(("127.0.0.1", port), make_handler(root, role, max_age))


def main() -> None:
    parser = argparse.ArgumentParser(description="Локальная имитация CDN и origin-сервера")
    parser.add_argument("--role", choices=("cdn", "origin"), default="cdn")
    parser.add_argument("--port", type=int, default=8002)
    parser.add_argument("--root", type=Path, default=STATIC_DIR)
    parser.add_argument("--max-age", type=int, default=60)
    args = parser.parse_args()

    server = create_server(args.role, args.port, args.root, args.max_age)
    print(f"{args.role} server: http://127.0.0.1:{args.port}/ (root={args.root}, max-age={args.max_age})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
