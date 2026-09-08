from PySide6.QtCore import Qt

from app.pages.ban_management_page import (
    BanManagementPage,
)


def _cell_text(table, row, column):
    item = table.item(row, column)
    assert item is not None
    return item.text()


def test_ban_management_page_starts_empty(qtbot):
    calls = []

    page = BanManagementPage(
        lambda: calls.append("refresh"),
        lambda: calls.append("add_creator"),
        lambda: calls.append("creator_state"),
        lambda: calls.append("creator_audit"),
        lambda: calls.append("add_video"),
        lambda: calls.append("video_state"),
        lambda: calls.append("video_audit"),
    )
    qtbot.addWidget(page)

    assert page.refresh_button.text() == "Refresh Bans"
    assert page.full_history_label.text() == (
        "Show Full Ban History:"
    )
    assert page.include_inactive_toggle.isChecked() is True
    assert (
        page.include_inactive_toggle.accessibleName()
        == "Show Full Ban History"
    )

    assert page.tabs.tabText(0) == "Creators / Channels"
    assert page.tabs.tabText(1) == "Individual Videos"

    assert page.creator_table.rowCount() == 0
    assert page.video_table.rowCount() == 0

    assert page.add_creator_button.text() == "Add Creator Ban"
    assert page.creator_state_button.text() == "Unban Selected"
    assert page.creator_audit_button.text() == "Audit History"

    assert page.add_video_button.text() == "Add Video Ban"
    assert page.video_state_button.text() == "Unban Selected"
    assert page.video_audit_button.text() == "Audit History"

    page.refresh_button.click()
    page.add_creator_button.click()
    page.add_video_button.click()

    assert calls == [
        "refresh",
        "add_creator",
        "add_video",
    ]


def test_ban_management_page_displays_creator_bans(qtbot):
    page = BanManagementPage(
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
    )
    qtbot.addWidget(page)

    page.apply_bans(
        creators=[
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
            },
            {
                "id": 13,
                "platform": "tiktok",
                "video_channel": "Old Channel",
                "video_creator_id": None,
                "reason": "Appeal accepted",
                "created_by": "manager-rose",
                "active": 0,
                "created_at": "2026-09-06 18:00:00",
                "updated_at": "2026-09-07 19:00:00",
            },
        ],
        videos=[],
    )

    assert page.creator_table.rowCount() == 2
    assert _cell_text(page.creator_table, 0, 0) == "YouTube"
    assert _cell_text(page.creator_table, 0, 1) == "Test Channel"
    assert _cell_text(page.creator_table, 0, 2) == "UC_TEST"
    assert _cell_text(page.creator_table, 0, 3) == "Repeated submissions"
    assert _cell_text(page.creator_table, 0, 4) == "manager-steve"
    assert _cell_text(page.creator_table, 0, 5) == "Active"

    assert _cell_text(page.creator_table, 1, 2) == "Unknown"
    assert _cell_text(page.creator_table, 1, 5) == "Inactive"

    page.creator_table.selectRow(0)

    item = page.creator_table.item(0, 0)
    assert item.data(Qt.ItemDataRole.UserRole) == 12
    assert item.data(Qt.ItemDataRole.UserRole + 1) is True
    assert page.selected_creator_ban() == (12, True)
    assert page.creator_state_button.text() == "Unban Selected"

    page.creator_table.selectRow(1)

    assert page.selected_creator_ban() == (13, False)
    assert page.creator_state_button.text() == "Re-ban Selected"


def test_ban_management_page_displays_video_bans(qtbot):
    page = BanManagementPage(
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
    )
    qtbot.addWidget(page)

    page.apply_bans(
        creators=[],
        videos=[
            {
                "id": 21,
                "platform": "youtube",
                "title": "Blocked Video",
                "video_platform_id": "video123",
                "url": "https://youtu.be/video123",
                "reason": "Do not play",
                "created_by": "manager-steve",
                "active": 1,
                "created_at": "2026-09-07 20:00:00",
                "updated_at": "2026-09-07 20:00:00",
            },
            {
                "id": 22,
                "platform": "tiktok",
                "title": None,
                "video_platform_id": "clip456",
                "url": None,
                "reason": None,
                "created_by": "manager-rose",
                "active": 0,
                "created_at": "2026-09-06 18:00:00",
                "updated_at": "2026-09-07 19:00:00",
            },
        ],
    )

    assert page.video_table.rowCount() == 2
    assert _cell_text(page.video_table, 0, 0) == "YouTube"
    assert _cell_text(page.video_table, 0, 1) == "Blocked Video"
    assert _cell_text(page.video_table, 0, 2) == "video123"
    assert _cell_text(page.video_table, 0, 3) == (
        "https://youtu.be/video123"
    )
    assert _cell_text(page.video_table, 0, 4) == "Do not play"
    assert _cell_text(page.video_table, 0, 5) == "manager-steve"
    assert _cell_text(page.video_table, 0, 6) == "Active"

    assert _cell_text(page.video_table, 1, 1) == "Unknown"
    assert _cell_text(page.video_table, 1, 3) == "Unknown"
    assert _cell_text(page.video_table, 1, 4) == "None"
    assert _cell_text(page.video_table, 1, 6) == "Inactive"

    page.video_table.selectRow(0)

    item = page.video_table.item(0, 0)
    assert item.data(Qt.ItemDataRole.UserRole) == 21
    assert item.data(Qt.ItemDataRole.UserRole + 1) is True
    assert page.selected_video_ban() == (21, True)
    assert page.video_state_button.text() == "Unban Selected"

    page.video_table.selectRow(1)

    assert page.selected_video_ban() == (22, False)
    assert page.video_state_button.text() == "Re-ban Selected"
