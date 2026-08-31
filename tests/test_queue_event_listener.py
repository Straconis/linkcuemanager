import json

import app.queue_event_listener as queue_events
from app.queue_event_listener import (
    QueueEventListener,
    websocket_events_url,
)


def test_http_bot_url_becomes_ws_events_url():
    assert (
        websocket_events_url("http://127.0.0.1:8000")
        == "ws://127.0.0.1:8000/ws/events?client_type=manager"
    )


def test_https_bot_url_becomes_wss_events_url():
    assert (
        websocket_events_url("https://linkcue.example.com/")
        == "wss://linkcue.example.com/ws/events?client_type=manager"
    )


def test_unsupported_scheme_is_rejected():
    try:
        websocket_events_url("ftp://linkcue.example.com")
    except ValueError as exc:
        assert "Unsupported LinkCue Bot URL scheme" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_connected_event_requests_refresh():
    calls = []

    listener = QueueEventListener(
        "http://linkcue.test",
        lambda message: calls.append(message),
    )

    listener._handle_message(
        json.dumps(
            {
                "type": "connected",
                "queue_revision": 2,
            }
        )
    )

    assert len(calls) == 1


def test_queue_changed_event_requests_refresh():
    calls = []

    listener = QueueEventListener(
        "http://linkcue.test",
        lambda message: calls.append(message),
    )

    listener._handle_message(
        json.dumps(
            {
                "type": "queue_changed",
                "revision": 3,
            }
        )
    )

    assert len(calls) == 1


def test_invalid_and_unknown_messages_are_ignored():
    calls = []

    listener = QueueEventListener(
        "http://linkcue.test",
        lambda message: calls.append(message),
    )

    listener._handle_message("not json")
    listener._handle_message(
        json.dumps(
            {
                "type": "something_else",
            }
        )
    )

    assert calls == []


def test_listen_once_uses_events_endpoint(monkeypatch):
    calls = []
    connection_args = {}

    class FakeSocket:
        def __init__(self):
            self.messages = [
                json.dumps(
                    {
                        "type": "connected",
                        "queue_revision": 0,
                    }
                ),
                None,
            ]
            self.closed = False

        def recv(self):
            return self.messages.pop(0)

        def settimeout(self, timeout):
            self.timeout = timeout

        def close(self):
            self.closed = True

    fake_socket = FakeSocket()

    def fake_create_connection(url, timeout):
        connection_args["url"] = url
        connection_args["timeout"] = timeout
        return fake_socket

    monkeypatch.setattr(
        queue_events.websocket,
        "create_connection",
        fake_create_connection,
    )

    listener = QueueEventListener(
        "https://linkcue.example.com",
        lambda message: calls.append(message),
    )

    listener._listen_once()

    assert connection_args == {
        "url": "wss://linkcue.example.com/ws/events?client_type=manager",
        "timeout": 10,
    }
    assert len(calls) == 1
    assert fake_socket.timeout is None
    assert fake_socket.closed is True
