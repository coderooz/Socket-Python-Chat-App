"""Protocol tests: JSON-newline format and message validation (no network)."""

from __future__ import annotations

import base64
import json


def encode_message(obj: dict) -> bytes:
    """Encode a protocol message the same way clients do (JSON + \\n)."""
    return (json.dumps(obj) + "\n").encode()


def decode_line(line: bytes) -> dict[str, object]:
    return json.loads(line.decode().strip())  # type: ignore[no-any-return]


def test_text_message_roundtrip():
    obj = {"type": "text", "username": "alice", "channel": "main", "message": "hello"}
    decoded = decode_line(encode_message(obj))
    assert decoded["type"] == "text"
    assert decoded["username"] == "alice"
    assert decoded["message"] == "hello"


def test_join_message_fields():
    obj = {"type": "join", "username": "bob", "channel": "main"}
    raw = encode_message(obj)
    assert raw.endswith(b"\n")
    assert json.loads(raw)["type"] == "join"


def test_file_message_base64_roundtrip():
    content = b"hello file content \x00\xff"
    b64 = base64.b64encode(content).decode()
    obj = {
        "type": "file",
        "username": "carol",
        "channel": "main",
        "filename": "note.txt",
        "data": b64,
    }
    decoded = decode_line(encode_message(obj))
    assert base64.b64decode(decoded["data"]) == content  # type: ignore[arg-type]
    assert decoded["filename"] == "note.txt"


def test_invalid_json_raises():
    import pytest

    with pytest.raises(json.JSONDecodeError):
        json.loads("not json\n")


def test_system_message_shape():
    obj = {
        "type": "system",
        "username": "__server__",
        "channel": "main",
        "message": "alice joined.",
        "timestamp": "2025-01-01T00:00:00Z",
    }
    decoded = decode_line(encode_message(obj))
    assert decoded["type"] == "system"
    assert str(decoded["timestamp"]).endswith("Z")


def test_newline_delimited_buffer_split():
    """Simulate TCP recv buffering: two messages in one recv."""
    m1 = (
        json.dumps(
            {"type": "text", "username": "a", "channel": "main", "message": "hi"}
        )
        + "\n"
    )
    m2 = (
        json.dumps(
            {"type": "text", "username": "b", "channel": "main", "message": "hey"}
        )
        + "\n"
    )
    buf = (m1 + m2).encode()
    parts = buf.split(b"\n")
    # last part is empty after trailing \n
    assert len(parts) == 3
    assert json.loads(parts[0])["username"] == "a"
    assert json.loads(parts[1])["username"] == "b"
