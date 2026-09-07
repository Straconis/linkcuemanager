from app.pages.software_page import SoftwarePage


def _cell_text(table, row, column):
    item = table.item(row, column)
    assert item is not None
    return item.text()


def test_software_page_starts_unchecked(qtbot):
    page = SoftwarePage(lambda: None)
    qtbot.addWidget(page)

    assert page.refresh_button.text() == "Refresh Software"
    assert page.bot_status_label.text() == "Not checked"
    assert page.bot_version_label.text() == "Unknown"
    assert page.bot_api_version_label.text() == "Unknown"
    assert page.manager_table.rowCount() == 0
    assert page.player_table.rowCount() == 0


def test_software_page_displays_bot_and_connected_clients(qtbot):
    page = SoftwarePage(lambda: None)
    qtbot.addWidget(page)

    page.apply_status(
        {
            "bot": {
                "status": "online",
                "version": "0.3.0",
                "api_version": "0.2",
            },
            "managers": [
                {
                    "display_name": "Rose",
                    "version": "0.2.0",
                    "client_id": "manager-rose",
                },
                {
                    "display_name": "Steve",
                    "version": "0.3.0",
                    "client_id": "manager-steve",
                },
            ],
            "players": [
                {
                    "display_name": "SmokeEEG",
                    "version": "0.4.0",
                    "client_id": "player-stream",
                }
            ],
        },
        {
            "state": "playing",
            "item": {
                "title": "Test Video",
            },
        },
    )

    assert page.bot_status_label.text() == "Online"
    assert page.bot_version_label.text() == "0.3.0"
    assert page.bot_api_version_label.text() == "0.2"

    assert page.manager_table.rowCount() == 2
    assert _cell_text(page.manager_table, 0, 0) == "Rose"
    assert _cell_text(page.manager_table, 0, 1) == "0.2.0"
    assert _cell_text(page.manager_table, 0, 2) == "manager-rose"
    assert _cell_text(page.manager_table, 1, 0) == "Steve"

    assert page.player_table.rowCount() == 1
    assert _cell_text(page.player_table, 0, 0) == "SmokeEEG"
    assert _cell_text(page.player_table, 0, 1) == "0.4.0"
    assert _cell_text(page.player_table, 0, 2) == "player-stream"
    assert _cell_text(page.player_table, 0, 3) == "Playing"
    assert _cell_text(page.player_table, 0, 4) == "Test Video"


def test_software_page_handles_offline_bot(qtbot):
    page = SoftwarePage(lambda: None)
    qtbot.addWidget(page)

    page.show_unavailable()

    assert page.bot_status_label.text() == "Offline"
    assert page.bot_version_label.text() == "Unknown"
    assert page.bot_api_version_label.text() == "Unknown"
    assert page.manager_table.rowCount() == 0
    assert page.player_table.rowCount() == 0
