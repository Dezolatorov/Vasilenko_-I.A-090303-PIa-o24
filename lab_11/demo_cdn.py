"""Сравнение прямой загрузки с origin-сервера и загрузки через CDN.

Запуск: python demo_cdn.py
Требует работающих cdn/origin_server.py (8080) и cdn/edge_server.py (8081).
"""

import time

import requests

ORIGIN = "http://127.0.0.1:8080"
EDGE = "http://127.0.0.1:8081"

ASSETS = (
    "/images/cover-01.png",
    "/images/cover-05.png",
    "/images/cover-10.png",
    "/css/style.css",
    "/js/app.js",
)

HEADER = ("HTTP", "Content-Type", "Content-Length", "Cache-Control", "Age", "X-Cache", "X-Served-By")


def fetch(url: str) -> tuple[dict, float, int]:
    """Запрос ресурса: заголовки, время ответа и размер тела."""
    started = time.perf_counter()
    response = requests.get(url, timeout=5)
    elapsed_ms = (time.perf_counter() - started) * 1000
    headers = {name: response.headers.get(name, "—") for name in HEADER}
    headers["HTTP"] = str(response.status_code)
    return headers, elapsed_ms, len(response.content)


def print_headers(title: str, headers: dict, elapsed_ms: float, size: int) -> None:
    print(title)
    for name in HEADER:
        print(f"    {name:<14}: {headers[name]}")
    print(f"    {'Время':<14}: {elapsed_ms:.2f} мс")
    print(f"    {'Размер':<14}: {size} байт")


def main() -> None:
    print("=" * 78)
    print("CDN-ЭКСПЕРИМЕНТ: origin-сервер (8080) против edge-сервера CDN (8081)")
    print("=" * 78)

    requests.get(f"{EDGE}/__edge/purge", timeout=5)

    for asset in ASSETS:
        print()
        print("-" * 78)
        print(f"Ресурс: {asset}")
        print("-" * 78)
        print(f"  URL origin : {ORIGIN}{asset}")
        print(f"  URL CDN    : {EDGE}{asset}")

        origin_headers, origin_ms, origin_size = fetch(f"{ORIGIN}{asset}")
        print_headers("  Прямая загрузка с origin:", origin_headers, origin_ms, origin_size)

        edge_headers, edge_ms, edge_size = fetch(f"{EDGE}{asset}")
        print_headers("  Первый запрос через CDN (промах кэша):", edge_headers, edge_ms, edge_size)

        time.sleep(1.2)
        hit_headers, hit_ms, hit_size = fetch(f"{EDGE}{asset}")
        print_headers("  Повторный запрос через CDN (попадание):", hit_headers, hit_ms, hit_size)
        print(f"  Примечание: edge-сервер локальный, поэтому выигрыш по времени невелик;")
        print(f"  признак работы кэша — X-Cache: HIT и Age = {hit_headers['Age']} c.")

    print()
    print("=" * 78)
    print("СОСТОЯНИЕ КЭША EDGE-СЕРВЕРА")
    print("=" * 78)
    stats = requests.get(f"{EDGE}/__edge/stats", timeout=5).json()
    print(f"Объектов в кэше: {stats['cached_objects']}")
    print(f"HIT: {stats['hit']}, MISS: {stats['miss']}, REVALIDATE: {stats['revalidate']}")
    for path, info in stats["objects"].items():
        print(f"  {path:<26} Age={info['age']} c, max-age={info['max_age']} c, '{info['cache_control']}'")

    print()
    print("Вывод: обложки и статические файлы кэшируются на edge-сервере,")
    print("повторные запросы отдаются с заголовком X-Cache: HIT и Age > 0,")
    print("при этом приложение (цена, наличие книг) по-прежнему берёт данные из БД.")


if __name__ == "__main__":
    main()
