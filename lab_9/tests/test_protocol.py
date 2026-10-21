import pytest
from protocol import encode_message, decode_message, encode_response, decode_response
from exceptions import ProtocolError


def test_encode_decode_message():
    raw = encode_message("calculate", {"expression": "2+2"}, "req-1")
    msg = decode_message(raw)
    assert msg["command"] == "calculate"
    assert msg["data"]["expression"] == "2+2"
    assert msg["request_id"] == "req-1"


def test_encode_without_request_id():
    msg = decode_message(encode_message("list"))
    assert msg["command"] == "list"
    assert "request_id" not in msg


def test_decode_invalid_json():
    with pytest.raises(ProtocolError):
        decode_message(b"{not json}\n")


def test_decode_missing_command():
    with pytest.raises(ProtocolError):
        decode_message(b'{"data": {}}\n')


def test_decode_data_not_object():
    with pytest.raises(ProtocolError):
        decode_message(b'{"command": "x", "data": []}\n')


def test_encode_response_ok():
    resp = decode_response(encode_response("ok", {"result": 4}))
    assert resp["status"] == "ok"
    assert resp["data"]["result"] == 4


def test_encode_response_error():
    resp = decode_response(encode_response("error", error="Something failed"))
    assert resp["status"] == "error"
    assert resp["error"] == "Something failed"