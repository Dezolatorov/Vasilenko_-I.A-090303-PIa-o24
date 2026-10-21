"""Демонстрация работы Redis: базовые команды, cache-aside, TTL, инвалидация.

Запуск (при работающем mini_redis.py): python demo_cache.py
"""

import json
import time

import config
from cache import RedisCache
from db import Database
from repository import BookRepository
from schemas import parse_filters
from service import BookService


def section(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def main() -> None:
    cache = RedisCache()
    print(f"Redis: {config.REDIS_HOST}:{config.REDIS_PORT}, ping = {cache.ping()}")

    section("1. Базовые операции Redis (SET / GET / DEL / EXPIRE / INCR)")
    cache.client.flushdb()
    print("FLUSHDB — кэш очищен")
    cache.set("demo:greeting", "привет", ttl=90)
    print(f"SET demo:greeting 'привет' EX 90  → GET demo:greeting = {cache.get('demo:greeting')!r}")
    print(f"TTL demo:greeting = {cache.ttl_of('demo:greeting')} c")
    cache.incr("demo:counter")
    cache.incr("demo:counter")
    print(f"INCR demo:counter дважды → {cache.get('demo:counter')}")
    cache.expire("demo:counter", 5)
    print(f"EXPIRE demo:counter 5 → TTL = {cache.ttl_of('demo:counter')} c")
    print(f"DEL demo:greeting → удалено ключей: {cache.delete('demo:greeting')}, "
          f"GET = {cache.get('demo:greeting')!r}")
    print(f"Ключи в базе кэша: {cache.keys('*')}")

    section("2. Cache-aside: промах и попадание")
    database = Database(config.DB_PATH)
    service = BookService(BookRepository(database), cache)
    cache.hits = cache.misses = 0

    started = time.perf_counter()
    first = service.get_book(4)
    first_time = (time.perf_counter() - started) * 1000
    print(f"GET /books/4 (1-й раз) → MISS: SELECT из SQLite «{first.title}», {first_time:.2f} мс")
    print(f"  ключ в Redis: book:4, TTL = {cache.ttl_of('book:4')} c")

    started = time.perf_counter()
    second = service.get_book(4)
    second_time = (time.perf_counter() - started) * 1000
    print(f"GET /books/4 (2-й раз) → HIT: значение из Redis «{second.title}», {second_time:.2f} мс")
    print(f"Статистика кэша: {json.dumps(cache.stats(), ensure_ascii=False)}")

    section("3. Инвалидация кэша после изменения (PATCH)")
    print(f"book:4 в кэше до изменения: {cache.get('book:4') is not None}")
    updated = service.patch_book(4, {"price": 1050.0})
    print(f"PATCH /books/4 {{'price': 1050.0}} → новая цена {updated.price}")
    print(f"book:4 в кэше после изменения: {cache.get('book:4') is not None} (ключ удалён)")
    fresh = service.get_book(4)
    print(f"Следующий GET /books/4 → MISS и свежие данные из БД: цена {fresh.price}")

    section("4. TTL: запись исчезает по истечении времени жизни")
    cache.set("demo:short", "живёт 2 секунды", ttl=2)
    print(f"SET demo:short EX 2 → GET = {cache.get('demo:short')!r}, TTL = {cache.ttl_of('demo:short')}")
    time.sleep(2.5)
    print(f"Через 2.5 секунды: GET = {cache.get('demo:short')!r}, TTL = {cache.ttl_of('demo:short')} (-2 = ключа нет)")

    section("5. История поиска в Redis (INCR + EXPIRE)")
    for query in ("война", "война", "собачье", "война", "1984"):
        cache.record_search(query)
    print("Поисковые запросы: война, война, собачье, война, 1984")
    for item in cache.search_history():
        print(f"  {item['query']:<10} запросов: {item['count']}, TTL = {item['ttl']} c")

    section("6. Ключи кэша после эксперимента")
    print(f"Ключи: {cache.keys('*')}")
    print(f"Итоговая статистика: {json.dumps(cache.stats(), ensure_ascii=False)}")


if __name__ == "__main__":
    main()
