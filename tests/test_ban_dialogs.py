from app.pages.ban_dialogs import (
    AuditHistoryDialog,
    CreatorBanDialog,
    VideoBanDialog,
)


def _cell_text(table, row, column):
    item = table.item(row, column)
    assert item is not None
    return item.text()


def test_creator_ban_dialog_values(qtbot):
    dialog = CreatorBanDialog()
    qtbot.addWidget(dialog)

    assert dialog.windowTitle() == "Add Creator Ban"
    assert dialog.platform_input.currentData() == "youtube"
    assert dialog.add_button.text() == "Add Ban"
    assert dialog.cancel_button.text() == "Cancel"

    dialog.platform_input.setCurrentIndex(1)
    dialog.channel_input.setText("  Test Channel  ")
    dialog.creator_id_input.setText("  UC_TEST  ")
    dialog.reason_input.setText("  Repeated submissions  ")

    assert dialog.values() == {
        "platform": "tiktok",
        "video_channel": "Test Channel",
        "video_creator_id": "UC_TEST",
        "reason": "Repeated submissions",
    }


def test_creator_ban_dialog_allows_optional_values(qtbot):
    dialog = CreatorBanDialog()
    qtbot.addWidget(dialog)

    dialog.channel_input.setText("Channel")

    assert dialog.values() == {
        "platform": "youtube",
        "video_channel": "Channel",
        "video_creator_id": None,
        "reason": None,
    }


def test_video_ban_dialog_values(qtbot):
    dialog = VideoBanDialog()
    qtbot.addWidget(dialog)

    assert dialog.windowTitle() == "Add Video Ban"
    assert dialog.platform_input.currentData() == "youtube"
    assert dialog.add_button.text() == "Add Ban"
    assert dialog.cancel_button.text() == "Cancel"

    dialog.platform_input.setCurrentIndex(1)
    dialog.video_id_input.setText("  clip123  ")
    dialog.title_input.setText("  Blocked Video  ")
    dialog.url_input.setText(
        "  https://tiktok.com/example  "
    )
    dialog.reason_input.setText("  Do not play  ")

    assert dialog.values() == {
        "platform": "tiktok",
        "video_platform_id": "clip123",
        "title": "Blocked Video",
        "url": "https://tiktok.com/example",
        "reason": "Do not play",
    }


def test_video_ban_dialog_allows_optional_values(qtbot):
    dialog = VideoBanDialog()
    qtbot.addWidget(dialog)

    dialog.video_id_input.setText("video123")

    assert dialog.values() == {
        "platform": "youtube",
        "video_platform_id": "video123",
        "title": None,
        "url": None,
        "reason": None,
    }


def test_audit_history_dialog_displays_entries(qtbot):
    dialog = AuditHistoryDialog(
        "Creator Ban Audit",
        [
            {
                "action": "banned",
                "actor": "manager-steve",
                "reason": "Repeated submissions",
                "created_at": "2026-09-07 20:00:00",
            },
            {
                "action": "unbanned",
                "actor": "manager-rose",
                "reason": None,
                "created_at": "2026-09-07 21:00:00",
            },
        ],
    )
    qtbot.addWidget(dialog)

    assert dialog.windowTitle() == "Creator Ban Audit"
    assert dialog.audit_table.rowCount() == 2

    assert _cell_text(dialog.audit_table, 0, 0) == "Banned"
    assert _cell_text(dialog.audit_table, 0, 1) == "manager-steve"
    assert _cell_text(dialog.audit_table, 0, 2) == (
        "Repeated submissions"
    )
    assert _cell_text(dialog.audit_table, 0, 3) == (
        "2026-09-07 20:00:00"
    )

    assert _cell_text(dialog.audit_table, 1, 0) == "Unbanned"
    assert _cell_text(dialog.audit_table, 1, 2) == "None"
    assert dialog.close_button.text() == "Close"
