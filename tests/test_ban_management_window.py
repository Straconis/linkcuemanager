import pytest

from app.window import ManagerWindow


@pytest.fixture(autouse=True)
def disable_startup_refreshes(monkeypatch):
    monkeypatch.setattr(
        "app.window.QTimer.singleShot",
        lambda delay, callback: None,
    )


def test_window_has_ban_management_tab(qtbot):
    window = ManagerWindow()
    qtbot.addWidget(window)

    assert window.navigation_buttons["bans"].text() == "Bans"
    assert window.ban_page.creator_table.rowCount() == 0
    assert window.ban_page.video_table.rowCount() == 0

    window.navigation_buttons["bans"].click()

    assert (
        window.page_stack.currentWidget()
        is window.ban_page
    )


def test_refresh_bans_displays_bot_records(qtbot):
    window = ManagerWindow()
    qtbot.addWidget(window)

    calls = []

    class FakeClient:
        def creator_bans(
            self,
            *,
            include_inactive,
        ):
            calls.append(
                ("creators", include_inactive)
            )

            return [
                {
                    "id": 12,
                    "platform": "youtube",
                    "video_channel": "Test Channel",
                    "video_creator_id": "UC_TEST",
                    "reason": "Repeated submissions",
                    "created_by": "manager-steve",
                    "active": 1,
                    "created_at": "2026-09-07 20:00:00",
                    "updated_at": "2026-09-07 20:00:00",
                }
            ]

        def video_bans(
            self,
            *,
            include_inactive,
        ):
            calls.append(
                ("videos", include_inactive)
            )

            return [
                {
                    "id": 21,
                    "platform": "youtube",
                    "title": "Blocked Video",
                    "video_platform_id": "video123",
                    "url": "https://youtu.be/video123",
                    "reason": "Do not play",
                    "created_by": "manager-steve",
                    "active": 0,
                    "created_at": "2026-09-07 20:00:00",
                    "updated_at": "2026-09-07 21:00:00",
                }
            ]

    window.bot_client = FakeClient()
    window._update_client = lambda: None

    window.refresh_bans()

    assert calls == [
        ("creators", True),
        ("videos", True),
    ]
    assert window.ban_page.creator_table.rowCount() == 1
    assert window.ban_page.video_table.rowCount() == 1
    assert (
        window.ban_page.creator_table.item(0, 1).text()
        == "Test Channel"
    )
    assert (
        window.ban_page.video_table.item(0, 1).text()
        == "Blocked Video"
    )
    assert window.status_label.text() == "Bans refreshed."


def test_refresh_bans_respects_active_only_filter(qtbot):
    window = ManagerWindow()
    qtbot.addWidget(window)

    calls = []

    class FakeClient:
        def creator_bans(
            self,
            *,
            include_inactive,
        ):
            calls.append(include_inactive)
            return []

        def video_bans(
            self,
            *,
            include_inactive,
        ):
            calls.append(include_inactive)
            return []

    window.bot_client = FakeClient()
    window._update_client = lambda: None

    window.ban_page.include_inactive_toggle.setChecked(
        False
    )

    calls.clear()
    window.refresh_bans()

    assert calls == [
        False,
        False,
    ]


def test_add_creator_and_video_bans(
    qtbot,
    monkeypatch,
):
    window = ManagerWindow()
    qtbot.addWidget(window)

    calls = []

    class FakeClient:
        def add_creator_ban(self, **values):
            calls.append(
                ("add_creator", values)
            )
            return {"ban_id": 12}

        def add_video_ban(self, **values):
            calls.append(
                ("add_video", values)
            )
            return {"ban_id": 21}

        def creator_bans(
            self,
            *,
            include_inactive,
        ):
            return []

        def video_bans(
            self,
            *,
            include_inactive,
        ):
            return []

    class FakeCreatorDialog:
        class DialogCode:
            Accepted = 1

        def __init__(self, parent):
            assert parent is window

        def exec(self):
            return self.DialogCode.Accepted

        def values(self):
            return {
                "platform": "youtube",
                "video_creator_id": "UC_TEST",
                "video_channel": "Test Channel",
                "reason": "Repeated submissions",
            }

    class FakeVideoDialog:
        class DialogCode:
            Accepted = 1

        def __init__(self, parent):
            assert parent is window

        def exec(self):
            return self.DialogCode.Accepted

        def values(self):
            return {
                "platform": "youtube",
                "video_platform_id": "video123",
                "title": "Blocked Video",
                "url": "https://youtu.be/video123",
                "reason": "Do not play",
            }

    monkeypatch.setattr(
        "app.window.CreatorBanDialog",
        FakeCreatorDialog,
    )
    monkeypatch.setattr(
        "app.window.VideoBanDialog",
        FakeVideoDialog,
    )

    window.bot_client = FakeClient()
    window._update_client = lambda: None

    window.show_add_creator_ban_dialog()

    assert calls[0] == (
        "add_creator",
        {
            "platform": "youtube",
            "video_creator_id": "UC_TEST",
            "video_channel": "Test Channel",
            "reason": "Repeated submissions",
        },
    )
    assert (
        window.status_label.text()
        == "Creator ban added."
    )

    window.show_add_video_ban_dialog()

    assert calls[1] == (
        "add_video",
        {
            "platform": "youtube",
            "video_platform_id": "video123",
            "title": "Blocked Video",
            "url": "https://youtu.be/video123",
            "reason": "Do not play",
        },
    )
    assert (
        window.status_label.text()
        == "Video ban added."
    )


def test_change_selected_ban_states(
    qtbot,
    monkeypatch,
):
    window = ManagerWindow()
    qtbot.addWidget(window)

    calls = []

    class FakeClient:
        def set_creator_ban_active(
            self,
            ban_id,
            *,
            active,
            reason,
        ):
            calls.append(
                (
                    "creator",
                    ban_id,
                    active,
                    reason,
                )
            )
            return {
                "ban_id": ban_id,
                "active": active,
                "changed": True,
            }

        def set_video_ban_active(
            self,
            ban_id,
            *,
            active,
            reason,
        ):
            calls.append(
                (
                    "video",
                    ban_id,
                    active,
                    reason,
                )
            )
            return {
                "ban_id": ban_id,
                "active": active,
                "changed": True,
            }

        def creator_bans(
            self,
            *,
            include_inactive,
        ):
            return []

        def video_bans(
            self,
            *,
            include_inactive,
        ):
            return []

    window.bot_client = FakeClient()
    window._update_client = lambda: None

    window.ban_page.apply_bans(
        creators=[
            {
                "id": 12,
                "platform": "youtube",
                "video_channel": "Test Channel",
                "active": 1,
            }
        ],
        videos=[
            {
                "id": 21,
                "platform": "youtube",
                "video_platform_id": "video123",
                "active": 0,
            }
        ],
    )

    monkeypatch.setattr(
        "app.window.QInputDialog.getText",
        lambda *args: (
            "  Moderation decision  ",
            True,
        ),
    )

    window.ban_page.creator_table.selectRow(0)
    window.change_selected_creator_ban_state()

    assert calls[0] == (
        "creator",
        12,
        False,
        "Moderation decision",
    )
    assert (
        window.status_label.text()
        == "Creator unbanned."
    )

    window.ban_page.apply_bans(
        creators=[],
        videos=[
            {
                "id": 21,
                "platform": "youtube",
                "video_platform_id": "video123",
                "active": 0,
            }
        ],
    )
    window.ban_page.video_table.selectRow(0)
    window.change_selected_video_ban_state()

    assert calls[1] == (
        "video",
        21,
        True,
        "Moderation decision",
    )
    assert (
        window.status_label.text()
        == "Video re-banned."
    )


def test_show_ban_audit_dialogs(
    qtbot,
    monkeypatch,
):
    window = ManagerWindow()
    qtbot.addWidget(window)

    shown = []

    class FakeClient:
        def creator_ban_audit(self, ban_id):
            assert ban_id == 12
            return [
                {
                    "action": "banned",
                    "actor": "manager-steve",
                }
            ]

        def video_ban_audit(self, ban_id):
            assert ban_id == 21
            return [
                {
                    "action": "unbanned",
                    "actor": "manager-rose",
                }
            ]

    class FakeAuditDialog:
        def __init__(
            self,
            title,
            entries,
            parent,
        ):
            assert parent is window
            shown.append(
                (title, entries)
            )

        def exec(self):
            return 1

    monkeypatch.setattr(
        "app.window.AuditHistoryDialog",
        FakeAuditDialog,
    )

    window.bot_client = FakeClient()
    window._update_client = lambda: None

    window.ban_page.apply_bans(
        creators=[
            {
                "id": 12,
                "platform": "youtube",
                "video_channel": "Test Channel",
                "active": 1,
            }
        ],
        videos=[
            {
                "id": 21,
                "platform": "youtube",
                "video_platform_id": "video123",
                "active": 1,
            }
        ],
    )

    window.ban_page.creator_table.selectRow(0)
    window.show_creator_ban_audit()

    window.ban_page.video_table.selectRow(0)
    window.show_video_ban_audit()

    assert shown == [
        (
            "Creator Ban Audit",
            [
                {
                    "action": "banned",
                    "actor": "manager-steve",
                }
            ],
        ),
        (
            "Video Ban Audit",
            [
                {
                    "action": "unbanned",
                    "actor": "manager-rose",
                }
            ],
        ),
    ]
