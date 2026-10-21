import socket
import threading
import time
import pytest

from server import CalculatorServer
from protocol import encode_message, decode_response


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def server_port():
    port = _free_port()
    server = CalculatorServer("127.0.0.1", port)
    thread = threading.Thread(target=server.start, daemon=True)
    thread.start()
    time.sleep(0.3)          # дать серверу подняться
    yield port


def _send(port: int, command: str, data: dict | None = None) -> dict:
    with socket.socket() as sock:
        sock.settimeout(3)
        sock.connect(("127.0.0.1", port))
        sock.sendall(encode_message(command, data))
        buffer = b""
        while b"\n" not in buffer:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buffer += chunk
    return decode_response(buffer)


def test_end_to_end_calculate(server_port):
    resp = _send(server_port, "calculate", {"expression": "7*6"})
    assert resp["status"] == "ok"
    assert resp["data"]["result"] == 42.0


def test_end_to_end_list(server_port):
    _send(server_port, "calculate", {"expression": "1+1"})
    resp = _send(server_port, "list")
    assert resp["status"] == "ok"
    assert isinstance(resp["data"], list)
    assert len(resp["data"]) >= 1


def test_end_to_end_unknown_command(server_port):
    resp = _send(server_port, "unknown")
    assert resp["status"] == "error"


def test_end_to_end_ping(server_port):
    resp = _send(server_port, "ping")
    assert resp["status"] == "ok"
    assert resp["data"]["message"] == "pong"


def test_end_to_end_delete_not_found(server_port):
    resp = _send(server_port, "delete", {"id": 999999})
    assert resp["status"] == "error"