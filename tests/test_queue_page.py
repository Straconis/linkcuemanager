from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QPushButton

import app.pages.queue_page as queue_page_module
from app.pages.queue_page import QueueCard, QueuePage


def _noop():
    pass


def _build_page() -> QueuePage:
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
