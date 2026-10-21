#!/usr/bin/env python3
"""Демонстрационный сценарий лабораторной №19 (вариант 2 «Библиотека»).

Поднимает микросервисы отдельными процессами (разные порты), выполняет
бизнес-сценарий через API Gateway, демонстрирует Retry и Circuit Breaker,
а также асинхронное событие LoanCreated. Все выводы сохраняются в каталог
lab19-report-data/ (demo.txt, tests.txt, service-*.log).
"""

import os
import subprocess
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent      # C:\elkin\lab_19
REPORT_DIR = Path(r"C:\Users\Игорь\Documents\MultiTool\HomeChats\Chat\lab19-report-data")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

PORTS = {"gateway": 8000, "readers": 8001, "books": 8002, "loans": 8003}
BASE = "http://127.0.0.1:8000"
READERS = "http://127.0.0.1:8001"
BOOKS = "http://127.0.0.1:8002"
LOANS = "http://127.0.0.1:8003"


class Demo:
    def __init__(self):
        self.procs = {}
        self.lines = []

    def say(self, msg):
        self.lines.append(msg)
        print(msg)

    def start_service(self, name, workdir, args, env_extra=None):
        env = dict(os.environ)
        env["PORT"] = str(PORTS[name])
        env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
        if env_extra:
            env.update(env_extra)
        log = open(REPORT_DIR / f"service-{name}.log", "a", encoding="utf-8")
        p = subprocess.Popen(
            [sys.executable] + list(args), cwd=str(workdir), env=env,
            stdout=log, stderr=subprocess.STDOUT,
        )
        self.procs[name] = p
        self.say(f"запущен {name} (pid {p.pid}) на порту {PORTS[name]}")

    def stop_service(self, name):
        p = self.procs.pop(name, None)
        if p:
            try:
                p.terminate()
            except Exception:
                pass
            try:
                p.wait(timeout=3)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass

    def start_all(self):
        self.start_service("readers", ROOT / "readers-service", ["-m", "app.main"],
                           {"READERS_DB": str(ROOT / "data/readers.json")})
        time.sleep(0.3)
        self.start_service("books", ROOT / "books-service", ["-m", "app.main"],
                           {"BOOKS_DB": str(ROOT / "data/books.json")})
        self.start_service("loans", ROOT / "loans-service", ["-m", "app.main"],
                           {"LOANS_DB": str(ROOT / "data/loans.json"),
                            "READERS_URL": READERS, "BOOKS_URL": BOOKS,
                            "EVENTS_DIR": str(ROOT / "data/events")})
        self.start_service("gateway", ROOT / "gateway", ["app.py"],
                           {"READERS_URL": READERS, "BOOKS_URL": BOOKS, "LOANS_URL": LOANS})

    def wait_ready(self, url, timeout=20):
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                if httpx.get(f"{url}/health", timeout=1.0).status_code == 200:
                    return True
            except Exception:
                pass
            time.sleep(0.3)
        return False

    def stop_all(self):
        for name in list(self.procs.keys()):
            self.stop_service(name)
        time.sleep(0.5)

    def scenario(self):
        self.say("\n=== СЦЕНАРИЙ ЧЕРЕЗ API GATEWAY ===")
        r = httpx.post(f"{BASE}/readers", json={
            "full_name": "Иван Петров", "email": "ivan@library.ru", "phone": "+7-900-000-00-00"}, timeout=5.0)
        reader = r.json()
        self.say(f"1) POST /readers -> {r.status_code} | читатель id={reader['id']} {reader['full_name']}")

        r = httpx.post(f"{BASE}/books", json={
            "title": "Война и мир", "author": "Л.Н. Толстой", "total_copies": 2}, timeout=5.0)
        book = r.json()
        self.say(f"2) POST /books -> {r.status_code} | книга id={book['id']} доступно={book['available_copies']}")

        r = httpx.get(f"{BOOKS}/books/check/{book['id']}", timeout=5.0)
        self.say(f"3) GET /books/check/{{id}} (books) -> {r.status_code} {r.json()}")

        r = httpx.post(f"{BASE}/loans", json={"reader_id": reader["id"], "book_id": book["id"]}, timeout=8.0)
        loan = r.json()
        self.say(f"4) POST /loans (gateway->loans->readers+books) -> {r.status_code} loan={loan['id']} статус={loan['status']}")

        r = httpx.get(f"{BOOKS}/books/check/{book['id']}", timeout=5.0)
        self.say(f"5) осталось доступных экземпляров: {r.json().get('available_copies')}")

        time.sleep(1.2)
        events = httpx.get(f"{LOANS}/events", timeout=5.0).json()
        created = [e for e in events if e["type"] == "LoanCreated"]
        self.say(f"6) файловая шина: событий LoanCreated доставлено = {len(created)}")

        r = httpx.post(f"{BASE}/loans/{loan['id']}/return", timeout=8.0)
        self.say(f"7) POST /loans/{{id}}/return -> {r.status_code} статус={r.json().get('status')}")

        return reader, book, loan

    def health_system(self):
        self.say("\n=== HEALTH CHECK СИСТЕМЫ через Gateway (/health/system) ===")
        try:
            h = httpx.get(f"{BASE}/health/system", timeout=5.0).json()
            self.say(f"  система: {h.get('system')}")
            for k, v in h.get("services", {}).items():
                self.say(f"  {k}: {v}")
        except Exception as exc:
            self.say(f"  health не выполнен: {exc}")

    def circuit_breaker(self, reader, book):
        self.say("\n=== ДЕМО CIRCUIT BREAKER и RETRY ===")
        self.say("останавливаю books-service (аналог docker compose stop books-service)...")
        self.stop_service("books")
        # убедиться, что порт books закрыт
        for _ in range(20):
            try:
                httpx.get(f"{BOOKS}/health", timeout=0.5)
                time.sleep(0.5)
            except Exception:
                break
        time.sleep(0.5)
        stamps = []
        for i in range(4):
            try:
                r = httpx.post(f"{LOANS}/loans", json={"reader_id": reader["id"], "book_id": book["id"]},
                               timeout=30.0)
                stamps.append(f"  попытка {i+1} -> HTTP {r.status_code} {r.json().get('detail', '')}")
            except Exception as exc:
                stamps.append(f"  попытка {i+1} -> {type(exc).__name__}: сервис недоступен")
        self.say("попытки выдачи при недоступном books-service:")
        self.say("\n".join(stamps))
        try:
            h = httpx.get(f"{LOANS}/health", timeout=10.0).json()
            cbs = h.get("circuit_breakers", {})
            self.say(f"состояния Circuit Breaker (loans-service): books={cbs.get('books')}, readers={cbs.get('readers')}")
            self.say(f"-> при books={cbs.get('books')} запросы к books отклоняются без обращения (защита от каскадного отказа)")
        except Exception as exc:
            self.say(f"не удалось прочитать CB: {exc}")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    d = Demo()

    # очистить данные предыдущих запусков для чистого сценария
    import glob
    for pat in ("data/*.json", "data/events/*.json"):
        for f in glob.glob(str(ROOT / pat)):
            try:
                os.remove(f)
            except OSError:
                pass
    (ROOT / "data/events").mkdir(parents=True, exist_ok=True)

    # -- тесты --
    d.say("=== РЕЗУЛЬТАТЫ ТЕСТОВ (pytest) ===")
    summaries = []
    for srv in ("readers-service", "books-service", "loans-service"):
        res = subprocess.run([sys.executable, "-m", "pytest", "tests", "-q", "--no-header"],
                             cwd=str(ROOT / srv), capture_output=True, text=True, encoding="utf-8", errors="replace")
        tail = res.stdout.strip().splitlines()
        summary = tail[-1] if tail else f"code={res.returncode}"
        summaries.append(f"  {srv}: returncode={res.returncode} | {summary}")
        d.say(summaries[-1])
    (REPORT_DIR / "tests.txt").write_text("\n".join(summaries) + "\n", encoding="utf-8")

    # -- запуск и сценарий --
    d.say("\n=== ЗАПУСК МИКРОСЕРВИСОВ (вариант 2 «Библиотека») ===")
    d.start_all()
    for name in ("readers", "books", "loans", "gateway"):
        url = BASE if name == "gateway" else f"http://127.0.0.1:{PORTS[name]}"
        ok = d.wait_ready(url)
        d.say(f"  [{name}] готов: {ok}")

    reader = book = loan = None
    try:
        reader, book, loan = d.scenario()
        d.health_system()
        d.circuit_breaker(reader, book)
    except Exception as exc:
        import traceback
        d.say(f"ОШИБКА сценария: {exc}")
        d.say(traceback.format_exc())
    d.stop_all()

    (REPORT_DIR / "demo.txt").write_text("\n".join(d.lines) + "\n", encoding="utf-8")
    print("\n=== ИТОГО ===")
    print(f"demo.txt и tests.txt сохранены в {REPORT_DIR}")


if __name__ == "__main__":
    main()