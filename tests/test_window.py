from app.config import APP_NAME, APP_VERSION, DEFAULT_BOT_URL
from app.window import ManagerWindow


def test_window_identity(qtbot):
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
