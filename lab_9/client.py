import socket
import json
import logging

from protocol import encode_message, decode_response
from exceptions import ProtocolError

logging.basicConfig(level=logging.WARNING,
                    format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
logger = logging.getLogger("client")

HOST = "127.0.0.1"
PORT = 5001
TIMEOUT = 5
BUFFER_SIZE = 4096


class CalculatorClient:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self._request_counter = 0

    def _next_request_id(self) -> str:
        self._request_counter += 1
        return f"req-{self._request_counter}"

    # ---------- Отправка одного запроса ----------
    def send(self, command: str, data: dict | None = None) -> dict:
        request_id = self._next_request_id()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(TIMEOUT)
            sock.connect((self.host, self.port))
            sock.sendall(encode_message(command, data, request_id))

            buffer = b""
            while b"\n" not in buffer:
                chunk = sock.recv(BUFFER_SIZE)
                if not chunk:
                    break
                buffer += chunk

        resp = decode_response(buffer)
        # Проверка соответствия request_id
        if resp.get("request_id") and resp["request_id"] != request_id:
            raise ProtocolError("request_id ответа не совпадает с запросом")
        return resp

    # ---------- Вывод ----------
    @staticmethod
    def _print_response(resp: dict) -> None:
        if resp.get("status") == "ok":
            print(json.dumps(resp.get("data"), ensure_ascii=False, indent=2))
        else:
            print(f"[ERROR] {resp.get('error')}")

    # ---------- Интерфейс ----------
    def interactive(self) -> None:
        print("=" * 52)
        print(" КАЛЬКУЛЯТОР — клиент")
        print("=" * 52)
        print("1. Вычислить выражение")
        print("2. Показать все вычисления")
        print("3. Получить по id")
        print("4. Изменить выражение")
        print("5. Удалить по id")
        print("6. История (последние N)")
        print("7. Очистить всё")
        print("8. Ping")
        print("0. Выход")

        while True:
            try:
                choice = input("\nВыберите действие: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            try:
                if choice == "1":
                    expr = input("Выражение (например, 2+2*3): ").strip()
                    self._print_response(self.send("calculate", {"expression": expr}))

                elif choice == "2":
                    self._print_response(self.send("list"))

                elif choice == "3":
                    cid = int(input("id: ").strip())
                    self._print_response(self.send("get", {"id": cid}))

                elif choice == "4":
                    cid = int(input("id: ").strip())
                    expr = input("Новое выражение: ").strip()
                    self._print_response(
                        self.send("update", {"id": cid, "expression": expr})
                    )

                elif choice == "5":
                    cid = int(input("id: ").strip())
                    self._print_response(self.send("delete", {"id": cid}))

                elif choice == "6":
                    raw = input("Сколько последних записей? [10]: ").strip()
                    limit = int(raw) if raw else 10
                    self._print_response(self.send("history", {"limit": limit}))

                elif choice == "7":
                    self._print_response(self.send("clear"))

                elif choice == "8":
                    self._print_response(self.send("ping"))

                elif choice == "0":
                    break
                else:
                    print("Неизвестный пункт меню")

            except socket.timeout:
                print("[ERROR] Тайм-аут ответа сервера")
            except ConnectionRefusedError:
                print("[ERROR] Не удалось подключиться к серверу")
            except ProtocolError as e:
                print(f"[ERROR] Протокол: {e}")
            except Exception as e:
                print(f"[ERROR] {e}")


if __name__ == "__main__":
    CalculatorClient(HOST, PORT).interactive()