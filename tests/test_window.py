from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidgetItem

from app.bot_client import BotClientError
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
    assert window.bot_page.bot_protocol_input.currentText() == "http://"
    assert window.bot_page.bot_url_input.text() == "127.0.0.1"
    assert window.bot_page.bot_url() == "http://127.0.0.1"
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

        def player_state(self):
            return {
                "state": "idle",
                "item": None,
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

        def player_state(self):
            return {
                "state": "idle",
                "item": None,
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

        def player_state(self):
            return {
                "state": "idle",
                "item": None,
            }

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

        def player_state(self):
            return {
                "state": "idle",
                "item": None,
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

    window.queue_page._queue_items = [{'id': 10, 'position': 1}, {'id': 42, 'position': 2}]

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

        def player_state(self):
            return {
                "state": "idle",
                "item": None,
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

    window.queue_page._queue_items = [{'id': 10, 'position': 1}, {'id': 42, 'position': 2}]

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

        def player_state(self):
            return {
                "state": "idle",
                "item": None,
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


def test_window_defaults_to_automatic_connection_mode(qtbot, monkeypatch):
    monkeypatch.delenv("LINKCUE_BOT_URL", raising=False)

    window = ManagerWindow()
    qtbot.addWidget(window)

    assert window.bot_page.connection_mode() == "automatic"
    assert window.bot_page.bot_url() == "http://127.0.0.1"


def test_update_client_automatic_mode_uses_portless_url(
    qtbot,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.window.QueueEventListener.start",
        lambda self: None,
    )

    window = ManagerWindow()
    qtbot.addWidget(window)

    window.bot_page.bot_protocol_input.setCurrentText("https://")
    window.bot_page.bot_url_input.setText(
        "linkcue.apps.bot-hosting.cloud"
    )
    window.bot_page.bot_port_input.setText("8000")

    window._update_client()

    assert (
        window.bot_client.base_url
        == "https://linkcue.apps.bot-hosting.cloud"
    )

def test_window_automatic_mode_uses_portless_client(
    qtbot,
    monkeypatch,
):
    monkeypatch.delenv("LINKCUE_BOT_URL", raising=False)
    monkeypatch.delenv("LINKCUE_BOT_PORT", raising=False)

    monkeypatch.setattr(
        "app.window.load_shared_settings",
        lambda: {
            "bot_url": "https://linkcue.apps.bot-hosting.cloud",
            "bot_port": 8000,
            "bot_connection_mode": "automatic",
        },
    )

    window = ManagerWindow()
    qtbot.addWidget(window)

    assert window.bot_page.connection_mode() == "automatic"
    assert (
        window.bot_client.base_url
        == "https://linkcue.apps.bot-hosting.cloud"
    )


def test_window_manual_mode_uses_configured_port(
    qtbot,
    monkeypatch,
):
    monkeypatch.delenv("LINKCUE_BOT_URL", raising=False)
    monkeypatch.delenv("LINKCUE_BOT_PORT", raising=False)

    monkeypatch.setattr(
        "app.window.load_shared_settings",
        lambda: {
            "bot_url": "http://127.0.0.1",
            "bot_port": 9123,
            "bot_connection_mode": "manual",
        },
    )

    window = ManagerWindow()
    qtbot.addWidget(window)

    assert window.bot_page.connection_mode() == "manual"
    assert window.bot_client.base_url == "http://127.0.0.1:9123"

def test_save_bot_url_persists_connection_mode(
    qtbot,
    monkeypatch,
):
    settings = {
        "bot_url": "http://127.0.0.1",
        "bot_port": 8000,
        "bot_connection_mode": "automatic",
    }
    saved = {}

    monkeypatch.delenv("LINKCUE_BOT_URL", raising=False)
    monkeypatch.delenv("LINKCUE_BOT_PORT", raising=False)
    monkeypatch.setattr(
        "app.window.load_shared_settings",
        lambda: dict(settings),
    )
    monkeypatch.setattr(
        "app.window.save_shared_settings",
        lambda value: saved.update(value),
    )

    window = ManagerWindow()
    qtbot.addWidget(window)

    class FakeBotClient:
        def set_bot_connection(self, host, port):
            return {"restart_required": False}

        def set_public_web_enabled(
            self,
            enabled,
            port,
            public_url=None,
            connection_mode=None,
        ):
            return {
                "enabled": enabled,
                "port": port,
                "public_url": public_url,
                "connection_mode": connection_mode,
            }


        def set_logging_setting(self, enabled, timezone):
            return {
                "enabled": enabled,
                "timezone": timezone,
            }
    window.bot_client = FakeBotClient()
    monkeypatch.setattr(
        window,
        "_update_client",
        lambda: None,
    )

    window.bot_page.connection_mode_input.setCurrentIndex(1)
    assert window.bot_page.connection_mode() == "manual"

    window.save_bot_url()

    assert saved["bot_connection_mode"] == "manual"

def test_save_bot_url_updates_client_before_remote_save(
    qtbot,
    monkeypatch,
):
    monkeypatch.delenv("LINKCUE_BOT_URL", raising=False)
    monkeypatch.delenv("LINKCUE_BOT_PORT", raising=False)

    monkeypatch.setattr(
        "app.window.load_shared_settings",
        lambda: {
            "bot_url": "http://127.0.0.1",
            "bot_port": 8000,
            "bot_connection_mode": "automatic",
        },
    )

    window = ManagerWindow()
    qtbot.addWidget(window)

    window.bot_page.bot_protocol_input.setCurrentText("https://")
    window.bot_page.bot_url_input.setText(
        "linkcue.apps.bot-hosting.cloud"
    )

    assert window.bot_client.base_url == "http://127.0.0.1"

    window._update_client()

    assert (
        window.bot_client.base_url
        == "https://linkcue.apps.bot-hosting.cloud"
    )

def test_save_bot_url_uses_current_ui_connection(
    qtbot,
    monkeypatch,
):
    monkeypatch.delenv("LINKCUE_BOT_URL", raising=False)
    monkeypatch.delenv("LINKCUE_BOT_PORT", raising=False)

    monkeypatch.setattr(
        "app.window.load_shared_settings",
        lambda: {
            "bot_url": "http://127.0.0.1",
            "bot_port": 8000,
            "bot_connection_mode": "automatic",
        },
    )
    monkeypatch.setattr(
        "app.window.save_shared_settings",
        lambda value: None,
    )

    window = ManagerWindow()
    qtbot.addWidget(window)

    calls = []

    class FakeBotClient:
        base_url = "https://linkcue.apps.bot-hosting.cloud"

        def set_bot_connection(self, host, port):
            calls.append(("bot", self.base_url, host, port))
            return {"restart_required": False}

        def set_public_web_enabled(
            self,
            enabled,
            port,
            public_url=None,
            connection_mode=None,
        ):
            return {
                "enabled": enabled,
                "port": port,
                "public_url": public_url,
                "connection_mode": connection_mode,
            }


        def set_logging_setting(self, enabled, timezone):
            return {
                "enabled": enabled,
                "timezone": timezone,
            }
    def fake_update_client():
        window.bot_client = FakeBotClient()

    monkeypatch.setattr(
        window,
        "_update_client",
        fake_update_client,
    )

    window.bot_page.bot_protocol_input.setCurrentText("https://")
    window.bot_page.bot_url_input.setText(
        "linkcue.apps.bot-hosting.cloud"
    )

    window.save_bot_url()

    assert calls
    assert (
        calls[0][1]
        == "https://linkcue.apps.bot-hosting.cloud"
    )




def test_refresh_public_web_setting_applies_bot_configuration(
    qtbot,
    monkeypatch,
):
    monkeypatch.delenv("LINKCUE_BOT_URL", raising=False)
    monkeypatch.delenv("LINKCUE_BOT_PORT", raising=False)

    monkeypatch.setattr(
        "app.window.load_shared_settings",
        lambda: {
            "bot_url": "http://de1.bot-hosting.cloud",
            "bot_port": 25479,
            "bot_connection_mode": "manual",
        },
    )

    window = ManagerWindow()
    qtbot.addWidget(window)

    class FakeBotClient:
        def public_web_setting(self):
            return {
                "enabled": True,
                "public_url": (
                    "https://linkcue.apps.bot-hosting.cloud"
                ),
                "connection_mode": "automatic",
                "port": 9000,
            }

    window.bot_client = FakeBotClient()

    monkeypatch.setattr(
        window,
        "_update_client",
        lambda: None,
    )

    window.refresh_public_web_setting()

    assert (
        window.bot_page.public_web_host()
        == "https://linkcue.apps.bot-hosting.cloud"
    )
    assert window.bot_page.public_web_mode() == "automatic"
    assert window.bot_page.public_web_port() == 9000
    assert window.bot_page.requested_public_web_enabled() is True


def test_save_bot_url_does_not_save_public_web(
    qtbot,
    monkeypatch,
):
    monkeypatch.delenv("LINKCUE_BOT_URL", raising=False)
    monkeypatch.delenv("LINKCUE_BOT_PORT", raising=False)

    monkeypatch.setattr(
        "app.window.load_shared_settings",
        lambda: {
            "bot_url": "http://127.0.0.1",
            "bot_port": 8000,
            "bot_connection_mode": "automatic",
        },
    )
    monkeypatch.setattr(
        "app.window.save_shared_settings",
        lambda value: None,
    )

    window = ManagerWindow()
    qtbot.addWidget(window)

    class FakeBotClient:
        def set_bot_connection(self, host, port):
            return {"restart_required": False}

        def set_public_web_enabled(self, *args, **kwargs):
            raise AssertionError(
                "Save Connection must not save Public Web settings"
            )

        def set_logging_setting(self, *args, **kwargs):
            return {
                "enabled": True,
                "timezone": "America/Detroit",
            }

    window.bot_client = FakeBotClient()

    monkeypatch.setattr(
        window,
        "_update_client",
        lambda: None,
    )

    window.save_bot_url()


def test_save_bot_url_does_not_save_logging(
    qtbot,
    monkeypatch,
):
    monkeypatch.delenv("LINKCUE_BOT_URL", raising=False)
    monkeypatch.delenv("LINKCUE_BOT_PORT", raising=False)

    monkeypatch.setattr(
        "app.window.load_shared_settings",
        lambda: {
            "bot_url": "http://127.0.0.1",
            "bot_port": 8000,
            "bot_connection_mode": "automatic",
        },
    )
    monkeypatch.setattr(
        "app.window.save_shared_settings",
        lambda value: None,
    )

    window = ManagerWindow()
    qtbot.addWidget(window)

    class FakeBotClient:
        def set_bot_connection(self, host, port):
            return {"restart_required": False}

        def set_public_web_enabled(
            self,
            enabled,
            port,
            public_url=None,
            connection_mode=None,
        ):
            return {
                "enabled": enabled,
                "port": port,
                "public_url": public_url,
                "connection_mode": connection_mode,
            }

        def set_logging_setting(self, *args, **kwargs):
            raise AssertionError(
                "Save Connection must not save Logging settings"
            )

    window.bot_client = FakeBotClient()

    monkeypatch.setattr(
        window,
        "_update_client",
        lambda: None,
    )

    window.save_bot_url()


def test_save_public_web_setting_sends_only_public_web_configuration(
    qtbot,
    monkeypatch,
):
    window = ManagerWindow()
    qtbot.addWidget(window)

    calls = []

    class FakeBotClient:
        def set_public_web_enabled(
            self,
            enabled,
            port,
            public_url=None,
            connection_mode=None,
        ):
            calls.append(
                (
                    enabled,
                    port,
                    public_url,
                    connection_mode,
                )
            )
            return {
                "enabled": enabled,
                "port": port,
                "public_url": public_url,
                "connection_mode": connection_mode,
            }

        def set_bot_connection(self, *args, **kwargs):
            raise AssertionError(
                "Save Public Web must not save Bot Connection settings"
            )

        def set_logging_setting(self, *args, **kwargs):
            raise AssertionError(
                "Save Public Web must not save Logging settings"
            )

    window.bot_client = FakeBotClient()

    monkeypatch.setattr(
        window,
        "_update_client",
        lambda: None,
    )

    window.bot_page.public_web_toggle.setChecked(True)
    window.bot_page.public_web_protocol_input.setCurrentText(
        "https://"
    )
    window.bot_page.public_web_url_input.setText(
        "linkcue.apps.bot-hosting.cloud"
    )
    window.bot_page.public_web_mode_input.setCurrentText(
        "Automatic"
    )
    window.bot_page.public_web_port_input.setText("9000")

    window.save_public_web_setting()

    assert calls == [
        (
            True,
            9000,
            "https://linkcue.apps.bot-hosting.cloud",
            "automatic",
        )
    ]


def test_save_bot_settings_shows_restart_required_popup(
    qtbot,
    monkeypatch,
):
    monkeypatch.delenv("LINKCUE_BOT_URL", raising=False)
    monkeypatch.delenv("LINKCUE_BOT_PORT", raising=False)

    monkeypatch.setattr(
        "app.window.load_shared_settings",
        lambda: {
            "bot_url": "http://127.0.0.1",
            "bot_port": 8000,
            "bot_connection_mode": "automatic",
        },
    )
    monkeypatch.setattr(
        "app.window.save_shared_settings",
        lambda value: None,
    )

    window = ManagerWindow()
    qtbot.addWidget(window)

    class FakeBotClient:
        def set_bot_connection(self, host, port):
            return {"restart_required": True}

        def set_public_web_enabled(
            self,
            enabled,
            port,
            public_url=None,
            connection_mode=None,
        ):
            return {
                "enabled": enabled,
                "port": port,
                "public_url": public_url,
                "connection_mode": connection_mode,
            }

        def set_logging_setting(self, enabled, timezone):
            return {
                "enabled": enabled,
                "timezone": timezone,
            }

    window.bot_client = FakeBotClient()

    monkeypatch.setattr(
        window,
        "_update_client",
        lambda: None,
    )

    popup_calls = []

    monkeypatch.setattr(
        "app.window.QMessageBox.warning",
        lambda *args: popup_calls.append(args),
    )

    window.save_bot_url()

    assert len(popup_calls) == 1
    assert "restart" in str(popup_calls[0]).lower()



def test_save_bot_settings_does_not_show_restart_popup_when_not_required(
    qtbot,
    monkeypatch,
):
    monkeypatch.delenv("LINKCUE_BOT_URL", raising=False)
    monkeypatch.delenv("LINKCUE_BOT_PORT", raising=False)

    monkeypatch.setattr(
        "app.window.load_shared_settings",
        lambda: {
            "bot_url": "http://127.0.0.1",
            "bot_port": 8000,
            "bot_connection_mode": "automatic",
        },
    )
    monkeypatch.setattr(
        "app.window.save_shared_settings",
        lambda value: None,
    )

    window = ManagerWindow()
    qtbot.addWidget(window)

    class FakeBotClient:
        def set_bot_connection(self, host, port):
            return {"restart_required": False}

        def set_public_web_enabled(
            self,
            enabled,
            port,
            public_url=None,
            connection_mode=None,
        ):
            return {
                "enabled": enabled,
                "port": port,
                "public_url": public_url,
                "connection_mode": connection_mode,
            }

        def set_logging_setting(self, enabled, timezone):
            return {
                "enabled": enabled,
                "timezone": timezone,
            }

    window.bot_client = FakeBotClient()

    monkeypatch.setattr(
        window,
        "_update_client",
        lambda: None,
    )

    popup_calls = []

    monkeypatch.setattr(
        "app.window.QMessageBox.warning",
        lambda *args: popup_calls.append(args),
    )

    window.save_bot_url()

    assert popup_calls == []



def test_save_bot_settings_persists_local_connection_when_bot_is_unreachable(
    qtbot,
    monkeypatch,
):
    monkeypatch.delenv("LINKCUE_BOT_URL", raising=False)
    monkeypatch.delenv("LINKCUE_BOT_PORT", raising=False)

    saved = {}

    monkeypatch.setattr(
        "app.window.load_shared_settings",
        lambda: {
            "bot_url": "http://127.0.0.1",
            "bot_port": 8000,
            "bot_connection_mode": "automatic",
        },
    )
    monkeypatch.setattr(
        "app.window.save_shared_settings",
        lambda value: saved.update(value),
    )

    window = ManagerWindow()
    qtbot.addWidget(window)

    window.bot_page.bot_protocol_input.setCurrentText("http://")
    window.bot_page.bot_url_input.setText(
        "de1.bot-hosting.cloud"
    )
    window.bot_page.bot_port_input.setText("25479")
    window.bot_page.connection_mode_input.setCurrentText(
        "Manual"
    )

    class FakeBotClient:
        def set_bot_connection(self, host, port):
            raise BotClientError("Bot unavailable")

    window.bot_client = FakeBotClient()

    monkeypatch.setattr(
        window,
        "_update_client",
        lambda: None,
    )
    monkeypatch.setattr(
        window,
        "_show_error",
        lambda exc: None,
    )

    window.save_bot_url()

    assert saved["bot_url"] == "http://de1.bot-hosting.cloud"
    assert saved["bot_port"] == 25479
    assert saved["bot_connection_mode"] == "manual"


def test_restart_bot_cancel_does_not_request_restart(
    qtbot,
    monkeypatch,
):
    from PySide6.QtWidgets import QMessageBox

    window = ManagerWindow()
    qtbot.addWidget(window)

    calls = []

    class FakeClient:
        def restart_bot(self):
            calls.append(True)
            return {"status": "restart_requested"}

    window.bot_client = FakeClient()
    window._update_client = lambda: None

    monkeypatch.setattr(
        "app.window.QMessageBox.question",
        lambda *args, **kwargs:
            QMessageBox.StandardButton.No,
    )

    window.restart_bot()

    assert calls == []


def test_restart_bot_confirm_requests_restart_once(
    qtbot,
    monkeypatch,
):
    from PySide6.QtWidgets import QMessageBox

    window = ManagerWindow()
    qtbot.addWidget(window)

    calls = []

    class FakeClient:
        def restart_bot(self):
            calls.append(True)
            return {"status": "restart_requested"}

    window.bot_client = FakeClient()
    window._update_client = lambda: None

    monkeypatch.setattr(
        "app.window.QMessageBox.question",
        lambda *args, **kwargs:
            QMessageBox.StandardButton.Yes,
    )

    window.restart_bot()

    assert calls == [True]


def test_queue_snapshot_renders_now_playing_before_queued(qtbot):
    window = ManagerWindow()
    qtbot.addWidget(window)

    rendered = []
    window._render_queue = lambda items: rendered.extend(items)

    window._apply_queue_snapshot(
        {
            "playing": [
                {
                    "id": 10,
                    "title": "Now Playing",
                    "status": "playing",
                    "position": None,
                }
            ],
            "queued": [
                {
                    "id": 11,
                    "title": "Queued Video",
                    "status": "queued",
                    "position": 1,
                }
            ],
        }
    )

    assert [item["id"] for item in rendered] == [10, 11]
    assert rendered[0]["status"] == "playing"
    assert rendered[1]["position"] == 1


def test_manual_queue_refresh_includes_now_playing(qtbot):
    window = ManagerWindow()
    qtbot.addWidget(window)

    calls = []

    class FakeClient:
        def player_state(self):
            calls.append("player-state")
            return {
                "state": "playing",
                "item": {
                    "id": 20,
                    "title": "Now Playing",
                    "status": "playing",
                    "position": None,
                },
            }

        def queue(self):
            calls.append("queue")
            return [
                {
                    "id": 21,
                    "title": "Queued Video",
                    "status": "queued",
                    "position": 1,
                }
            ]

    rendered = []
    window.bot_client = FakeClient()
    window._update_client = lambda: None
    window._render_queue = lambda items: rendered.extend(items)

    window.refresh_queue()

    assert calls == ["player-state", "queue"]
    assert [item["id"] for item in rendered] == [20, 21]
    assert rendered[0]["status"] == "playing"
    assert rendered[1]["position"] == 1



def test_move_selected_to_position_uses_dialog_target(qtbot, monkeypatch):
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

        def player_state(self):
            return {
                "state": "idle",
                "item": None,
            }

        def queue(self):
            return []

    window.bot_client = FakeClient()
    window._update_client = lambda: None

    window.queue_page.queue_table.setRowCount(5)

    for row, position in enumerate(range(1, 6)):
        item = QTableWidgetItem(str(position))
        item.setData(
            Qt.ItemDataRole.UserRole,
            42 if position == 2 else 100 + position,
        )
        item.setData(
            Qt.ItemDataRole.UserRole + 1,
            position,
        )
        window.queue_page.queue_table.setItem(row, 0, item)

    window.queue_page._queue_items = [{'id': 101, 'position': 1}, {'id': 42, 'position': 2}, {'id': 103, 'position': 3}, {'id': 104, 'position': 4}, {'id': 105, 'position': 5}]

    window.queue_page.queue_table.selectRow(1)

    dialog_calls = []

    def fake_get_int(
        parent,
        title,
        label,
        value,
        minimum,
        maximum,
        step,
    ):
        dialog_calls.append(
            (title, label, value, minimum, maximum, step)
        )
        return 4, True

    monkeypatch.setattr(
        "app.window.QInputDialog.getInt",
        fake_get_int,
    )

    window.move_selected_to_position()

    assert dialog_calls == [
        (
            "Move Queue Item",
            "Move selected item to position:",
            2,
            1,
            5,
            1,
        )
    ]
    assert moved == [(42, 4)]
    assert (
        window.status_label.text()
        == "Queue item moved to position 4."
    )


def test_move_selected_to_position_cancel_is_noop(qtbot, monkeypatch):
    window = ManagerWindow()
    qtbot.addWidget(window)

    moved = []

    class FakeClient:
        def move_queue_item(self, item_id, position):
            moved.append((item_id, position))
            return {}

    window.bot_client = FakeClient()
    window._update_client = lambda: None

    window.queue_page.queue_table.setRowCount(3)

    item = QTableWidgetItem("2")
    item.setData(Qt.ItemDataRole.UserRole, 42)
    item.setData(Qt.ItemDataRole.UserRole + 1, 2)
    window.queue_page.queue_table.setItem(1, 0, item)
    window.queue_page.queue_table.selectRow(1)

    monkeypatch.setattr(
        "app.window.QInputDialog.getInt",
        lambda *args, **kwargs: (2, False),
    )

    window.move_selected_to_position()

    assert moved == []



def test_move_to_position_excludes_now_playing_from_maximum(
    qtbot,
    monkeypatch,
):
    window = ManagerWindow()
    qtbot.addWidget(window)

    window.queue_page.queue_table.setRowCount(5)

    now_playing = QTableWidgetItem("")
    now_playing.setData(Qt.ItemDataRole.UserRole, 100)
    now_playing.setData(Qt.ItemDataRole.UserRole + 1, None)
    window.queue_page.queue_table.setItem(0, 0, now_playing)

    for row, position in enumerate(range(1, 5), start=1):
        item = QTableWidgetItem(str(position))
        item.setData(Qt.ItemDataRole.UserRole, 200 + position)
        item.setData(
            Qt.ItemDataRole.UserRole + 1,
            position,
        )
        window.queue_page.queue_table.setItem(row, 0, item)

    window.queue_page._queue_items = [{'id': 100, 'position': None, 'status': 'playing'}, {'id': 201, 'position': 1}, {'id': 202, 'position': 2}, {'id': 203, 'position': 3}, {'id': 204, 'position': 4}]

    window.queue_page.queue_table.selectRow(2)

    dialog_calls = []

    def fake_get_int(
        parent,
        title,
        label,
        value,
        minimum,
        maximum,
        step,
    ):
        dialog_calls.append(
            (value, minimum, maximum, step)
        )
        return value, False

    monkeypatch.setattr(
        "app.window.QInputDialog.getInt",
        fake_get_int,
    )

    window.move_selected_to_position()

    assert dialog_calls == [(2, 1, 4, 1)]


def test_move_to_end_excludes_now_playing_from_queue_length(qtbot):
    window = ManagerWindow()
    qtbot.addWidget(window)

    moved = []

    class FakeClient:
        def move_queue_item(self, item_id, position):
            moved.append((item_id, position))
            return {}

        def player_state(self):
            return {
                "state": "idle",
                "item": None,
            }

        def queue(self):
            return []

    window.bot_client = FakeClient()
    window._update_client = lambda: None

    window.queue_page.queue_table.setRowCount(5)

    now_playing = QTableWidgetItem("")
    now_playing.setData(Qt.ItemDataRole.UserRole, 100)
    now_playing.setData(Qt.ItemDataRole.UserRole + 1, None)
    window.queue_page.queue_table.setItem(0, 0, now_playing)

    for row, position in enumerate(range(1, 5), start=1):
        item = QTableWidgetItem(str(position))
        item.setData(Qt.ItemDataRole.UserRole, 200 + position)
        item.setData(
            Qt.ItemDataRole.UserRole + 1,
            position,
        )
        window.queue_page.queue_table.setItem(row, 0, item)

    window.queue_page._queue_items = [{'id': 100, 'position': None, 'status': 'playing'}, {'id': 201, 'position': 1}, {'id': 202, 'position': 2}, {'id': 203, 'position': 3}, {'id': 204, 'position': 4}]

    window.queue_page.queue_table.selectRow(2)

    window.move_selected_to_end()

    assert moved == [(202, 4)]


def test_move_selected_to_rejects_position_outside_real_queue(qtbot):
    window = ManagerWindow()
    qtbot.addWidget(window)

    moved = []

    class FakeClient:
        def move_queue_item(self, item_id, position):
            moved.append((item_id, position))
            return {}

    window.bot_client = FakeClient()
    window._update_client = lambda: None

    window.queue_page.queue_table.setRowCount(3)

    first = QTableWidgetItem("1")
    first.setData(Qt.ItemDataRole.UserRole, 10)
    first.setData(Qt.ItemDataRole.UserRole + 1, 1)
    window.queue_page.queue_table.setItem(0, 0, first)

    second = QTableWidgetItem("2")
    second.setData(Qt.ItemDataRole.UserRole, 20)
    second.setData(Qt.ItemDataRole.UserRole + 1, 2)
    window.queue_page.queue_table.setItem(1, 0, second)

    window.queue_page._queue_items = [{'id': 10, 'position': 1}, {'id': 20, 'position': 2}]

    window.queue_page.queue_table.selectRow(0)

    window._move_selected_to(
        3,
        "should not happen",
    )

    assert moved == []
    assert (
        window.status_label.text()
        == "Position 3 is outside the queue range (1-2)."
    )



def test_export_selected_queue_items_uses_selected_ids():
    import inspect

    from app.window import ManagerWindow

    source = inspect.getsource(
        ManagerWindow.export_selected_queue_csv
    )

    assert "selected_queue_item_ids" in source
    assert "Export LinkCue Queue Selection" in source


def test_queue_page_exposes_selected_queue_item_ids():
    from app.pages.queue_page import QueuePage

    assert hasattr(
        QueuePage,
        "selected_queue_item_ids",
    )


def test_max_queue_position_uses_full_queue_when_filtered(qtbot):
    window = ManagerWindow()
    qtbot.addWidget(window)

    window.queue_page.render_items(
        [
            {
                "id": 10,
                "position": 1,
                "title": "Visible Video",
                "status": "queued",
            },
            {
                "id": 20,
                "position": 2,
                "title": "Hidden Video A",
                "status": "queued",
            },
            {
                "id": 30,
                "position": 3,
                "title": "Hidden Video B",
                "status": "queued",
            },
        ]
    )

    assert window.queue_page.max_queue_position() == 3

    window.queue_page.apply_search("Visible Video")

    assert window.queue_page.queue_table.rowCount() == 1
    assert window.queue_page.max_queue_position() == 3



def test_refresh_current_view_loads_history(qtbot, monkeypatch):
    window = ManagerWindow()
    qtbot.addWidget(window)

    monkeypatch.setattr(
        window,
        "_update_client",
        lambda: None,
    )

    history_items = [
        {
            "id": 99,
            "position": None,
            "title": "Played Video",
            "status": "played",
        }
    ]

    monkeypatch.setattr(
        window.bot_client,
        "history",
        lambda: history_items,
    )

    window.queue_page.set_view_mode("history")
    window.refresh_current_view()

    assert window.queue_page.view_mode == "history"
    assert window.queue_page._queue_items == history_items
    assert window.queue_page.queue_table.rowCount() == 1


def test_queue_changed_does_not_replace_history(
    qtbot,
    monkeypatch,
):
    window = ManagerWindow()
    qtbot.addWidget(window)

    monkeypatch.setattr(
        window,
        "_update_client",
        lambda: None,
    )

    history_items = [
        {
            "id": 99,
            "position": None,
            "title": "Played Video",
            "status": "played",
        }
    ]

    monkeypatch.setattr(
        window.bot_client,
        "history",
        lambda: history_items,
    )

    window.queue_page.set_view_mode("history")
    window.refresh_current_view()

    window.refresh_queue(
        {
            "type": "queue_changed",
            "snapshot": {
                "playing": [],
                "queued": [
                    {
                        "id": 1,
                        "position": 1,
                        "title": "Queued Video",
                        "status": "queued",
                    }
                ],
            },
        }
    )

    assert window.queue_page.view_mode == "history"
    assert window.queue_page._queue_items == history_items

def test_save_streamer_settings_splits_shared_and_manager_settings(
    qtbot,
    monkeypatch,
):
    window = ManagerWindow()
    qtbot.addWidget(window)

    shared_settings = {
        "bot_url": "http://example.test",
    }
    manager_settings = {
        "manager_username": "Steve",
        "dark_mode": True,
    }

    saved_shared = []
    saved_manager = []

    monkeypatch.setattr(
        "app.window.load_shared_settings",
        lambda: dict(shared_settings),
    )
    monkeypatch.setattr(
        "app.window.save_shared_settings",
        lambda settings: saved_shared.append(dict(settings)),
    )
    monkeypatch.setattr(
        "app.window.load_manager_settings",
        lambda: dict(manager_settings),
    )
    monkeypatch.setattr(
        "app.window.save_manager_settings",
        lambda settings: saved_manager.append(dict(settings)),
    )

    window.streamer_page.streamer_name_input.setText(
        "smokeeeg"
    )
    window.streamer_page.twitch_url_input.setText(
        "https://twitch.tv/smokeeeg"
    )
    window.streamer_page.populate_from_twitch_toggle.setChecked(
        True
    )

    window.save_streamer_settings()

    assert saved_shared == [
        {
            "bot_url": "http://example.test",
            "streamer_name": "smokeeeg",
            "streamer_twitch_url": (
                "https://twitch.tv/smokeeeg"
            ),
        }
    ]

    assert saved_manager == [
        {
            "manager_username": "Steve",
            "dark_mode": True,
            "populate_from_twitch_url": True,
        }
    ]


def test_window_loads_streamer_identity_from_shared_settings(
    qtbot,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.window.load_shared_settings",
        lambda: {
            "streamer_name": "smokeeeg",
            "streamer_twitch_url": (
                "https://twitch.tv/smokeeeg"
            ),
        },
    )

    monkeypatch.setattr(
        "app.window.load_manager_settings",
        lambda: {
            "populate_from_twitch_url": True,
        },
    )

    window = ManagerWindow()
    qtbot.addWidget(window)

    assert (
        window.streamer_page.streamer_name()
        == "smokeeeg"
    )

    assert (
        window.streamer_page.twitch_url()
        == "https://twitch.tv/smokeeeg"
    )

    assert (
        window.streamer_page
        .populate_from_twitch_enabled()
        is True
    )

    assert (
        window.twitch_page.entered_channel()
        == "smokeeeg"
    )


def test_window_migrates_legacy_streamer_identity_to_shared_settings(
    qtbot,
    monkeypatch,
):
    shared_settings = {}

    manager_settings = {
        "streamer_name": "smokeeeg",
        "streamer_twitch_url": (
            "https://twitch.tv/smokeeeg"
        ),
        "populate_from_twitch_url": True,
    }

    saved_shared = []

    monkeypatch.setattr(
        "app.window.load_shared_settings",
        lambda: dict(shared_settings),
    )

    monkeypatch.setattr(
        "app.window.load_manager_settings",
        lambda: dict(manager_settings),
    )

    monkeypatch.setattr(
        "app.window.save_shared_settings",
        lambda settings: saved_shared.append(dict(settings)),
    )

    window = ManagerWindow()
    qtbot.addWidget(window)

    assert (
        window.streamer_page.streamer_name()
        == "smokeeeg"
    )

    assert (
        window.streamer_page.twitch_url()
        == "https://twitch.tv/smokeeeg"
    )

    assert saved_shared == [
        {
            "streamer_name": "smokeeeg",
            "streamer_twitch_url": (
                "https://twitch.tv/smokeeeg"
            ),
        }
    ]
