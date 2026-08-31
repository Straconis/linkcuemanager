from __future__ import annotations

import json
import threading
from collections.abc import Callable
from urllib.parse import urlsplit, urlunsplit

import websocket


def websocket_events_url(base_url: str) -> str:
    parts = urlsplit(base_url.rstrip("/"))

    if parts.scheme == "http":
        scheme = "ws"
    elif parts.scheme == "https":
        scheme = "wss"
    else:
        raise ValueError(
            f"Unsupported LinkCue Bot URL scheme: {parts.scheme}"
        )

    return urlunsplit(
        (
            scheme,
            parts.netloc,
            "/ws/events",
            "client_type=manager",
            "",
        )
    )


class QueueEventListener:
    def __init__(
        self,
        base_url: str,
        on_queue_refresh: Callable[[dict], None],
        reconnect_delay: float = 2.0,
    ) -> None:
        self.url = websocket_events_url(base_url)
        self.on_queue_refresh = on_queue_refresh
        self.reconnect_delay = reconnect_delay

        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._socket = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return

        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._run,
            daemon=True,
            name="LinkCueManagerQueueEvents",
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

        socket = self._socket

        if socket is not None:
            try:
                socket.close()
            except Exception:
                pass

        thread = self._thread

        if (
            thread is not None
            and thread.is_alive()
            and thread is not threading.current_thread()
        ):
            thread.join(timeout=2.0)

        self._thread = None
        self._socket = None

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._listen_once()
            except Exception:
                pass

            if self._stop_event.wait(self.reconnect_delay):
                break

    def _listen_once(self) -> None:
        socket = websocket.create_connection(
            self.url,
            timeout=10,
        )
        socket.settimeout(None)
        self._socket = socket

        try:
            while not self._stop_event.is_set():
                raw_message = socket.recv()

                if raw_message is None:
                    break

                self._handle_message(raw_message)
        finally:
            try:
                socket.close()
            except Exception:
                pass

            if self._socket is socket:
                self._socket = None

    def _handle_message(self, raw_message: str) -> None:
        try:
            message = json.loads(raw_message)
        except (TypeError, json.JSONDecodeError):
            return

        if not isinstance(message, dict):
            return

        if message.get("type") in {
            "connected",
            "queue_changed",
            "manager_presence_changed",
            "player_presence_changed",
        }:
            self.on_queue_refresh(message)
