import json

import httpx
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMessageBox

from app.bot_client import BotClient
from app.pages.streamer_page import StreamerPage
from app.window import ManagerWindow


def test_bot_client_master_and_reset_methods():
    requests = []

    def handler(request):
        requests.append(request)

        if request.url.path == "/player/master":
            assert request.url.params["channel"] == "smokeeeg"

            return httpx.Response(
                200,
                json={
                    "active": True,
                    "channel": "smokeeeg",
                    "client_id": "player-main",
                    "display_name": "Main Player",
                },
            )

        if request.url.path == (
            "/player/master/force-release"
        ):
            assert json.loads(request.content) == {
                "channel": "smokeeeg",
            }

            return httpx.Response(
                200,
                json={
                    "status": "released",
                    "channel": "smokeeeg",
                },
            )

        assert request.url.path == (
            "/auth/reset-streamer-sync-password"
        )
        assert json.loads(request.content) == {
            "current_password": "old-password",
            "new_password": "new-password",
        }

        return httpx.Response(
            200,
            json={
                "status": "streamer_sync_password_reset",
                "revoked_players": 2,
                "invalidated_pairing_codes": 1,
            },
        )

    client = BotClient(
        "http://linkcue.test",
        transport=httpx.MockTransport(handler),
    )

    assert client.player_master_status(
        "smokeeeg"
    )["active"] is True

    assert client.force_release_player_master(
        "smokeeeg"
    )["status"] == "released"

    assert client.reset_streamer_sync_password(
        "old-password",
        "new-password",
    )["revoked_players"] == 2

    assert len(requests) == 3


def test_streamer_page_admin_controls(qtbot):
    refreshed = []
    released = []
    reset = []

    page = StreamerPage(
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
        refresh_master_callback=(
            lambda: refreshed.append(True)
        ),
        force_release_master_callback=(
            lambda: released.append(True)
        ),
        reset_streamer_sync_callback=(
            lambda: reset.append(True)
        ),
    )
    qtbot.addWidget(page)

    page.refresh_master_status_button.click()
    page.force_release_master_button.click()
    page.reset_streamer_sync_password_button.click()

    assert refreshed == [True]
    assert released == [True]
    assert reset == [True]

    assert (
        page.current_streamer_sync_password_input
        .echoMode()
        == page.current_streamer_sync_password_input
        .EchoMode.Password
    )


def test_streamer_page_formats_master_status(qtbot):
    page = StreamerPage(
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
    )
    qtbot.addWidget(page)

    page.set_master_player_status(
        {
            "active": True,
            "channel": "smokeeeg",
            "display_name": "Main Player",
        }
    )

    assert page.master_player_status_label.text() == (
        "Master Player: Active - Main Player for smokeeeg"
    )

    page.set_master_player_status(
        {
            "active": False,
            "channel": "smokeeeg",
        }
    )

    assert page.master_player_status_label.text() == (
        "Master Player: None active for smokeeeg"
    )


def disable_background_refreshes(
    monkeypatch,
):
    method_names = [
        "refresh_queue",
        "refresh_software_status",
        "refresh_public_web_setting",
        "refresh_logging_setting",
        "refresh_twitch_setting",
    ]

    for method_name in method_names:
        monkeypatch.setattr(
            ManagerWindow,
            method_name,
            lambda self: None,
        )


def test_manager_force_releases_master(
    qtbot,
    monkeypatch,
):
    disable_background_refreshes(monkeypatch)

    window = ManagerWindow()
    qtbot.addWidget(window)

    calls = []

    class FakeClient:
        def force_release_player_master(
            self,
            channel,
        ):
            calls.append(channel)

            return {
                "status": "released",
                "channel": channel,
            }

    for timer in window.findChildren(QTimer):
        timer.stop()

    window.bot_client = FakeClient()
    window._update_client = lambda: None

    window.streamer_page.configured_channel_input.setText(
        "SmokeEEG"
    )

    monkeypatch.setattr(
        "app.window.QMessageBox.question",
        lambda *args, **kwargs: (
            QMessageBox.StandardButton.Yes
        ),
    )

    window.force_release_master_player()

    assert calls == ["smokeeeg"]
    assert (
        window.streamer_page
        .master_player_status_label.text()
        == "Master Player: None active for smokeeeg"
    )
    assert (
        window.status_label.text()
        == "Master Player released for smokeeeg."
    )


def test_manager_resets_streamer_sync_password(
    qtbot,
    monkeypatch,
):
    disable_background_refreshes(monkeypatch)

    window = ManagerWindow()
    qtbot.addWidget(window)

    calls = []

    class FakeClient:
        def reset_streamer_sync_password(
            self,
            current_password,
            new_password,
        ):
            calls.append(
                (
                    current_password,
                    new_password,
                )
            )

            return {
                "status": "streamer_sync_password_reset",
                "revoked_players": 3,
                "invalidated_pairing_codes": 1,
            }

    for timer in window.findChildren(QTimer):
        timer.stop()

    window.bot_client = FakeClient()
    window._update_client = lambda: None

    page = window.streamer_page
    page.current_streamer_sync_password_input.setText(
        "old-password"
    )
    page.new_streamer_sync_password_input.setText(
        "new-password"
    )
    page.confirm_streamer_sync_password_input.setText(
        "new-password"
    )

    monkeypatch.setattr(
        "app.window.QMessageBox.question",
        lambda *args, **kwargs: (
            QMessageBox.StandardButton.Yes
        ),
    )

    window.reset_streamer_sync_password()

    assert calls == [
        (
            "old-password",
            "new-password",
        )
    ]
    assert (
        page.current_streamer_sync_password()
        == ""
    )
    assert page.new_streamer_sync_password() == ""
    assert (
        "revoked 3 player pairing"
        in window.status_label.text().lower()
    )


def test_manager_rejects_mismatched_new_passwords(
    qtbot,
    monkeypatch,
):
    disable_background_refreshes(monkeypatch)

    window = ManagerWindow()
    qtbot.addWidget(window)

    page = window.streamer_page
    page.current_streamer_sync_password_input.setText(
        "old-password"
    )
    page.new_streamer_sync_password_input.setText(
        "new-password"
    )
    page.confirm_streamer_sync_password_input.setText(
        "different-password"
    )

    window.reset_streamer_sync_password()

    assert "do not match" in (
        window.status_label.text().lower()
    )
