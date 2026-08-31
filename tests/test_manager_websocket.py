from types import SimpleNamespace

import app.window as window_module
from app.window import ManagerWindow


class FakeListener:
    def __init__(self):
        self.stopped = False

    def stop(self):
        self.stopped = True


def test_stop_background_services_stops_queue_listener():
    listener = FakeListener()

    window = SimpleNamespace(
        queue_event_listener=listener,
    )

    ManagerWindow._stop_background_services(window)

    assert listener.stopped is True


def test_update_client_restarts_listener_when_bot_url_changes(
    qtbot,
    monkeypatch,
):
    window = ManagerWindow()
    qtbot.addWidget(window)

    original_listener = window.queue_event_listener
    original_listener.stop()

    created = []

    class ReplacementListener:
        def __init__(self, base_url, callback):
            self.url = window_module.websocket_events_url(base_url)
            self.base_url = base_url
            self.callback = callback
            self.started = False
            self.stopped = False
            created.append(self)

        def start(self):
            self.started = True

        def stop(self):
            self.stopped = True

    monkeypatch.setattr(
        window_module,
        "QueueEventListener",
        ReplacementListener,
    )

    original_listener.stop = lambda: setattr(
        original_listener,
        "_test_stopped",
        True,
    )

    window.bot_url_input.setText(
        "https://linkcue.example.com"
    )

    window._update_client()

    assert getattr(original_listener, "_test_stopped", False) is True
    assert len(created) == 1
    assert created[0].base_url == "https://linkcue.example.com"
    assert created[0].started is True
    assert window.queue_event_listener is created[0]
