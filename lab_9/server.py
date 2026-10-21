import socket
import logging
from concurrent.futures import ThreadPoolExecutor

from protocol import decode_message, encode_response
from service import CalculatorService
from repository import CalculationRepository
from exceptions import (
    CalculationError,
    CalculationNotFoundError,
    ProtocolError,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("server")

HOST = "127.0.0.1"
PORT = 5001
BUFFER_SIZE = 4096
CLIENT_TIMEOUT = 30          # сек
MAX_WORKERS = 10


class CalculatorServer:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.service = CalculatorService(CalculationRepository())
        self._executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

    # ---------- Обработка одной команды ----------
    def _handle_command(self, message: dict) -> dict:
        command = message["command"]
        data = message.get("data", {}) or {}
        request_id = message.get("request_id")

        logger.info("Command: %s, data=%s", command, data)

        try:
            if command == "list":
                items = [c.to_dict() for c in self.service.get_all()]
                return {"status": "ok", "data": items, "request_id": request_id}

            if command == "get":
                calc = self.service.get(int(data["id"]))
                return {"status": "ok", "data": calc.to_dict(), "request_id": request_id}

            if command == "calculate":                       # специализированная команда
                calc = self.service.calculate(str(data.get("expression", "")))
                return {"status": "ok", "data": calc.to_dict(), "request_id": request_id}

            if command == "update":
                calc = self.service.update(
                    int(data["id"]), str(data.get("expression", ""))
                )
                return {"status": "ok", "data": calc.to_dict(), "request_id": request_id}

            if command == "delete":
                self.service.delete(int(data["id"]))
                return {"status": "ok",
                        "data": {"deleted": int(data["id"])},
                        "request_id": request_id}

            if command == "history":
                limit = int(data.get("limit", 10))
                items = [c.to_dict() for c in self.service.history(limit)]
                return {"status": "ok", "data": items, "request_id": request_id}

            if command == "clear":
                count = self.service.clear()
                return {"status": "ok",
                        "data": {"cleared": count},
                        "request_id": request_id}

            if command == "ping":
                return {"status": "ok",
                        "data": {"message": "pong"},
                        "request_id": request_id}

            return {"status": "error",
                    "error": f"Неизвестная команда: {command}",
                    "request_id": request_id}

        except CalculationNotFoundError as e:
            return {"status": "error", "error": str(e), "request_id": request_id}
        except CalculationError as e:
            return {"status": "error", "error": str(e), "request_id": request_id}
        except (KeyError, ValueError, TypeError) as e:
            return {"status": "error",
                    "error": f"Некорректные параметры: {e}",
                    "request_id": request_id}
        except Exception as e:
            logger.exception("Unexpected error")
            return {"status": "error",
                    "error": f"Внутренняя ошибка: {e}",
                    "request_id": request_id}

    # ---------- Обработчик клиента ----------
    def _client_thread(self, conn: socket.socket, addr) -> None:
        logger.info("Client connected: %s", addr)
        conn.settimeout(CLIENT_TIMEOUT)
        buffer = b""
        try:
            while True:
                try:
                    chunk = conn.recv(BUFFER_SIZE)
                except socket.timeout:
                    logger.warning("Client %s timeout", addr)
                    break
                if not chunk:
                    break
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if not line.strip():
                        continue
                    try:
                        message = decode_message(line)
                        response = self._handle_command(message)
                    except ProtocolError as e:
                        response = {"status": "error", "error": str(e)}
                    conn.sendall(encode_response(**response))
        except ConnectionResetError:
            logger.warning("Client %s reset connection", addr)
        except Exception:
            logger.exception("Error handling client %s", addr)
        finally:
            conn.close()
            logger.info("Client disconnected: %s", addr)

    # ---------- Запуск ----------
    def start(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self.host, self.port))
            server.listen(5)
            logger.info("Server started on %s:%d", self.host, self.port)
            try:
                while True:
                    conn, addr = server.accept()
                    self._executor.submit(self._client_thread, conn, addr)
            except KeyboardInterrupt:
                logger.info("Server stopped by user")
            finally:
                self._executor.shutdown(wait=False)


if __name__ == "__main__":
    CalculatorServer(HOST, PORT).start()