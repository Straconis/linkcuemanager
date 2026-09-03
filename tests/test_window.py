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
    assert window.bot_page.bot_url_input.text() == "http://127.0.0.1"
    assert window.bot_page.bot_port_input.text() == "8000"


def test_window_has_twitch_controls(qtbot):
    window = ManagerWindow()
    qtbot.addWidget(window)

    assert window.twitch_page.channel_input is not None
    assert window.twitch_page.join_button.text() == "Join Channel"
    assert window.twitch_page.leave_button.text() == "Leave Channel"
    assert window.twitch_page.channel_list is not None


def test_window_has_queue_table(qtbot):
    window = ManagerWindow()
    qtbot.addWidget(window)

    # Queue uses one stretched column containing
    # thumbnail + multiline metadata cards.
    assert window.queue_page.queue_table.columnCount() == 1
    assert window.queue_page.queue_table.isColumnHidden(0) is False
    assert window.queue_page.refresh_queue_button.text() == (
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

    window.twitch_page.channel_list.addItem("teststreamer")
    window.twitch_page.channel_list.setCurrentRow(0)

    window.bot_client = FakeClient()
    window._update_client = lambda: None

    window.leave_channel()

    assert window.twitch_page.channel_list.count() == 0
    assert window.twitch_page.status_label.text() == "Inactive"


def test_window_has_player_status_controls(qtbot):
    window = ManagerWindow()
    qtbot.addWidget(window)

    assert window.player_page.player_status_label.text() == "Not checked"
    assert window.player_page.playback_status_label.text() == "Not checked"
    assert window.player_page.now_playing_label.text() == "None"
    assert window.player_page.refresh_button.text() == "Refresh Player"


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

    assert window.player_page.player_status_label.text() == "Active"
    assert window.player_page.playback_status_label.text() == "Playing"
    assert window.player_page.now_playing_label.text() == "Test Video"


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

    assert window.player_page.player_status_label.text() == "Offline"
    assert window.player_page.playback_status_label.text() == "Idle"
    assert window.player_page.now_playing_label.text() == "None"


def test_window_has_queue_controls(qtbot):
    window = ManagerWindow()
    qtbot.addWidget(window)

    assert window.queue_page.add_video_button.text() == "Add Video"
    assert (
        window.queue_page.refresh_metadata_button.text()
        == "Refresh Metadata"
    )
    assert window.queue_page.move_up_button.text() == "Move Up"
    assert window.queue_page.move_down_button.text() == "Move Down"
    assert window.queue_page.remove_selected_button.text() == "Remove Selected"


def test_add_video_to_end(qtbot, monkeypatch):
    window = ManagerWindow()
    qtbot.addWidget(window)

    calls = []

    class FakeClient:
        def add_queue_item(self, url, submitted_by=None):
            calls.append(("add", url))
            assert submitted_by is None
            return {"id": 42}

        def queue(self):
            return []

    class FakeDialog:
        ADD_TO_END = "Add to End of Queue"
        ADD_NEXT = "Add Next"

        class DialogCode:
            Accepted = 1

        def __init__(self, parent=None):
            pass

        def exec(self):
            return self.DialogCode.Accepted

        def video_url(self):
            return "https://youtu.be/example"

        def behavior(self):
            return self.ADD_TO_END

    monkeypatch.setattr(
        "app.window.AddVideoDialog",
        FakeDialog,
    )

    window.bot_client = FakeClient()
    window._update_client = lambda: None

    window.show_add_video_dialog()

    assert calls == [
        ("add", "https://youtu.be/example"),
    ]
    assert (
        window.status_label.text()
        == "Video added to end of queue."
    )


def test_add_next_moves_new_item_to_front(qtbot, monkeypatch):
    window = ManagerWindow()
    qtbot.addWidget(window)

    calls = []

    class FakeClient:
        def add_queue_item(self, url, submitted_by=None):
            calls.append(("add", url))
            assert submitted_by is None
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

    class FakeDialog:
        ADD_TO_END = "Add to End of Queue"
        ADD_NEXT = "Add Next"

        class DialogCode:
            Accepted = 1

        def __init__(self, parent=None):
            pass

        def exec(self):
            return self.DialogCode.Accepted

        def video_url(self):
            return "https://youtu.be/example"

        def behavior(self):
            return self.ADD_NEXT

    monkeypatch.setattr(
        "app.window.AddVideoDialog",
        FakeDialog,
    )

    window.bot_client = FakeClient()
    window._update_client = lambda: None

    window.show_add_video_dialog()

    assert calls == [
        ("add", "https://youtu.be/example"),
        ("move", 42, 1),
    ]
    assert window.status_label.text() == "Video added next."


def test_refresh_queue_metadata(qtbot):
    window = ManagerWindow()
    qtbot.addWidget(window)

    calls = []

    class FakeClient:
        def refresh_queue_metadata(self):
            calls.append("refresh-metadata")
            return {"status": "ok"}

        def queue(self):
            return []

    window.bot_client = FakeClient()
    window._update_client = lambda: None

    window.refresh_queue_metadata()

    assert calls == ["refresh-metadata"]
    assert (
        window.status_label.text()
        == "Queue metadata refresh requested."
    )


def test_move_selected_up_uses_hidden_item_id(qtbot):
    window = ManagerWindow()
    qtbot.addWidget(window)

    moved = []

    class FakeClient:
        def move_queue_item(self, item_id, position):
            moved.append((item_id, position))
            return {
                "status": "moved",
                "id": item_id,
                "position": position,
            }

        def queue(self):
            return []

    window.bot_client = FakeClient()
    window._update_client = lambda: None

    window.queue_page.queue_table.setRowCount(2)

    first = QTableWidgetItem("1")
    first.setData(Qt.ItemDataRole.UserRole, 10)
    first.setData(Qt.ItemDataRole.UserRole + 1, 1)
    window.queue_page.queue_table.setItem(0, 0, first)

    second = QTableWidgetItem("2")
    second.setData(Qt.ItemDataRole.UserRole, 42)
    second.setData(Qt.ItemDataRole.UserRole + 1, 2)
    window.queue_page.queue_table.setItem(1, 0, second)

    window.queue_page.queue_table.selectRow(1)

    window.move_selected_up()

    assert moved == [(42, 1)]
    assert window.status_label.text() == "Queue item moved up."


def test_move_selected_down_uses_hidden_item_id(qtbot):
    window = ManagerWindow()
    qtbot.addWidget(window)

    moved = []

    class FakeClient:
        def move_queue_item(self, item_id, position):
            moved.append((item_id, position))
            return {
                "status": "moved",
                "id": item_id,
                "position": position,
            }

        def queue(self):
            return []

    window.bot_client = FakeClient()
    window._update_client = lambda: None

    window.queue_page.queue_table.setRowCount(2)

    first = QTableWidgetItem("1")
    first.setData(Qt.ItemDataRole.UserRole, 10)
    first.setData(Qt.ItemDataRole.UserRole + 1, 1)
    window.queue_page.queue_table.setItem(0, 0, first)

    second = QTableWidgetItem("2")
    second.setData(Qt.ItemDataRole.UserRole, 42)
    second.setData(Qt.ItemDataRole.UserRole + 1, 2)
    window.queue_page.queue_table.setItem(1, 0, second)

    window.queue_page.queue_table.selectRow(0)

    window.move_selected_down()

    assert moved == [(10, 2)]
    assert window.status_label.text() == "Queue item moved down."


def test_move_selected_up_rejects_top_item(qtbot):
    window = ManagerWindow()
    qtbot.addWidget(window)

    moved = []

    class FakeClient:
        def move_queue_item(self, item_id, position):
            moved.append((item_id, position))
            return {}

    window.bot_client = FakeClient()
    window._update_client = lambda: None

    window.queue_page.queue_table.setRowCount(2)

    item = QTableWidgetItem("1")
    item.setData(Qt.ItemDataRole.UserRole, 42)
    item.setData(Qt.ItemDataRole.UserRole + 1, 1)
    window.queue_page.queue_table.setItem(0, 0, item)
    window.queue_page.queue_table.selectRow(0)

    window.move_selected_up()

    assert moved == []
    assert window.status_label.text() == "Queue item is already at the top."


def test_move_selected_down_rejects_bottom_item(qtbot):
    window = ManagerWindow()
    qtbot.addWidget(window)

    moved = []

    class FakeClient:
        def move_queue_item(self, item_id, position):
            moved.append((item_id, position))
            return {}

    window.bot_client = FakeClient()
    window._update_client = lambda: None

    window.queue_page.queue_table.setRowCount(2)

    item = QTableWidgetItem("2")
    item.setData(Qt.ItemDataRole.UserRole, 42)
    item.setData(Qt.ItemDataRole.UserRole + 1, 2)
    window.queue_page.queue_table.setItem(1, 0, item)
    window.queue_page.queue_table.selectRow(1)

    window.move_selected_down()

    assert moved == []
    assert window.status_label.text() == "Queue item is already at the bottom."


def test_move_selected_requires_selection(qtbot):
    window = ManagerWindow()
    qtbot.addWidget(window)

    window.move_selected_up()

    assert window.status_label.text() == "Select a queue item first."


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

    window.queue_page.queue_table.setRowCount(1)

    item = QTableWidgetItem("7")
    item.setData(
        Qt.ItemDataRole.UserRole,
        42,
    )

    window.queue_page.queue_table.setItem(0, 0, item)
    window.queue_page.queue_table.selectRow(0)

    window.remove_selected()

    assert removed == [42]
    assert window.status_label.text() == "Queue item removed."


def test_window_uses_compact_console_layout(qtbot):
    window = ManagerWindow()
    qtbot.addWidget(window)

    assert window.width() == 1000
    assert window.height() == 700
    assert window.twitch_page.channel_list.maximumHeight() == 90


def test_window_has_dark_mode_toggle(qtbot):
    window = ManagerWindow()
    qtbot.addWidget(window)

    assert window.manager_page.dark_mode_toggle.isCheckable()
    assert (
        window.manager_page.dark_mode_toggle.accessibleName()
        == "Dark Mode"
    )
    assert window.manager_page.dark_mode_toggle.isCheckable()
    assert not window.manager_page.dark_mode_toggle.isChecked()


def test_dark_mode_toggle_changes_stylesheet(qtbot):
    window = ManagerWindow()
    qtbot.addWidget(window)

    window.manager_page.dark_mode_toggle.setChecked(True)

    assert window.styleSheet()
    assert window.status_label.text() == "Dark mode enabled."

    window.manager_page.dark_mode_toggle.setChecked(False)

    assert window.styleSheet()
    assert "LINKCUE MANAGER" in window.styleSheet()
    assert "Light dashboard theme" in window.styleSheet()
    assert window.status_label.text() == "Dark mode disabled."
    assert window.status_label.text() == "Dark mode disabled."


def test_window_schedules_initial_player_refresh(qtbot, monkeypatch):
    scheduled = []

    monkeypatch.setattr(
        "app.window.QTimer.singleShot",
        lambda delay, callback: scheduled.append((delay, callback)),
    )

    window = ManagerWindow()
    qtbot.addWidget(window)

    assert len(scheduled) == 4

    assert scheduled[0][0] == 0
    assert scheduled[0][1].__self__ is window
    assert scheduled[0][1].__func__ is ManagerWindow.refresh_queue

    assert scheduled[1][0] == 0
    assert scheduled[1][1].__self__ is window
    assert (
        scheduled[1][1].__func__
        is ManagerWindow.refresh_player_status
    )

    assert scheduled[2][0] == 0
    assert scheduled[2][1].__self__ is window
    assert (
        scheduled[2][1].__func__
        is ManagerWindow.refresh_public_web_setting
    )
