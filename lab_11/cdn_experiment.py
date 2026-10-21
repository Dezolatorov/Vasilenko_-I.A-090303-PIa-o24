from __future__ import annotations

import json
import threading
import time
import urllib.request
from pathlib import Path
from typing import Dict, List

from cdn_server import STATIC_DIR, create_server

BASE_DIR = Path(__file__).resolve().parent
ORIGIN_PORT = 8001
CDN_PORT = 8002
CDN_MAX_AGE = 60

RESOURCES = (
    "images/cover-1.jpg",
    "css/style.css",
    "js/app.js",
)


def start_server(role: str, port: int) -> "threading.Thread":
    server = create_server(role, port, STATIC_DIR, CDN_MAX_AGE)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    thread.server = server  # type: ignore[attr-defined]
    return thread


def stop_server(thread: "threading.Thread") -> None:
    server = getattr(thread, "server")
    server.shutdown()
    server.server_close()


def fetch(url: str) -> Dict[str, object]:
    started = time.perf_counter()
    with urllib.request.urlopen(url, timeout=5) as response:
        body = response.read()
        headers = {key.lower(): value for key, value in response.headers.items()}
        status = response.status
    elapsed_ms = (time.perf_counter() - started) * 1000
    return {
        "url": url,
        "status": status,
        "elapsed_ms": round(elapsed_ms, 2),
        "size_bytes": len(body),
        "content_type": headers.get("content-type"),
        "cache_control": headers.get("cache-control"),
        "age": headers.get("age"),
        "x_cache": headers.get("x-cache"),
        "served_by": headers.get("x-served-by"),
    }


def collect() -> List[Dict[str, object]]:
    origin_thread = start_server("origin", ORIGIN_PORT)
    cdn_thread = start_server("cdn", CDN_PORT)
    time.sleep(0.3)

    results: List[Dict[str, object]] = []
    try:
        for resource in RESOURCES:
            for attempt in (1, 2):
                if attempt == 2:
                    time.sleep(1.2)
                origin = fetch(f"http://127.0.0.1:{ORIGIN_PORT}/{resource}")
                origin.update({"source": "origin", "resource": resource, "attempt": attempt})
                results.append(origin)

                cdn = fetch(f"http://127.0.0.1:{CDN_PORT}/{resource}")
                cdn.update({"source": "cdn", "resource": resource, "attempt": attempt})
                results.append(cdn)
    finally:
        stop_server(origin_thread)
        stop_server(cdn_thread)

    return results


def format_table(results: List[Dict[str, object]]) -> str:
    header = "| Источник | Ресурс | Попытка | Код | Размер, байт | Время, мс | Cache-Control | Age | X-Cache |"
    divider = "|---|---|---|---|---|---|---|---|---|"
    lines = [header, divider]
    for row in results:
        lines.append(
            "| {source} | {resource} | {attempt} | {status} | {size_bytes} | {elapsed_ms} | "
            "{cache_control} | {age} | {x_cache} |".format(
                source=row["source"],
                resource=row["resource"],
                attempt=row["attempt"],
                status=row["status"],
                size_bytes=row["size_bytes"],
                elapsed_ms=row["elapsed_ms"],
                cache_control=row["cache_control"],
                age=row["age"] if row["age"] not in (None, "") else "—",
                x_cache=row["x_cache"],
            )
        )
    return "\n".join(lines)


def summary(results: List[Dict[str, object]]) -> str:
    def average(source: str, attempt: int) -> float:
        values = [
            float(row["elapsed_ms"])
            for row in results
            if row["source"] == source and row["attempt"] == attempt
        ]
        return round(sum(values) / len(values), 2) if values else 0.0

    return (
        f"Среднее время (origin, 1-й запрос): {average('origin', 1)} мс\n"
        f"Среднее время (cdn, 1-й запрос): {average('cdn', 1)} мс\n"
        f"Среднее время (cdn, 2-й запрос): {average('cdn', 2)} мс"
    )


def main() -> None:
    results = collect()
    table = format_table(results)
    stats = summary(results)

    print(table)
    print()
    print(stats)

    report = f"""# Отчёт по CDN-эксперименту

Origin: http://127.0.0.1:{ORIGIN_PORT}/ (Cache-Control: no-store)
CDN: http://127.0.0.1:{CDN_PORT}/ (Cache-Control: public, max-age={CDN_MAX_AGE})

{table}

## Итоги

{stats}
"""
    (BASE_DIR / "cdn_report.md").write_text(report, encoding="utf-8")
    (BASE_DIR / "cdn_report.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("\nСохранено: cdn_report.md, cdn_report.json")


if __name__ == "__main__":
    main()
