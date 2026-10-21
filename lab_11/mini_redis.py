"""Минимальный Redis-совместимый сервер (протокол RESP) для локального запуска.

Redis не имеет официальной сборки под Windows, поэтому для лабораторной работы
поднимается локальный сервер, который понимает протокол RESP и набор команд,
используемых приложением: PING, SET (с EX), GET, DEL, EXPIRE, TTL, INCR, KEYS,
DBSIZE, FLUSHDB. Приложение обращается к нему штатным клиентом redis-py,
поэтому переключение на настоящий Redis сводится к смене host/port.

Запуск: python mini_redis.py [--port 6379]
"""

import argparse
import socketserver
import threading
import time

STORE: dict[str, tuple[str, float | None]] = {}
LOCK = threading.Lock()


def _now() -> float:
    return time.time()


def _get(key: str) -> str | None:
    item = STORE.get(key)
    if item is None:
        return None
    value, expires_at = item
    if expires_at is not None and expires_at <= _now():
        STORE.pop(key, None)
        return None
    return value


def _set(key: str, value: str, ttl: float | None = None) -> None:
    STORE[key] = (value, None if ttl is None else _now() + ttl)


def handle_command(parts: list[str]) -> tuple[str, object]:
    """Выполнить команду и вернуть (тип ответа, значение)."""
    if not parts:
        return "error", "ERR empty command"

    command = parts[0].upper()
    args = parts[1:]

    with LOCK:
        if command == "PING":
            return "simple", "PONG"

        if command in ("CLIENT", "SELECT", "CONFIG", "COMMAND"):
            return "simple", "OK"

        if command == "SET":
            if len(args) < 2:
                return "error", "ERR wrong number of arguments for 'set'"
            ttl = None
            rest = args[2:]
            for index, token in enumerate(rest):
                if token.upper() in ("EX", "PX") and index + 1 < len(rest):
                    seconds = float(rest[index + 1])
                    ttl = seconds if token.upper() == "EX" else seconds / 1000.0
            _set(args[0], args[1], ttl)
            return "simple", "OK"

        if command == "GET":
            value = _get(args[0]) if args else None
            return ("bulk", value) if value is not None else ("nil", None)

        if command == "DEL":
            removed = 0
            for key in args:
                if STORE.pop(key, None) is not None:
                    removed += 1
            return "int", removed

        if command == "EXPIRE":
            if len(args) < 2:
                return "error", "ERR wrong number of arguments for 'expire'"
            value = _get(args[0])
            if value is None:
                return "int", 0
            _set(args[0], value, float(args[1]))
            return "int", 1

        if command == "TTL":
            item = STORE.get(args[0]) if args else None
            if item is None or _get(args[0]) is None:
                return "int", -2
            expires_at = item[1]
            if expires_at is None:
                return "int", -1
            return "int", max(0, int(round(expires_at - _now())))

        if command in ("INCR", "INCRBY", "DECRBY"):
            if not args:
                return "error", f"ERR wrong number of arguments for '{command.lower()}'"
            current = _get(args[0])
            try:
                value = int(current) if current is not None else 0
            except ValueError:
                return "error", "ERR value is not an integer or out of range"
            if command == "INCR":
                value += 1
            else:
                try:
                    delta = int(args[1])
                except (IndexError, ValueError):
                    return "error", "ERR value is not an integer or out of range"
                value += delta if command == "INCRBY" else -delta
            item = STORE.get(args[0])
            _set(args[0], str(value), None if item is None else (
                None if item[1] is None else max(0.0, item[1] - _now())
            ))
            return "int", value

        if command == "KEYS":
            pattern = args[0] if args else "*"
            prefix = pattern.rstrip("*")
            keys = [key for key in list(STORE) if _get(key) is not None and key.startswith(prefix)]
            return "array", sorted(keys)

        if command == "DBSIZE":
            return "int", sum(1 for key in list(STORE) if _get(key) is not None)

        if command in ("FLUSHDB", "FLUSHALL"):
            STORE.clear()
            return "simple", "OK"

    return "error", f"ERR unknown command '{parts[0]}'"


def encode(kind: str, value: object) -> bytes:
    if kind == "hello":
        pairs = [
            ("server", "mini-redis"),
            ("version", "7.0.0"),
            ("proto", "2"),
            ("id", "1"),
            ("mode", "standalone"),
            ("role", "master"),
        ]
        payload = b"*13\r\n"
        for key, item in pairs:
            for text in (key, item):
                data = text.encode()
                payload += b"$" + str(len(data)).encode() + b"\r\n" + data + b"\r\n"
        payload += b"*0\r\n"  # modules — пустой список
        return payload
    if kind == "simple":
        return f"+{value}\r\n".encode()
    if kind == "error":
        return f"-{value}\r\n".encode()
    if kind == "int":
        return f":{value}\r\n".encode()
    if kind == "nil":
        return b"$-1\r\n"
    if kind == "bulk":
        data = str(value).encode()
        return b"$" + str(len(data)).encode() + b"\r\n" + data + b"\r\n"
    if kind == "array":
        items = [str(item) for item in value]  # type: ignore[union-attr]
        payload = b"*" + str(len(items)).encode() + b"\r\n"
        for item in items:
            data = item.encode()
            payload += b"$" + str(len(data)).encode() + b"\r\n" + data + b"\r\n"
        return payload
    return b"-ERR internal\r\n"


def read_command(stream) -> list[str] | None:
    """Прочитать одну команду RESP (массив bulk-строк) или inline-команду."""
    line = stream.readline()
    if not line:
        return None
    text = line.decode(errors="replace").strip()
    if not text:
        return []
    if not text.startswith("*"):
        return text.split()

    count = int(text[1:])
    parts: list[str] = []
    for _ in range(count):
        header = stream.readline().decode(errors="replace").strip()
        if not header.startswith("$"):
            return parts
        length = int(header[1:])
        if length < 0:
            parts.append("")
            continue
        data = stream.read(length + 2)
        parts.append(data[:-2].decode(errors="replace"))
    return parts


class RedisHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        while True:
            try:
                parts = read_command(self.rfile)
            except (ValueError, OSError):
                return
            if parts is None:
                return
            if not parts:
                continue
            kind, value = handle_command(parts)
            self.wfile.write(encode(kind, value))
            self.wfile.flush()


class RedisServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main() -> None:
    parser = argparse.ArgumentParser(description="Локальный Redis-совместимый сервер")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=6379)
    args = parser.parse_args()

    with RedisServer((args.host, args.port), RedisHandler) as server:
        print(f"mini-redis слушает {args.host}:{args.port} (RESP), Ctrl+C — остановка")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nmini-redis остановлен")


if __name__ == "__main__":
    main()
