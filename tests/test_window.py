from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidgetItem

from app.config import APP_NAME, APP_VERSION, DEFAULT_BOT_URL
from app.window import ManagerWindow

import pytest


@pytest.fixture(autouse=True)
def disable_startup_timer(monkeypatch):
    monkeypatch.setattr(
        "app.window.QTimer.singleShot",
        lambda *args, **kwargs: None,
    )




def test_window_identity(qtbot, monkeypatch):
    monkeypatch.delenv("LINKCUE_BOT_URL", raising=False)

    window = ManagerWindow()
    qtbot.addWidget(window)

    assert window.windowTitle() == (
        f"{APP_NAME} {APP_VERSION}"
    )
    assert window.bot_url_input.text() == DEFAULT_BOT_URL


def test_window_has_twitch_controls(qtbot):
    window = ManagerWindow()
    qtbot.addWidget(window)

    assert window.channel_input is not None
    assert window.join_button.text() == "Join Channel"
    assert window.leave_button.text() == "Leave Channel"
    assert window.channel_list is not None


def test_window_has_queue_table(qtbot):
    window = ManagerWindow()
    qtbot.addWidget(window)

    assert window.queue_table.columnCount() == 5
    assert window.refresh_queue_button.text() == (
        "Refresh Queue"
    )


def test_leave_uses_selected_channel(qtbot):
    window = ManagerWindow()
    qtbot.addWidget(window)

    class FakeClient:
        def leave_twitch_channel(self, channel):
            assert channel == "teststreamer"
            return {
                "status": "left",
                "channel": channel,
                "channels": [],
            }

    window.channel_list.addItem("teststreamer")
    window.channel_list.setCurrentRow(0)

    window.bot_client = FakeClient()
    window._update_client = lambda: None

    window.leave_channel()

    assert window.channel_list.count() == 0
    assert window.twitch_status_label.text() == "Inactive"


def test_window_has_player_status_controls(qtbot):
    window = ManagerWindow()
    qtbot.addWidget(window)

    assert window.player_status_label.text() == "Not checked"
    assert window.playback_status_label.text() == "Not checked"
    assert window.now_playing_label.text() == "None"
    assert window.refresh_player_button.text() == "Refresh Player"


def test_refresh_player_status_active_and_playing(qtbot):
    window = ManagerWindow()
    qtbot.addWidget(window)

    class FakeClient:
        def player_status(self):
            return {
                "active": True,
                "last_heartbeat": "2026-08-31T21:00:00+00:00",
                "timeout_seconds": 15,
            }

        def player_state(self):
            return {
                "state": "playing",
                "item": {
                    "title": "Test Video",
                    "url": "https://youtu.be/example",
                },
            }

    window.bot_client = FakeClient()
    window._update_client = lambda: None

    window.refresh_player_status()

    assert window.player_status_label.text() == "Active"
    assert window.playback_status_label.text() == "Playing"
    assert window.now_playing_label.text() == "Test Video"


def test_refresh_player_status_offline_and_idle(qtbot):
    window = ManagerWindow()
    qtbot.addWidget(window)

    class FakeClient:
        def player_status(self):
            return {
                "active": False,
                "last_heartbeat": None,
                "timeout_seconds": 15,
            }

        def player_state(self):
            return {
                "state": "idle",
                "item": None,
            }

    window.bot_client = FakeClient()
    window._update_client = lambda: None

    window.refresh_player_status()

    assert window.player_status_label.text() == "Offline"
    assert window.playback_status_label.text() == "Idle"
    assert window.now_playing_label.text() == "None"


def test_window_has_queue_controls(qtbot):
    window = ManagerWindow()
    qtbot.addWidget(window)

    assert window.queue_url_input is not None
    assert window.add_queue_button.text() == "Add to Queue"
    assert window.add_next_button.text() == "Add Next"
    assert window.remove_selected_button.text() == "Remove Selected"


def test_add_to_queue(qtbot):
    window = ManagerWindow()
    qtbot.addWidget(window)

    class FakeClient:
        def add_queue_item(self, url):
            assert url == "https://youtu.be/example"
            return {"id": 42}

        def queue(self):
            return []

    window.bot_client = FakeClient()
    window._update_client = lambda: None

    window.queue_url_input.setText(
        "https://youtu.be/example"
    )

    window.add_to_queue()

    assert window.queue_url_input.text() == ""
    assert window.status_label.text() == "Video added to queue."


def test_add_next_moves_new_item_to_front(qtbot):
    window = ManagerWindow()
    qtbot.addWidget(window)

    calls = []

    class FakeClient:
        def add_queue_item(self, url):
            calls.append(("add", url))
            return {"id": 42}

        def move_queue_item(self, item_id, position):
            calls.append(("move", item_id, position))
            return {
                "status": "moved",
                "id": item_id,
                "position": position,
            }

        def queue(self):
            return []

    window.bot_client = FakeClient()
    window._update_client = lambda: None

    window.queue_url_input.setText(
        "https://youtu.be/example"
    )

    window.add_next()

    assert calls == [
        ("add", "https://youtu.be/example"),
        ("move", 42, 1),
    ]
    assert window.status_label.text() == "Video added next."


def test_remove_selected_uses_hidden_item_id(qtbot):
    window = ManagerWindow()
    qtbot.addWidget(window)

    removed = []

    class FakeClient:
        def remove_queue_item(self, item_id):
            removed.append(item_id)
            return {
                "status": "deleted",
                "id": item_id,
            }

        def queue(self):
            return []

    window.bot_client = FakeClient()
    window._update_client = lambda: None

    window.queue_table.setRowCount(1)

    item = QTableWidgetItem("7")
    item.setData(
        Qt.ItemDataRole.UserRole,
        42,
    )

    window.queue_table.setItem(0, 0, item)
    window.queue_table.selectRow(0)

    window.remove_selected()

    assert removed == [42]
    assert window.status_label.text() == "Queue item removed."


def test_window_uses_compact_console_layout(qtbot):
    window = ManagerWindow()
    qtbot.addWidget(window)

    assert window.width() == 1000
    assert window.height() == 700
    assert window.channel_list.maximumHeight() == 90


def test_window_has_dark_mode_toggle(qtbot):
    window = ManagerWindow()
    qtbot.addWidget(window)

    assert window.dark_mode_button.text() == "Dark Mode"
    assert window.dark_mode_button.isCheckable()
    assert not window.dark_mode_button.isChecked()


def test_dark_mode_toggle_changes_stylesheet(qtbot):
    window = ManagerWindow()
    qtbot.addWidget(window)

    window.dark_mode_button.setChecked(True)

    assert window.styleSheet()
    assert window.status_label.text() == "Dark mode enabled."

    window.dark_mode_button.setChecked(False)

    assert window.styleSheet() == ""
    assert window.status_label.text() == "Dark mode disabled."


def test_window_schedules_initial_player_refresh(qtbot, monkeypatch):
    scheduled = []

    monkeypatch.setattr(
        "app.window.QTimer.singleShot",
        lambda delay, callback: scheduled.append((delay, callback)),
    )

    window = ManagerWindow()
    qtbot.addWidget(window)

    assert len(scheduled) == 1
    assert scheduled[0][0] == 0
    assert scheduled[0][1].__self__ is window
    assert scheduled[0][1].__func__ is ManagerWindow.refresh_player_status
