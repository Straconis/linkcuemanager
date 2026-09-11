from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QPushButton

import app.pages.queue_page as queue_page_module
from app.pages.queue_page import QueueCard, QueuePage


def _noop():
    pass


def _build_page(
    drag_reorder_callback=_noop,
) -> QueuePage:
    app = QApplication.instance() or QApplication([])

    return QueuePage(
        refresh_callback=_noop,
        add_video_callback=_noop,
        refresh_metadata_callback=_noop,
        export_queue_callback=_noop,
        export_selected_callback=_noop,
        export_history_callback=_noop,
        import_queue_callback=_noop,
        move_to_beginning_callback=_noop,
        move_up_callback=_noop,
        move_down_callback=_noop,
        move_to_end_callback=_noop,
        move_to_position_callback=_noop,
        remove_callback=_noop,
        clear_queue_callback=_noop,
        drag_reorder_callback=drag_reorder_callback,
    )


def test_add_video_button_uses_primary_action_object_name():
    page = _build_page()

    assert page.add_video_button.objectName() == "addVideoButton"

def test_add_video_button_is_in_primary_action_stylesheet():
    import inspect

    from app.window import ManagerWindow

    source = inspect.getsource(ManagerWindow.set_dark_mode)

    assert "QPushButton#addVideoButton," in source
    assert "QPushButton#addVideoButton:hover," in source


def test_add_video_dialog_add_button_has_primary_action_object_name():
    from app.pages.add_video_dialog import AddVideoDialog

    dialog = AddVideoDialog()

    add_buttons = [
        button
        for button in dialog.findChildren(QPushButton)
        if button.text() == "Add"
    ]

    assert len(add_buttons) == 1
    assert add_buttons[0].objectName() == "addVideoDialogAddButton"


def test_dark_theme_styles_dialogs_and_combo_boxes():
    import inspect

    from app.window import ManagerWindow

    source = inspect.getsource(ManagerWindow.set_dark_mode)
    dark_source = source.split("else:", 1)[0]

    assert "QDialog," in dark_source
    assert "QMessageBox {" in dark_source
    assert "QComboBox {" in dark_source
    assert "QComboBox:focus {" in dark_source


def test_now_playing_queue_card_uses_np_position_badge():
    from PySide6.QtWidgets import QApplication

    from app.pages.queue_page import QueueCard

    app = QApplication.instance() or QApplication([])

    card = QueueCard(
        {
            "id": 20,
            "title": "Now Playing",
            "status": "playing",
            "position": None,
            "url": "https://youtu.be/example",
        },
        lambda: None,
    )

    assert card.position_label.text() == "NP"



def test_now_playing_context_menu_is_display_only():
    import inspect

    from app.pages.queue_page import QueuePage

    source = inspect.getsource(QueuePage._show_queue_context_menu)

    assert "is_queue_item = position is not None" in source
    assert "remove_action.setEnabled(is_queue_item)" in source
    assert "move_beginning_action.setEnabled(False)" in source
    assert "move_up_action.setEnabled(False)" in source
    assert "move_down_action.setEnabled(False)" in source
    assert "move_end_action.setEnabled(False)" in source


def test_render_items_preserves_selected_item_by_id():
    from PySide6.QtCore import Qt

    page = _build_page()

    original_items = [
        {
            "id": 10,
            "position": 1,
            "url": "https://youtu.be/first",
            "title": "First",
            "status": "queued",
        },
        {
            "id": 42,
            "position": 2,
            "url": "https://youtu.be/selected",
            "title": "Selected",
            "status": "queued",
        },
        {
            "id": 99,
            "position": 3,
            "url": "https://youtu.be/third",
            "title": "Third",
            "status": "queued",
        },
    ]

    page.render_items(original_items)
    page.queue_table.selectRow(1)

    reordered_items = [
        {
            "id": 42,
            "position": 1,
            "url": "https://youtu.be/selected",
            "title": "Selected",
            "status": "queued",
        },
        {
            "id": 10,
            "position": 2,
            "url": "https://youtu.be/first",
            "title": "First",
            "status": "queued",
        },
        {
            "id": 99,
            "position": 3,
            "url": "https://youtu.be/third",
            "title": "Third",
            "status": "queued",
        },
    ]

    page.render_items(reordered_items)

    selected_row = page.queue_table.currentRow()
    assert selected_row == 0

    selected_item = page.queue_table.item(
        selected_row,
        0,
    )
    assert (
        selected_item.data(Qt.ItemDataRole.UserRole)
        == 42
    )



def test_queue_context_menu_has_move_to_position_action():
    import inspect

    source = inspect.getsource(
        QueuePage._show_queue_context_menu
    )

    assert '"Move to Position..."' in source
    assert "move_to_position_callback()" in source



def test_render_items_updates_total_video_count():
    page = _build_page()

    page.render_items(
        [
            {
                "id": 10,
                "title": "Now Playing",
                "status": "playing",
                "position": None,
            },
            {
                "id": 11,
                "title": "Queued One",
                "status": "queued",
                "position": 1,
            },
            {
                "id": 12,
                "title": "Queued Two",
                "status": "queued",
                "position": 2,
            },
        ]
    )

    assert page.video_count_label.text() == "Videos: 3"



def test_queue_search_filters_local_snapshot():
    from PySide6.QtCore import Qt

    page = _build_page()

    items = [
        {
            "id": 1,
            "title": "Funny Cat Video",
            "video_channel": "Cat Channel",
            "platform": "youtube",
            "submitted_by": "Alice",
            "url": "https://youtu.be/cat123",
            "status": "queued",
            "position": 1,
        },
        {
            "id": 2,
            "title": "Speedrun Highlights",
            "video_channel": "Gaming Central",
            "platform": "tiktok",
            "submitted_by": "Bob",
            "url": "https://www.tiktok.com/@runner/video/123",
            "status": "queued",
            "position": 2,
        },
    ]

    page.render_items(items)
    page.apply_search("gaming")

    assert page.queue_table.rowCount() == 1

    visible_item = page.queue_table.item(0, 0)

    assert (
        visible_item.data(Qt.ItemDataRole.UserRole)
        == 2
    )

    assert page._queue_items == items



def test_queue_page_has_search_button():
    page = _build_page()

    assert page.search_button.text() == "Search"
    assert page.search_button.objectName() == "queueSearchButton"


def test_queue_page_exposes_search_dialog():
    page = _build_page()

    assert callable(page.show_search_dialog)



def test_queue_filters_apply_locally_to_snapshot():
    from PySide6.QtCore import Qt

    page = _build_page()

    items = [
        {
            "id": 1,
            "title": "YouTube Queued",
            "platform": "youtube",
            "status": "queued",
            "position": 1,
        },
        {
            "id": 2,
            "title": "TikTok Queued",
            "platform": "tiktok",
            "status": "queued",
            "position": 2,
        },
        {
            "id": 3,
            "title": "YouTube Playing",
            "platform": "youtube",
            "status": "playing",
            "position": None,
        },
    ]

    page.render_items(items)
    page.apply_filters(
        platform="youtube",
        status="queued",
    )

    assert page.queue_table.rowCount() == 1

    visible_item = page.queue_table.item(0, 0)

    assert (
        visible_item.data(Qt.ItemDataRole.UserRole)
        == 1
    )

    assert page._queue_items == items


def test_clearing_queue_filters_restores_local_snapshot():
    page = _build_page()

    items = [
        {
            "id": 1,
            "title": "YouTube",
            "platform": "youtube",
            "status": "queued",
            "position": 1,
        },
        {
            "id": 2,
            "title": "TikTok",
            "platform": "tiktok",
            "status": "queued",
            "position": 2,
        },
    ]

    page.render_items(items)

    page.apply_filters(platform="youtube")
    assert page.queue_table.rowCount() == 1

    page.apply_filters()
    assert page.queue_table.rowCount() == 2



def test_queue_page_has_filters_button():
    page = _build_page()

    assert page.filters_button.text() == "Filters"
    assert page.filters_button.objectName() == "queueFiltersButton"


def test_queue_page_exposes_filter_dialog():
    page = _build_page()

    assert callable(page.show_filter_dialog)



def test_queue_search_and_filters_compose():
    from PySide6.QtCore import Qt

    page = _build_page()

    items = [
        {
            "id": 1,
            "title": "Funny Cat Video",
            "platform": "youtube",
            "status": "queued",
            "position": 1,
        },
        {
            "id": 2,
            "title": "Funny Cat Clip",
            "platform": "tiktok",
            "status": "queued",
            "position": 2,
        },
        {
            "id": 3,
            "title": "Speedrun Highlights",
            "platform": "youtube",
            "status": "queued",
            "position": 3,
        },
    ]

    page.render_items(items)
    page.apply_search("cat")
    page.apply_filters(platform="youtube")

    assert page.queue_table.rowCount() == 1

    visible_item = page.queue_table.item(0, 0)

    assert (
        visible_item.data(Qt.ItemDataRole.UserRole)
        == 1
    )


def test_queue_local_view_survives_snapshot_refresh():
    from PySide6.QtCore import Qt

    page = _build_page()

    page.render_items(
        [
            {
                "id": 1,
                "title": "Cat Video",
                "platform": "youtube",
                "status": "queued",
                "position": 1,
            },
            {
                "id": 2,
                "title": "Dog Video",
                "platform": "youtube",
                "status": "queued",
                "position": 2,
            },
        ]
    )

    page.apply_search("cat")
    page.apply_filters(platform="youtube")

    page.render_items(
        [
            {
                "id": 1,
                "title": "Cat Video",
                "platform": "youtube",
                "status": "queued",
                "position": 1,
            },
            {
                "id": 2,
                "title": "Dog Video",
                "platform": "youtube",
                "status": "queued",
                "position": 2,
            },
            {
                "id": 3,
                "title": "Cat TikTok",
                "platform": "tiktok",
                "status": "queued",
                "position": 3,
            },
        ]
    )

    assert page.queue_table.rowCount() == 1

    visible_item = page.queue_table.item(0, 0)

    assert (
        visible_item.data(Qt.ItemDataRole.UserRole)
        == 1
    )



def test_queue_uses_extended_selection():
    from PySide6.QtWidgets import QAbstractItemView

    page = _build_page()

    assert (
        page.queue_table.selectionMode()
        == QAbstractItemView.SelectionMode.ExtendedSelection
    )


def test_queue_select_all_toggle_excludes_now_playing():
    page = _build_page()

    page.render_items(
        [
            {
                "id": 10,
                "title": "Now Playing",
                "status": "playing",
                "position": None,
            },
            {
                "id": 11,
                "title": "Queued One",
                "status": "queued",
                "position": 1,
            },
            {
                "id": 12,
                "title": "Queued Two",
                "status": "queued",
                "position": 2,
            },
        ]
    )

    assert page.select_all_button.text() == "Select All"

    page.toggle_select_all()

    selected_rows = {
        index.row()
        for index in page.queue_table.selectionModel().selectedRows()
    }

    assert selected_rows == {1, 2}
    assert page.select_all_button.text() == "Deselect All"

    page.toggle_select_all()

    assert (
        page.queue_table.selectionModel().selectedRows()
        == []
    )
    assert page.select_all_button.text() == "Select All"



def test_queue_has_import_export_button():
    page = _build_page()

    assert page.import_export_button.text() == "Import / Export"
    assert (
        page.import_export_button.objectName()
        == "queueImportExportButton"
    )


def test_queue_import_export_dialog_exposes_expected_actions():
    page = _build_page()

    assert page.import_queue_button.text() == "Import Queue"
    assert page.export_queue_button.text() == "Export Queue"
    assert (
        page.export_selected_button.text()
        == "Export Selected"
    )
    assert page.export_history_button.text() == "Export History"



def test_selected_queue_item_ids_excludes_now_playing():
    page = _build_page()

    page.render_items([
        {
            "id": 10,
            "title": "Now Playing",
            "status": "playing",
            "position": None,
        },
        {
            "id": 11,
            "title": "Queued One",
            "status": "queued",
            "position": 1,
        },
        {
            "id": 12,
            "title": "Queued Two",
            "status": "queued",
            "position": 2,
        },
    ])

    page.queue_table.selectAll()

    assert page.selected_queue_item_ids() == [11, 12]



def test_queue_page_defaults_to_queue_mode():
    page = _build_page()

    assert page.view_mode == "queue"
    assert page.view_toggle_button.text() == "View History"


def test_history_mode_is_read_only():
    page = _build_page()

    page.set_view_mode("history")

    assert page.view_mode == "history"
    assert page.view_toggle_button.text() == "View Queue"
    assert page.add_video_button.isEnabled() is False
    assert page.select_all_button.isEnabled() is False
    assert page.move_to_beginning_button.isEnabled() is False
    assert page.move_up_button.isEnabled() is False
    assert page.move_down_button.isEnabled() is False
    assert page.move_to_end_button.isEnabled() is False
    assert page.remove_selected_button.isEnabled() is False
    assert page.clear_queue_button.isEnabled() is False
    assert page.refresh_metadata_button.isEnabled() is False


def test_returning_to_queue_mode_restores_queue_controls():
    page = _build_page()

    page.set_view_mode("history")
    page.set_view_mode("queue")

    assert page.view_mode == "queue"
    assert page.view_toggle_button.text() == "View History"
    assert page.add_video_button.isEnabled() is True
    assert page.select_all_button.isEnabled() is True
    assert page.move_to_beginning_button.isEnabled() is True
    assert page.remove_selected_button.isEnabled() is True
    assert page.clear_queue_button.isEnabled() is True
    assert page.refresh_metadata_button.isEnabled() is True


def test_clear_queue_action_has_explicit_label():
    page = _build_page()

    assert (
        page.clear_queue_button.text()
        == "Clear Queue"
    )



def test_search_button_changes_to_clear_search_when_active():
    page = _build_page()

    page.render_items(
        [
            {
                "id": 1,
                "position": 1,
                "title": "Alpha Video",
                "status": "queued",
            },
            {
                "id": 2,
                "position": 2,
                "title": "Beta Video",
                "status": "queued",
            },
        ]
    )

    page.apply_search("Alpha")

    assert page.search_button.text() == "Clear Search"
    assert page.queue_table.rowCount() == 1


def test_clear_search_button_restores_full_view():
    page = _build_page()

    page.render_items(
        [
            {
                "id": 1,
                "position": 1,
                "title": "Alpha Video",
                "status": "queued",
            },
            {
                "id": 2,
                "position": 2,
                "title": "Beta Video",
                "status": "queued",
            },
        ]
    )

    page.apply_search("Alpha")

    assert page.queue_table.rowCount() == 1

    page.show_search_dialog()

    assert page._search_query == ""
    assert page.search_button.text() == "Search"
    assert page.queue_table.rowCount() == 2


def test_clear_search_preserves_filters():
    page = _build_page()

    page.render_items(
        [
            {
                "id": 1,
                "position": 1,
                "title": "Alpha",
                "platform": "youtube",
                "status": "queued",
            },
            {
                "id": 2,
                "position": 2,
                "title": "Beta",
                "platform": "tiktok",
                "status": "queued",
            },
        ]
    )

    page.apply_filters(platform="youtube")
    page.apply_search("Alpha")
    page.show_search_dialog()

    assert page._search_query == ""
    assert page._filter_platform == "youtube"
    assert page.queue_table.rowCount() == 1


def test_local_sort_changes_display_without_reordering_bot_items():
    page = _build_page()

    items = [
        {
            "id": 1,
            "position": 1,
            "title": "Beta",
            "status": "queued",
        },
        {
            "id": 2,
            "position": 2,
            "title": "Alpha",
            "status": "queued",
        },
        {
            "id": 3,
            "position": 3,
            "title": "Charlie",
            "status": "queued",
        },
    ]

    page.render_items(items)

    assert [
        item["id"]
        for item in page._queue_items
    ] == [1, 2, 3]

    page.apply_sort(
        sort_by="title",
        descending=False,
    )

    assert [
        page.queue_table.item(row, 0).data(
            Qt.ItemDataRole.UserRole
        )
        for row in range(page.queue_table.rowCount())
    ] == [2, 1, 3]

    assert [
        item["id"]
        for item in page._queue_items
    ] == [1, 2, 3]

    assert page.sort_button.text() == "Sort (Active)"

    page.apply_sort(
        sort_by="title",
        descending=True,
    )

    assert [
        page.queue_table.item(row, 0).data(
            Qt.ItemDataRole.UserRole
        )
        for row in range(page.queue_table.rowCount())
    ] == [3, 1, 2]

    assert [
        item["id"]
        for item in page._queue_items
    ] == [1, 2, 3]

    page.apply_sort()

    assert [
        page.queue_table.item(row, 0).data(
            Qt.ItemDataRole.UserRole
        )
        for row in range(page.queue_table.rowCount())
    ] == [1, 2, 3]

    assert page.sort_button.text() == "Sort"


def test_local_sort_applies_after_filters():
    page = _build_page()

    page.render_items(
        [
            {
                "id": 1,
                "position": 1,
                "title": "Beta",
                "platform": "youtube",
                "status": "queued",
            },
            {
                "id": 2,
                "position": 2,
                "title": "Alpha",
                "platform": "tiktok",
                "status": "queued",
            },
            {
                "id": 3,
                "position": 3,
                "title": "Alpha",
                "platform": "youtube",
                "status": "queued",
            },
        ]
    )

    page.apply_filters(platform="youtube")
    page.apply_sort(
        sort_by="title",
        descending=False,
    )

    assert page.queue_table.rowCount() == 2

    assert [
        page.queue_table.item(row, 0).data(
            Qt.ItemDataRole.UserRole
        )
        for row in range(page.queue_table.rowCount())
    ] == [3, 1]

    assert [
        item["id"]
        for item in page._queue_items
    ] == [1, 2, 3]



def test_queue_card_copy_link_writes_url_to_clipboard(
    monkeypatch,
):
    app = QApplication.instance() or QApplication([])

    card = QueueCard(
        {
            "id": 1,
            "title": "Example Video",
            "status": "queued",
            "url": "https://youtu.be/example",
        },
        lambda: None,
    )

    class FakeMenu:
        def __init__(self, parent):
            self.action = object()

        def addAction(self, text):
            assert text == "Copy Link"
            return self.action

        def exec(self, position):
            return self.action

    monkeypatch.setattr(
        queue_page_module,
        "QMenu",
        FakeMenu,
    )

    clipboard = QApplication.clipboard()
    clipboard.clear()

    card._show_url_context_menu(
        card.url_label.rect().center(),
        "https://youtu.be/example",
    )

    assert clipboard.text() == "https://youtu.be/example"


def test_queue_filter_button_shows_active_count():
    page = _build_page()

    assert page.filters_button.text() == "Filters"

    page.apply_filters(platform="youtube")

    assert page.filters_button.text() == "Filters (1)"

    page.apply_filters(
        platform="youtube",
        status="queued",
        submitter="Alice",
        submission_source="manager",
    )

    assert page.filters_button.text() == "Filters (4)"
    assert "Platform: Youtube" in (
        page.filters_button.toolTip()
    )
    assert "Status: Queued" in (
        page.filters_button.toolTip()
    )
    assert "Submitted by: alice" in (
        page.filters_button.toolTip()
    )
    assert "Source: Manager" in (
        page.filters_button.toolTip()
    )

    page.apply_filters()

    assert page.filters_button.text() == "Filters"
    assert (
        page.filters_button.toolTip()
        == "Filter the current view"
    )


def test_queue_filters_by_submitter_and_source():
    from PySide6.QtCore import Qt

    page = _build_page()
    page.render_items(
        [
            {
                "id": 1,
                "position": 1,
                "title": "Manager submission",
                "submitted_by": "Alice",
                "submission_source": "manager",
                "status": "queued",
            },
            {
                "id": 2,
                "position": 2,
                "title": "Chat submission",
                "submitted_by": "Bob",
                "submission_source": "chat",
                "status": "queued",
            },
            {
                "id": 3,
                "position": 3,
                "title": "Player submission",
                "submitted_by": "Alice",
                "submission_source": "player",
                "status": "queued",
            },
        ]
    )

    page.apply_filters(
        submitter="alice",
        submission_source="player",
    )

    assert page.queue_table.rowCount() == 1
    assert (
        page.queue_table.item(0, 0).data(
            Qt.ItemDataRole.UserRole
        )
        == 3
    )


def test_chat_source_filter_accepts_twitch_alias():
    from PySide6.QtCore import Qt

    page = _build_page()
    page.render_items(
        [
            {
                "id": 1,
                "position": 1,
                "submitted_by": "Alice",
                "submission_source": "twitch",
                "status": "queued",
            },
            {
                "id": 2,
                "position": 2,
                "submitted_by": "Bob",
                "submission_source": "manager",
                "status": "queued",
            },
        ]
    )

    page.apply_filters(
        submission_source="chat"
    )

    assert page.queue_table.rowCount() == 1
    assert (
        page.queue_table.item(0, 0).data(
            Qt.ItemDataRole.UserRole
        )
        == 1
    )


def test_queue_filter_dialog_preserves_all_filters(
    monkeypatch,
):
    from PySide6.QtWidgets import (
        QComboBox,
        QDialog,
    )

    page = _build_page()
    page.render_items(
        [
            {
                "id": 1,
                "position": 1,
                "platform": "youtube",
                "status": "queued",
                "submitted_by": "Alice",
                "submission_source": "manager",
            },
        ]
    )

    page.apply_filters(
        platform="youtube",
        status="queued",
        submitter="alice",
        submission_source="manager",
    )

    inspected = []

    def fake_exec(dialog):
        combos = {
            combo.objectName(): combo
            for combo in dialog.findChildren(
                QComboBox
            )
        }

        assert (
            combos["queuePlatformFilter"].currentData()
            == "youtube"
        )
        assert (
            combos["queueStatusFilter"].currentData()
            == "queued"
        )
        assert (
            combos["queueSubmitterFilter"].currentData()
            == "alice"
        )
        assert (
            combos[
                "queueSubmissionSourceFilter"
            ].currentData()
            == "manager"
        )

        inspected.append(dialog.windowTitle())

        return QDialog.DialogCode.Rejected

    monkeypatch.setattr(
        "app.pages.queue_page.QDialog.exec",
        fake_exec,
    )

    page.show_filter_dialog()

    assert inspected == ["Queue Filters"]


def test_queue_filter_dialog_applies_all_values(
    monkeypatch,
):
    from PySide6.QtWidgets import (
        QComboBox,
        QDialog,
        QPushButton,
    )

    page = _build_page()
    page.render_items(
        [
            {
                "id": 1,
                "position": 1,
                "title": "Manager item",
                "platform": "youtube",
                "status": "queued",
                "submitted_by": "Alice",
                "submission_source": "manager",
            },
            {
                "id": 2,
                "position": 2,
                "title": "Chat item",
                "platform": "tiktok",
                "status": "played",
                "submitted_by": "Bob",
                "submission_source": "twitch",
            },
        ]
    )

    def fake_exec(dialog):
        combos = {
            combo.objectName(): combo
            for combo in dialog.findChildren(
                QComboBox
            )
        }
        buttons = {
            button.text(): button
            for button in dialog.findChildren(
                QPushButton
            )
        }

        selections = {
            "queuePlatformFilter": "tiktok",
            "queueStatusFilter": "played",
            "queueSubmitterFilter": "bob",
            "queueSubmissionSourceFilter": "chat",
        }

        for object_name, value in selections.items():
            combo = combos[object_name]
            combo.setCurrentIndex(
                combo.findData(value)
            )

        buttons["Apply"].click()

        return QDialog.DialogCode.Accepted

    monkeypatch.setattr(
        "app.pages.queue_page.QDialog.exec",
        fake_exec,
    )

    page.show_filter_dialog()

    assert page._filter_platform == "tiktok"
    assert page._filter_status == "played"
    assert page._filter_submitter == "bob"
    assert (
        page._filter_submission_source
        == "chat"
    )
    assert page.filters_button.text() == "Filters (4)"
    assert page.queue_table.rowCount() == 1


def test_history_filter_dialog_uses_history_title(
    monkeypatch,
):
    from PySide6.QtWidgets import QDialog

    page = _build_page()
    page.set_view_mode("history")

    titles = []

    def fake_exec(dialog):
        titles.append(dialog.windowTitle())

        return QDialog.DialogCode.Rejected

    monkeypatch.setattr(
        "app.pages.queue_page.QDialog.exec",
        fake_exec,
    )

    page.show_filter_dialog()

    assert titles == ["History Filters"]


def test_local_sort_by_video_length():
    from PySide6.QtCore import Qt

    page = _build_page()
    page.render_items(
        [
            {
                "id": 1,
                "position": 1,
                "title": "Two minutes",
                "duration": 120,
                "status": "queued",
            },
            {
                "id": 2,
                "position": 2,
                "title": "Nine seconds",
                "duration": 9,
                "status": "queued",
            },
            {
                "id": 3,
                "position": 3,
                "title": "Unknown duration",
                "duration": None,
                "status": "queued",
            },
            {
                "id": 4,
                "position": 4,
                "title": "One minute",
                "duration": "60",
                "status": "queued",
            },
        ]
    )

    page.apply_sort(
        sort_by="duration",
        descending=False,
    )

    assert [
        page.queue_table.item(row, 0).data(
            Qt.ItemDataRole.UserRole
        )
        for row in range(
            page.queue_table.rowCount()
        )
    ] == [2, 4, 1, 3]

    page.apply_sort(
        sort_by="duration",
        descending=True,
    )

    assert [
        page.queue_table.item(row, 0).data(
            Qt.ItemDataRole.UserRole
        )
        for row in range(
            page.queue_table.rowCount()
        )
    ] == [1, 4, 2, 3]


def test_sort_dialog_has_video_length_option(
    monkeypatch,
):
    from PySide6.QtWidgets import (
        QComboBox,
        QDialog,
    )

    page = _build_page()
    inspected = []

    def fake_exec(dialog):
        combo_values = [
            [
                combo.itemData(index)
                for index in range(
                    combo.count()
                )
            ]
            for combo in dialog.findChildren(
                QComboBox
            )
        ]

        assert any(
            "duration" in values
            for values in combo_values
        )

        inspected.append(dialog.windowTitle())

        return QDialog.DialogCode.Rejected

    monkeypatch.setattr(
        "app.pages.queue_page.QDialog.exec",
        fake_exec,
    )

    page.show_sort_dialog()

    assert inspected == ["Queue Sort"]


def test_queue_status_area_displays_view_state():
    page = _build_page()

    assert (
        page.queue_status_area.objectName()
        == "queueStatusArea"
    )
    assert page.video_count_label.text() == "Videos: 0"
    assert (
        page.filter_status_label.text()
        == "Filters: None"
    )
    assert (
        page.sort_status_label.text()
        == "Sort: Queue Order"
    )

    page.render_items(
        [
            {
                "id": 1,
                "position": 1,
                "title": "Short",
                "duration": 30,
                "platform": "youtube",
                "status": "queued",
                "submitted_by": "Alice",
                "submission_source": "manager",
            },
            {
                "id": 2,
                "position": 2,
                "title": "Long",
                "duration": 120,
                "platform": "tiktok",
                "status": "queued",
                "submitted_by": "Bob",
                "submission_source": "chat",
            },
        ]
    )

    assert page.video_count_label.text() == "Videos: 2"

    page.apply_filters(
        platform="youtube",
        submitter="alice",
    )

    assert page.video_count_label.text() == "Videos: 1"
    assert (
        page.filter_status_label.text()
        == (
            "Filters: Platform: Youtube; "
            "Submitted by: alice"
        )
    )

    page.apply_sort(
        sort_by="duration",
        descending=True,
    )

    assert (
        page.sort_status_label.text()
        == "Sort: Video Length (Descending)"
    )

    page.apply_filters()
    page.apply_sort()

    assert (
        page.filter_status_label.text()
        == "Filters: None"
    )
    assert (
        page.sort_status_label.text()
        == "Sort: Queue Order"
    )


def test_queue_status_area_contains_presence_counts():
    page = _build_page()

    status_layout = page.queue_status_area.layout()

    player_index = status_layout.indexOf(
        page.player_count_label
    )
    manager_index = status_layout.indexOf(
        page.manager_count_label
    )

    assert player_index >= 0
    assert manager_index > player_index
    assert (
        page.player_count_label.text()
        == "Players Connected: 0"
    )
    assert (
        page.manager_count_label.text()
        == (
            "Managers Connected: 0 "
            "(including this instance)"
        )
    )


def test_drag_reorder_toggle_and_dispatch():
    from PySide6.QtWidgets import QAbstractItemView

    moves = []
    page = _build_page(
        lambda item_id, position:
        moves.append((item_id, position))
    )

    page.render_items(
        [
            {
                "id": 90,
                "position": None,
                "status": "playing",
                "title": "Now Playing",
            },
            {
                "id": 1,
                "position": 1,
                "status": "queued",
                "title": "One",
            },
            {
                "id": 2,
                "position": 2,
                "status": "queued",
                "title": "Two",
            },
            {
                "id": 3,
                "position": 3,
                "status": "queued",
                "title": "Three",
            },
        ]
    )

    assert (
        page.drag_reorder_button.text()
        == "Drag Reorder: Off"
    )

    page.drag_reorder_button.click()

    assert page._drag_reorder_enabled is True
    assert (
        page.drag_reorder_button.text()
        == "Drag Reorder: On"
    )
    assert (
        page.queue_table.dragDropMode()
        == QAbstractItemView.DragDropMode.InternalMove
    )

    assert (
        page.queue_table.request_reorder(
            1,
            3,
        )
        is True
    )
    assert moves == [(1, 3)]

    assert (
        page.queue_table.request_reorder(
            0,
            1,
        )
        is False
    )

    page.drag_reorder_button.click()

    assert page._drag_reorder_enabled is False
    assert (
        page.queue_table.dragDropMode()
        == QAbstractItemView.DragDropMode.NoDragDrop
    )


def test_drag_reorder_requires_canonical_queue_view(
    monkeypatch,
):
    page = _build_page()
    messages = []

    monkeypatch.setattr(
        "app.pages.queue_page.QMessageBox.information",
        lambda parent, title, message:
        messages.append((title, message)),
    )

    page.apply_sort(
        sort_by="duration",
        descending=True,
    )
    page.drag_reorder_button.click()

    assert page._drag_reorder_enabled is False
    assert page.drag_reorder_button.isChecked() is False
    assert messages
    assert messages[0][0] == "Drag Reorder Unavailable"
    assert "clear search" in messages[0][1].lower()


def test_transforming_view_disables_drag_reorder():
    page = _build_page()

    page.drag_reorder_button.click()
    assert page._drag_reorder_enabled is True

    page.apply_filters(platform="youtube")

    assert page._drag_reorder_enabled is False
    assert page.drag_reorder_button.isChecked() is False
    assert (
        page.drag_reorder_button.text()
        == "Drag Reorder: Off"
    )


def test_optimistic_drag_reorder_updates_immediately():
    page = _build_page()

    page.render_items(
        [
            {
                "id": 90,
                "position": None,
                "status": "playing",
            },
            {
                "id": 1,
                "position": 1,
                "status": "queued",
            },
            {
                "id": 2,
                "position": 2,
                "status": "queued",
            },
            {
                "id": 3,
                "position": 3,
                "status": "queued",
            },
        ]
    )

    assert page.optimistically_reorder_item(1, 3) is True

    assert [
        page.queue_table.item(row, 0).data(
            Qt.ItemDataRole.UserRole
        )
        for row in range(page.queue_table.rowCount())
    ] == [90, 2, 3, 1]

    assert [
        item.get("position")
        for item in page._queue_items
    ] == [None, 1, 2, 3]


def test_drag_reorder_busy_state_preserves_toggle():
    page = _build_page()

    page.drag_reorder_button.click()
    assert page._drag_reorder_enabled is True

    page.set_drag_reorder_busy(True)

    assert page.drag_reorder_button.isEnabled() is False
    assert (
        page.drag_reorder_button.text()
        == "Drag Reorder: Saving..."
    )

    page.set_drag_reorder_busy(False)

    assert page.drag_reorder_button.isEnabled() is True
    assert (
        page.drag_reorder_button.text()
        == "Drag Reorder: On"
    )
