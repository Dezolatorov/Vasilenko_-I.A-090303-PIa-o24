import json
from exceptions import ProtocolError


def encode_message(command: str, data: dict | None = None,
                   request_id: str | None = None) -> bytes:
    """Кодирует запрос клиента в newline-delimited JSON."""
    message: dict = {"command": command, "data": data or {}}
    if request_id is not None:
        message["request_id"] = request_id
    return (json.dumps(message, ensure_ascii=False) + "\n").encode("utf-8")


def decode_message(raw: bytes) -> dict:
    """Разбирает запрос клиента."""
    try:
        text = raw.decode("utf-8").strip()
        if not text:
            raise ProtocolError("Пустое сообщение")
        message = json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise ProtocolError(f"Некорректный JSON: {e}")

    if not isinstance(message, dict):
        raise ProtocolError("Сообщение должно быть JSON-объектом")
    if "command" not in message or not isinstance(message["command"], str):
        raise ProtocolError("Отсутствует обязательное поле 'command'")
    if "data" in message and not isinstance(message["data"], dict):
        raise ProtocolError("Поле 'data' должно быть объектом")
    return message


def encode_response(status: str, data: dict | list | None = None,
                    error: str | None = None,
                    request_id: str | None = None) -> bytes:
    """Кодирует ответ сервера."""
    response: dict = {"status": status}
    if data is not None:
        response["data"] = data
    if error is not None:
        response["error"] = error
    if request_id is not None:
        response["request_id"] = request_id
    return (json.dumps(response, ensure_ascii=False) + "\n").encode("utf-8")


def decode_response(raw: bytes) -> dict:
    """Разбирает ответ сервера."""
    try:
        text = raw.decode("utf-8").strip()
        response = json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise ProtocolError(f"Некорректный JSON ответа: {e}")

    if not isinstance(response, dict) or "status" not in response:
        raise ProtocolError("Ответ должен содержать поле 'status'")
    return response