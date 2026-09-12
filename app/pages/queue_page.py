from collections.abc import Callable

from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtNetwork import (
    QNetworkAccessManager,
    QNetworkReply,
    QNetworkRequest,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


def _format_duration(value) -> str:
    if value in (None, "", 0):
        return "Duration unknown"

    if isinstance(value, str):
        stripped = value.strip()

        if not stripped:
            return "Duration unknown"

        if ":" in stripped:
            return stripped

        try:
            value = float(stripped)
        except ValueError:
            return stripped

    try:
        total_seconds = int(float(value))
    except (TypeError, ValueError):
        return str(value)

    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"

    return f"{minutes}:{seconds:02d}"


def _format_queue_time(value) -> str:
    if value in (None, ""):
        return "--:--:--"

    text = str(value).strip()

    if not text:
        return "--:--:--"

    try:
        from datetime import datetime, timezone

        normalized = text.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)

        # SQLite CURRENT_TIMESTAMP is UTC but timezone-naive.
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        local_time = parsed.astimezone()

        return local_time.strftime("%H:%M:%S")
    except (TypeError, ValueError):
        return text

class QueueCard(QFrame):
    def __init__(
        self,
        item: dict,
        select_callback: Callable[[], None],
        parent: QWidget | None = None,
        drag_callback: Callable[[], None] | None = None,
    ):
        super().__init__(parent)

        self._select_callback = select_callback
        self._drag_callback = drag_callback
        self._drag_start_position = None

        self.setObjectName("queueCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.setMinimumHeight(112)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 10, 8)
        layout.setSpacing(12)

        position = item.get("position")

        self.media_container = QWidget()
        self.media_container.setObjectName("queueMediaContainer")

        # Preferred layout:
        # [38px queue badge] [12px gap] [128px thumbnail]
        #
        # Under horizontal pressure the thumbnail slides left under
        # the badge, reducing the media footprint from 178px to 128px.
        self.media_container.setFixedSize(178, 72)

        self.thumbnail_label = QLabel(
            "No\nThumbnail",
            self.media_container,
        )
        self.thumbnail_label.setObjectName("queueThumbnail")
        self.thumbnail_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.thumbnail_label.setGeometry(50, 0, 128, 72)
        self.thumbnail_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True,
        )

        badge_text = "NP" if item.get("status") == "playing" else ("" if position is None else str(position))
        self.position_label = QLabel(
            badge_text,
            self.media_container,
        )
        self.position_label.setObjectName("queuePositionBadge")
        self.position_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.position_label.setFixedSize(38, 38)
        self.position_label.move(0, 17)
        self.position_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True,
        )
        self.position_label.raise_()

        layout.addWidget(
            self.media_container,
            0,
            Qt.AlignmentFlag.AlignVCenter,
        )

        title = item.get("title") or item.get("url") or "Untitled"
        channel = (
            item.get("video_channel")
            or item.get("channel")
            or "Unknown channel"
        )
        platform = item.get("platform") or "Unknown platform"
        duration = _format_duration(item.get("duration"))
        submitted_by = item.get("submitted_by") or "Unknown"
        status = item.get("status") or "Unknown"
        created_at = _format_queue_time(item.get("created_at"))
        url = item.get("url") or ""

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("queueCardTitle")
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet(
            "font-weight: 600; font-size: 14px;"
        )

        self.details_label = QLabel(
            f"{channel}  •  {platform}  •  {duration}  •  {status}"
        )
        self.details_label.setObjectName("queueCardDetails")

        self.submitter_label = QLabel(
            f"Submitted by: {submitted_by}  |  Added: {created_at}"
        )
        self.submitter_label.setObjectName(
            "queueCardSubmitter"
        )

        self.url_label = QLabel(url)
        self.url_label.setObjectName("queueCardUrl")
        self.url_label.setWordWrap(True)
        self.url_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.url_label.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.url_label.customContextMenuRequested.connect(
            lambda position, url=url:
            self._show_url_context_menu(position, url)
        )

        for label in (
            self.title_label,
            self.details_label,
            self.submitter_label,
        ):
            label.setAttribute(
                Qt.WidgetAttribute.WA_TransparentForMouseEvents,
                True,
            )

        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.details_label)
        text_layout.addWidget(self.submitter_label)
        text_layout.addWidget(self.url_label)

        text_layout.addStretch()

        layout.addLayout(text_layout, 1)

        self.open_link_button = QPushButton("Open Link")
        self.open_link_button.setObjectName(
            "queueOpenLinkButton"
        )
        self.open_link_button.setFixedWidth(90)
        self.open_link_button.setEnabled(bool(url))
        self.open_link_button.clicked.connect(
            lambda checked=False, url=url:
            QDesktopServices.openUrl(QUrl(url))
        )

        layout.addWidget(
            self.open_link_button,
            0,
            Qt.AlignmentFlag.AlignVCenter,
        )

        self._update_media_layout()

    def _show_url_context_menu(
        self,
        position,
        url: str,
    ) -> None:
        if not url:
            return

        menu = QMenu(self.url_label)
        copy_action = menu.addAction("Copy Link")

        selected_action = menu.exec(
            self.url_label.mapToGlobal(position)
        )

        if selected_action is copy_action:
            QApplication.clipboard().setText(url)

    def _update_media_layout(self) -> None:
        # The full thumbnail is preferred.
        #
        # Only overlap the queue badge and thumbnail when the title
        # would not fit on one line with the normal media footprint.
        title_width = self.title_label.fontMetrics().horizontalAdvance(
            self.title_label.text()
        )

        current_text_width = self.title_label.width()

        # Overlap mode gives the text area 50px more width. If we are
        # already overlapped, subtract that reclaimed space so we can
        # determine whether the normal layout would now fit again.
        currently_overlapped = (
            self.media_container.width() == 128
        )

        if currently_overlapped:
            normal_text_width = max(
                0,
                current_text_width - 50,
            )
        else:
            normal_text_width = current_text_width

        use_overlap = title_width > normal_text_width

        if use_overlap:
            self.media_container.setFixedWidth(128)
            self.thumbnail_label.move(0, 0)
        else:
            self.media_container.setFixedWidth(178)
            self.thumbnail_label.move(50, 0)

        self.position_label.raise_()

    def resizeEvent(self, event) -> None:
        self._update_media_layout()
        super().resizeEvent(event)

    def mousePressEvent(self, event) -> None:
        self._select_callback()

        if (
            event.button()
            == Qt.MouseButton.LeftButton
        ):
            self._drag_start_position = (
                event.position().toPoint()
            )

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if (
            self._drag_callback is not None
            and self._drag_start_position is not None
            and event.buttons()
            & Qt.MouseButton.LeftButton
        ):
            distance = (
                event.position().toPoint()
                - self._drag_start_position
            ).manhattanLength()

            if (
                distance
                >= QApplication.startDragDistance()
            ):
                self._drag_start_position = None
                self._drag_callback()
                event.accept()
                return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self._drag_start_position = None
        super().mouseReleaseEvent(event)

    def set_thumbnail(self, pixmap: QPixmap) -> None:
        if pixmap.isNull():
            return

        scaled = pixmap.scaled(
            self.thumbnail_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.thumbnail_label.setPixmap(scaled)
        self.thumbnail_label.setText("")


class ReorderableQueueTable(QTableWidget):
    def __init__(
        self,
        rows: int,
        columns: int,
        parent: QWidget | None = None,
    ):
        super().__init__(rows, columns, parent)

        self._drag_reorder_enabled = False
        self._drag_source_row: int | None = None
        self._reorder_callback: (
            Callable[[int, int], None] | None
        ) = None

        self.setDragDropOverwriteMode(False)
        self.setDefaultDropAction(
            Qt.DropAction.MoveAction
        )
        self.set_drag_reorder_enabled(False)

    def set_reorder_callback(
        self,
        callback: Callable[[int, int], None] | None,
    ) -> None:
        self._reorder_callback = callback

    def set_drag_reorder_enabled(
        self,
        enabled: bool,
    ) -> None:
        self._drag_reorder_enabled = bool(enabled)

        self.setDragEnabled(
            self._drag_reorder_enabled
        )
        self.setAcceptDrops(
            self._drag_reorder_enabled
        )
        self.viewport().setAcceptDrops(
            self._drag_reorder_enabled
        )
        self.setDropIndicatorShown(
            self._drag_reorder_enabled
        )
        self.setDragDropMode(
            QAbstractItemView.DragDropMode.InternalMove
            if self._drag_reorder_enabled
            else QAbstractItemView.DragDropMode.NoDragDrop
        )

    def begin_row_drag(self, row: int) -> None:
        if not self._drag_reorder_enabled:
            return

        model_item = self.item(row, 0)

        if not self._is_queued_item(model_item):
            return

        self._drag_source_row = row
        self.selectRow(row)
        self.startDrag(Qt.DropAction.MoveAction)

    @staticmethod
    def _is_queued_item(
        model_item: QTableWidgetItem | None,
    ) -> bool:
        if model_item is None:
            return False

        position = model_item.data(
            Qt.ItemDataRole.UserRole + 1
        )

        try:
            return int(position) >= 1
        except (TypeError, ValueError):
            return False

    def queued_rows(self) -> list[int]:
        return [
            row
            for row in range(self.rowCount())
            if self._is_queued_item(
                self.item(row, 0)
            )
        ]

    def request_reorder(
        self,
        source_row: int,
        target_position: int,
    ) -> bool:
        if (
            not self._drag_reorder_enabled
            or self._reorder_callback is None
        ):
            return False

        source_item = self.item(source_row, 0)

        if not self._is_queued_item(source_item):
            return False

        queued_count = len(self.queued_rows())

        try:
            item_id = int(
                source_item.data(
                    Qt.ItemDataRole.UserRole
                )
            )
            current_position = int(
                source_item.data(
                    Qt.ItemDataRole.UserRole + 1
                )
            )
            target_position = int(target_position)
        except (TypeError, ValueError):
            return False

        if (
            target_position < 1
            or target_position > queued_count
            or target_position == current_position
        ):
            return False

        self._reorder_callback(
            item_id,
            target_position,
        )
        return True

    def dropEvent(self, event) -> None:
        if not self._drag_reorder_enabled:
            event.ignore()
            return

        source_row = self._drag_source_row
        self._drag_source_row = None

        if source_row is None:
            event.ignore()
            return

        queued_rows = self.queued_rows()

        if source_row not in queued_rows:
            event.ignore()
            return

        source_index = queued_rows.index(source_row)
        point = event.position().toPoint()
        hovered_index = self.indexAt(point)

        if not hovered_index.isValid():
            insertion_index = len(queued_rows)
        else:
            hovered_row = hovered_index.row()

            if hovered_row not in queued_rows:
                insertion_index = (
                    0
                    if (
                        queued_rows
                        and hovered_row < queued_rows[0]
                    )
                    else len(queued_rows)
                )
            else:
                hovered_queue_index = (
                    queued_rows.index(hovered_row)
                )
                hovered_rect = self.visualRect(
                    hovered_index
                )
                drop_after = (
                    point.y()
                    > hovered_rect.center().y()
                )
                insertion_index = (
                    hovered_queue_index
                    + (1 if drop_after else 0)
                )

        if insertion_index > source_index:
            insertion_index -= 1

        final_index = max(
            0,
            min(
                insertion_index,
                len(queued_rows) - 1,
            ),
        )

        moved = self.request_reorder(
            source_row,
            final_index + 1,
        )

        if moved:
            event.setDropAction(
                Qt.DropAction.MoveAction
            )
            event.accept()
        else:
            event.ignore()


class QueuePage(QWidget):
    def __init__(
        self,
        refresh_callback: Callable[[], None],
        add_video_callback: Callable[[], None],
        refresh_metadata_callback: Callable[[], None],
        export_queue_callback: Callable[[], None],
        export_selected_callback: Callable[[], None],
        export_history_callback: Callable[[], None],
        import_queue_callback: Callable[[], None],
        move_to_beginning_callback: Callable[[], None],
        move_up_callback: Callable[[], None],
        move_down_callback: Callable[[], None],
        move_to_end_callback: Callable[[], None],
        move_to_position_callback: Callable[[], None],
        remove_callback: Callable[[], None],
        clear_queue_callback: Callable[[], None],
        drag_reorder_callback: (
            Callable[[int, int], None] | None
        ) = None,
        parent: QWidget | None = None,
        bulk_add_callback: Callable[[], None] | None = None,
    ):
        super().__init__(parent)

        self._network_manager = QNetworkAccessManager(self)
        self._queue_items: list[dict] = []
        self.view_mode = "queue"
        self._search_query = ""
        self._filter_platform: str | None = None
        self._filter_status: str | None = None
        self._filter_submitter: str | None = None
        self._filter_submission_source: str | None = None
        self._sort_by: str | None = None
        self._sort_descending = False
        self._drag_reorder_enabled = False
        self._drag_reorder_busy = False
        self._drag_reorder_callback = (
            drag_reorder_callback
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 12)
        layout.setSpacing(10)

        self.page_title = QLabel("QUEUE MANAGEMENT")
        self.page_title.setObjectName("pageTitle")
        layout.addWidget(self.page_title)

        group = QGroupBox("Queue")
        group_layout = QVBoxLayout(group)

        header = QHBoxLayout()

        title = QLabel("Current Bot Queue")
        title.setStyleSheet("font-weight: bold;")

        self.video_count_label = QLabel("Videos: 0")
        self.video_count_label.setObjectName("videoCountLabel")

        self.player_count_label = QLabel(
            "Players Connected: 0"
        )
        self.player_count_label.setObjectName(
            "playerCountLabel"
        )

        self.manager_count_label = QLabel(
            "Managers Connected: 0 (including this instance)"
        )
        self.manager_count_label.setObjectName(
            "managerCountLabel"
        )

        header.addWidget(title)
        header.addStretch()

        group_layout.addLayout(header)

        self.queue_status_area = QFrame()
        self.queue_status_area.setObjectName(
            "queueStatusArea"
        )
        self.queue_status_area.setFrameShape(
            QFrame.Shape.StyledPanel
        )

        status_layout = QHBoxLayout(
            self.queue_status_area
        )
        status_layout.setContentsMargins(
            12,
            7,
            12,
            7,
        )
        status_layout.setSpacing(10)

        self.video_count_label.setObjectName(
            "queueVisibleVideoCount"
        )

        self.filter_status_label = QLabel(
            "Filters: None"
        )
        self.filter_status_label.setObjectName(
            "queueActiveFilters"
        )

        self.sort_status_label = QLabel(
            "Sort: Queue Order"
        )
        self.sort_status_label.setObjectName(
            "queueActiveSort"
        )

        status_layout.addWidget(
            self.video_count_label
        )
        status_layout.addWidget(QLabel("|"))
        status_layout.addWidget(
            self.filter_status_label
        )
        status_layout.addWidget(QLabel("|"))
        status_layout.addWidget(
            self.sort_status_label
        )
        status_layout.addStretch()
        status_layout.addWidget(
            self.player_count_label
        )
        status_layout.addWidget(QLabel("|"))
        status_layout.addWidget(
            self.manager_count_label
        )

        group_layout.addWidget(
            self.queue_status_area
        )

        self.playback_mode_notice = QLabel()
        self.playback_mode_notice.setObjectName(
            "roundRobinNotice"
        )
        self.playback_mode_notice.setWordWrap(True)
        self.playback_mode_notice.setStyleSheet(
            "background: #5b4300; color: #fff0b3; "
            "border: 1px solid #b48700; border-radius: 6px; "
            "padding: 8px 10px; font-weight: 600;"
        )
        self.playback_mode_notice.hide()
        group_layout.addWidget(self.playback_mode_notice)

        queue_controls = QHBoxLayout()

        self.view_toggle_button = QPushButton(
            "View History"
        )
        self.view_toggle_button.setObjectName(
            "queueViewToggleButton"
        )
        self.view_toggle_button.clicked.connect(
            self.toggle_view_mode
        )

        self.add_video_button = QPushButton(
            "Add Video"
        )
        self.add_video_button.setObjectName(
            "addVideoButton"
        )
        self.add_video_button.clicked.connect(
            add_video_callback
        )

        self.bulk_add_button = QPushButton("Bulk Add")
        self.bulk_add_button.setObjectName(
            "bulkAddVideoButton"
        )
        self.bulk_add_button.setToolTip(
            "Paste multiple YouTube and TikTok links"
        )

        if bulk_add_callback is not None:
            self.bulk_add_button.clicked.connect(
                bulk_add_callback
            )
        else:
            self.bulk_add_button.setEnabled(False)

        self.search_button = QPushButton("Search")
        self.search_button.setObjectName(
            "queueSearchButton"
        )
        self.search_button.clicked.connect(
            self.show_search_dialog
        )

        self.filters_button = QPushButton("Filters")
        self.filters_button.setObjectName(
            "queueFiltersButton"
        )
        self.filters_button.clicked.connect(
            self.show_filter_dialog
        )

        self.sort_button = QPushButton("Sort")
        self.sort_button.setObjectName(
            "queueSortButton"
        )
        self.sort_button.clicked.connect(
            self.show_sort_dialog
        )

        self.drag_reorder_button = QPushButton(
            "Drag Reorder: Off"
        )
        self.drag_reorder_button.setObjectName(
            "queueDragReorderButton"
        )
        self.drag_reorder_button.setCheckable(True)
        self.drag_reorder_button.setToolTip(
            "Enable dragging queue cards into a new "
            "canonical queue position"
        )
        self.drag_reorder_button.clicked.connect(
            self.toggle_drag_reorder
        )

        self.select_all_button = QPushButton("Select All")
        self.select_all_button.setObjectName(
            "queueSelectAllButton"
        )
        self.select_all_button.clicked.connect(
            self.toggle_select_all
        )

        self.move_to_beginning_button = QPushButton(
            "Move to Beginning"
        )
        self.move_to_beginning_button.setObjectName(
            "moveToBeginningButton"
        )
        self.move_to_beginning_button.clicked.connect(
            move_to_beginning_callback
        )

        self.move_up_button = QPushButton("Move Up")
        self.move_up_button.setObjectName(
            "moveUpButton"
        )
        self.move_up_button.clicked.connect(
            move_up_callback
        )

        self.move_down_button = QPushButton(
            "Move Down"
        )
        self.move_down_button.setObjectName(
            "moveDownButton"
        )
        self.move_down_button.clicked.connect(
            move_down_callback
        )

        self.move_to_end_button = QPushButton(
            "Move to End"
        )
        self.move_to_end_button.setObjectName(
            "moveToEndButton"
        )
        self.move_to_end_button.clicked.connect(
            move_to_end_callback
        )

        self.remove_selected_button = QPushButton(
            "Remove Selected"
        )
        self.remove_selected_button.setObjectName(
            "removeSelectedButton"
        )
        self.remove_selected_button.clicked.connect(
            remove_callback
        )

        self.clear_queue_button = QPushButton(
            "Clear Queue"
        )
        self.clear_queue_button.setObjectName(
            "clearQueueButton"
        )
        self.clear_queue_button.clicked.connect(
            clear_queue_callback
        )

        self.refresh_queue_button = QPushButton(
            "Refresh Queue"
        )
        self.refresh_queue_button.setObjectName(
            "refreshQueueButton"
        )
        self.refresh_queue_button.clicked.connect(
            refresh_callback
        )

        self.import_export_button = QPushButton(
            "Import / Export"
        )
        self.import_export_button.setObjectName(
            "queueImportExportButton"
        )
        self.import_export_button.clicked.connect(
            self.show_import_export_dialog
        )

        self.export_queue_button = QPushButton(
            "Export Queue"
        )
        self.export_queue_button.setObjectName(
            "exportQueueButton"
        )
        self.export_queue_button.clicked.connect(
            export_queue_callback
        )

        self.export_selected_button = QPushButton(
            "Export Selected"
        )
        self.export_selected_button.setObjectName(
            "exportSelectedButton"
        )
        self.export_selected_button.clicked.connect(
            export_selected_callback
        )

        self.export_history_button = QPushButton(
            "Export History"
        )
        self.export_history_button.setObjectName(
            "exportHistoryButton"
        )
        self.export_history_button.clicked.connect(
            export_history_callback
        )

        self.import_queue_button = QPushButton(
            "Import Queue"
        )
        self.import_queue_button.setObjectName(
            "importQueueButton"
        )
        self.import_queue_button.clicked.connect(
            import_queue_callback
        )

        self.refresh_metadata_button = QPushButton(
            "Refresh Metadata"
        )
        self.refresh_metadata_button.setObjectName(
            "refreshMetadataButton"
        )
        self.refresh_metadata_button.clicked.connect(
            refresh_metadata_callback
        )

        queue_controls.addWidget(
            self.view_toggle_button
        )
        queue_controls.addWidget(
            self.add_video_button
        )
        queue_controls.addWidget(
            self.bulk_add_button
        )
        queue_controls.addWidget(
            self.search_button
        )
        queue_controls.addWidget(
            self.filters_button
        )
        queue_controls.addWidget(
            self.sort_button
        )
        queue_controls.addWidget(
            self.drag_reorder_button
        )
        queue_controls.addWidget(
            self.select_all_button
        )
        queue_controls.addWidget(
            self.import_export_button
        )
        queue_controls.addWidget(
            self.move_to_beginning_button
        )
        queue_controls.addWidget(
            self.move_up_button
        )
        queue_controls.addWidget(
            self.move_down_button
        )
        queue_controls.addWidget(
            self.move_to_end_button
        )
        queue_controls.addWidget(
            self.remove_selected_button
        )
        queue_controls.addWidget(
            self.clear_queue_button
        )
        queue_controls.addStretch()

        maintenance_controls = QHBoxLayout()

        maintenance_controls.addStretch()

        maintenance_controls.addWidget(
            self.refresh_queue_button
        )
        maintenance_controls.addWidget(
            self.refresh_metadata_button
        )

        group_layout.addLayout(queue_controls)
        group_layout.addLayout(maintenance_controls)

        self.queue_table = ReorderableQueueTable(
            0,
            1,
        )
        self.queue_table.setObjectName("queueTable")
        self.queue_table.set_reorder_callback(
            self._request_drag_reorder
        )

        self.queue_table.horizontalHeader().hide()
        self.queue_table.verticalHeader().hide()

        self.queue_table.horizontalHeader().setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.Stretch,
        )

        self.queue_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.queue_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.queue_table.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.queue_table.setShowGrid(False)
        self.queue_table.setWordWrap(True)

        self.queue_table.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.queue_table.setVerticalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel
        )

        self.queue_table.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.queue_table.customContextMenuRequested.connect(
            lambda pos: self._show_queue_context_menu(
                pos,
                move_to_beginning_callback,
                move_up_callback,
                move_down_callback,
                move_to_end_callback,
                move_to_position_callback,
                remove_callback,
            )
        )

        group_layout.addWidget(self.queue_table)

        layout.addWidget(group, 1)

    @staticmethod
    def _queue_position(item: dict) -> int | None:
        try:
            position = int(item.get("position"))
        except (TypeError, ValueError):
            return None

        return position if position >= 1 else None

    def optimistically_reorder_item(
        self,
        item_id: int,
        target_position: int,
    ) -> bool:
        queued_items = sorted(
            (
                dict(item)
                for item in self._queue_items
                if self._queue_position(item) is not None
            ),
            key=lambda item: (
                self._queue_position(item) or 0
            ),
        )

        source_index = next(
            (
                index
                for index, item in enumerate(queued_items)
                if item.get("id") == item_id
            ),
            None,
        )

        if source_index is None:
            return False

        try:
            target_index = int(target_position) - 1
        except (TypeError, ValueError):
            return False

        if not 0 <= target_index < len(queued_items):
            return False

        moved_item = queued_items.pop(source_index)
        queued_items.insert(target_index, moved_item)

        for position, item in enumerate(
            queued_items,
            start=1,
        ):
            item["position"] = position

        replacements = iter(queued_items)
        reordered_items = []

        for item in self._queue_items:
            if self._queue_position(item) is None:
                reordered_items.append(item)
            else:
                reordered_items.append(next(replacements))

        self._queue_items = reordered_items
        self._refresh_local_view()
        return True

    def set_drag_reorder_busy(
        self,
        busy: bool,
    ) -> None:
        self._drag_reorder_busy = bool(busy)
        self.drag_reorder_button.setEnabled(
            not self._drag_reorder_busy
            and self.view_mode == "queue"
        )

        if self._drag_reorder_busy:
            self.drag_reorder_button.setText(
                "Drag Reorder: Saving..."
            )
            self.queue_table.set_drag_reorder_enabled(
                False
            )
            return

        self.drag_reorder_button.setText(
            "Drag Reorder: On"
            if self._drag_reorder_enabled
            else "Drag Reorder: Off"
        )
        self.queue_table.set_drag_reorder_enabled(
            self._drag_reorder_enabled
            and self._drag_reorder_is_available()
        )

    def _drag_reorder_is_available(self) -> bool:
        return (
            self.view_mode == "queue"
            and not self._search_query
            and self._filter_platform is None
            and self._filter_status is None
            and self._filter_submitter is None
            and self._filter_submission_source is None
            and self._sort_by is None
        )

    def set_drag_reorder_enabled(
        self,
        enabled: bool,
    ) -> bool:
        enabled = bool(enabled)

        if (
            enabled
            and not self._drag_reorder_is_available()
        ):
            self._drag_reorder_enabled = False
            self.drag_reorder_button.setChecked(False)
            self.drag_reorder_button.setText(
                "Drag Reorder: Off"
            )
            self.queue_table.set_drag_reorder_enabled(
                False
            )

            QMessageBox.information(
                self,
                "Drag Reorder Unavailable",
                "Return to the Queue and clear search, "
                "filters, and sorting before enabling "
                "drag reordering.",
            )
            return False

        self._drag_reorder_enabled = enabled
        self.drag_reorder_button.setChecked(enabled)
        self.drag_reorder_button.setText(
            "Drag Reorder: On"
            if enabled
            else "Drag Reorder: Off"
        )
        self.queue_table.set_drag_reorder_enabled(
            enabled
        )
        return enabled

    def toggle_drag_reorder(
        self,
        checked: bool = False,
    ) -> None:
        self.set_drag_reorder_enabled(bool(checked))

    def _request_drag_reorder(
        self,
        item_id: int,
        target_position: int,
    ) -> None:
        if self._drag_reorder_callback is None:
            return

        self._drag_reorder_callback(
            item_id,
            target_position,
        )

    def toggle_view_mode(self) -> None:
        if self.view_mode == "queue":
            self.set_view_mode("history")
        else:
            self.set_view_mode("queue")

    def set_view_mode(self, mode: str) -> None:
        if mode not in {"queue", "history"}:
            raise ValueError(
                f"Unsupported queue view mode: {mode}"
            )

        self.view_mode = mode
        history_mode = mode == "history"

        self.view_toggle_button.setText(
            "View Queue"
            if history_mode
            else "View History"
        )

        queue_only_controls = (
            self.add_video_button,
            self.drag_reorder_button,
            self.select_all_button,
            self.move_to_beginning_button,
            self.move_up_button,
            self.move_down_button,
            self.move_to_end_button,
            self.remove_selected_button,
            self.clear_queue_button,
            self.refresh_metadata_button,
        )

        for control in queue_only_controls:
            control.setEnabled(not history_mode)

        if history_mode:
            self.queue_table.clearSelection()
            self.select_all_button.setText("Select All")

    def selected_queue_item_ids(self) -> list[int]:
        selected_ids = []

        for index in self.queue_table.selectionModel().selectedRows():
            item = self.queue_table.item(index.row(), 0)

            if item is None:
                continue

            position = item.data(
                Qt.ItemDataRole.UserRole + 1
            )

            try:
                position = int(position)
            except (TypeError, ValueError):
                continue

            if position < 1:
                continue

            item_id = item.data(
                Qt.ItemDataRole.UserRole
            )

            try:
                item_id = int(item_id)
            except (TypeError, ValueError):
                continue

            selected_ids.append(item_id)

        return selected_ids

    def show_import_export_dialog(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Import / Export")

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        layout.addWidget(self.import_queue_button)
        layout.addWidget(self.export_queue_button)
        layout.addWidget(self.export_selected_button)
        layout.addWidget(self.export_history_button)

        dialog.exec()

    def toggle_select_all(self) -> None:
        selectable_rows = []

        for row in range(self.queue_table.rowCount()):
            item = self.queue_table.item(row, 0)

            if item is None:
                continue

            position = item.data(
                Qt.ItemDataRole.UserRole + 1
            )

            try:
                position = int(position)
            except (TypeError, ValueError):
                continue

            if position >= 1:
                selectable_rows.append(row)

        selected_rows = {
            index.row()
            for index
            in self.queue_table.selectionModel().selectedRows()
        }

        all_selected = (
            bool(selectable_rows)
            and all(
                row in selected_rows
                for row in selectable_rows
            )
        )

        if all_selected:
            self.queue_table.clearSelection()
            self.select_all_button.setText("Select All")
            return

        self.queue_table.clearSelection()

        for row in selectable_rows:
            item = self.queue_table.item(row, 0)

            if item is not None:
                item.setSelected(True)

        self.select_all_button.setText("Deselect All")

    def show_search_dialog(self) -> None:
        if self._search_query:
            self.apply_search("")
            return

        view_name = (
            "History"
            if self.view_mode == "history"
            else "Queue"
        )

        query, accepted = QInputDialog.getText(
            self,
            f"Search {view_name}",
            "Search title, channel, URL, submitter, or platform:",
        )

        if accepted:
            self.apply_search(query)

    def show_filter_dialog(self) -> None:
        dialog = QDialog(self)

        view_name = (
            "History"
            if self.view_mode == "history"
            else "Queue"
        )

        dialog.setWindowTitle(
            f"{view_name} Filters"
        )
        dialog.setModal(True)

        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("Platform"))

        platform_combo = QComboBox()
        platform_combo.setObjectName(
            "queuePlatformFilter"
        )
        platform_combo.addItem("Any Platform", None)
        platform_combo.addItem(
            "YouTube",
            "youtube",
        )
        platform_combo.addItem(
            "TikTok",
            "tiktok",
        )

        platform_index = platform_combo.findData(
            self._filter_platform
        )

        if platform_index >= 0:
            platform_combo.setCurrentIndex(
                platform_index
            )

        layout.addWidget(platform_combo)

        layout.addWidget(QLabel("Status"))

        status_combo = QComboBox()
        status_combo.setObjectName(
            "queueStatusFilter"
        )
        status_combo.addItem("Any Status", None)
        status_combo.addItem(
            "Queued",
            "queued",
        )
        status_combo.addItem(
            "Playing",
            "playing",
        )
        status_combo.addItem(
            "Played",
            "played",
        )

        status_index = status_combo.findData(
            self._filter_status
        )

        if status_index >= 0:
            status_combo.setCurrentIndex(
                status_index
            )

        layout.addWidget(status_combo)

        layout.addWidget(QLabel("Submitted By"))

        submitter_combo = QComboBox()
        submitter_combo.setObjectName(
            "queueSubmitterFilter"
        )
        submitter_combo.addItem(
            "Any Submitter",
            None,
        )

        submitters = sorted(
            {
                str(
                    item.get("submitted_by") or ""
                ).strip()
                for item in self._queue_items
                if str(
                    item.get("submitted_by") or ""
                ).strip()
            },
            key=str.casefold,
        )

        for submitter in submitters:
            submitter_combo.addItem(
                submitter,
                submitter.casefold(),
            )

        submitter_index = submitter_combo.findData(
            self._filter_submitter
        )

        if submitter_index >= 0:
            submitter_combo.setCurrentIndex(
                submitter_index
            )

        layout.addWidget(submitter_combo)

        layout.addWidget(
            QLabel("Submission Source")
        )

        source_combo = QComboBox()
        source_combo.setObjectName(
            "queueSubmissionSourceFilter"
        )
        source_combo.addItem(
            "Any Source",
            None,
        )
        source_combo.addItem(
            "Chat",
            "chat",
        )
        source_combo.addItem(
            "Manager",
            "manager",
        )
        source_combo.addItem(
            "Player",
            "player",
        )

        source_index = source_combo.findData(
            self._filter_submission_source
        )

        if source_index >= 0:
            source_combo.setCurrentIndex(
                source_index
            )

        layout.addWidget(source_combo)

        button_row = QHBoxLayout()

        clear_button = QPushButton("Clear")
        clear_button.setObjectName(
            "clearQueueFiltersButton"
        )
        clear_button.setEnabled(
            any(
                value is not None
                for value in (
                    self._filter_platform,
                    self._filter_status,
                    self._filter_submitter,
                    self._filter_submission_source,
                )
            )
        )

        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName(
            "cancelQueueFiltersButton"
        )

        apply_button = QPushButton("Apply")
        apply_button.setObjectName(
            "applyQueueFiltersButton"
        )
        apply_button.setDefault(True)

        button_row.addWidget(clear_button)
        button_row.addStretch()
        button_row.addWidget(cancel_button)
        button_row.addWidget(apply_button)
        layout.addLayout(button_row)

        def clear_filters() -> None:
            self.apply_filters()
            dialog.accept()

        def apply_selected_filters() -> None:
            self.apply_filters(
                platform=platform_combo.currentData(),
                status=status_combo.currentData(),
                submitter=submitter_combo.currentData(),
                submission_source=source_combo.currentData(),
            )
            dialog.accept()

        clear_button.clicked.connect(clear_filters)
        cancel_button.clicked.connect(dialog.reject)
        apply_button.clicked.connect(
            apply_selected_filters
        )

        dialog.exec()

    def show_sort_dialog(self) -> None:
        dialog = QDialog(self)

        view_name = (
            "History"
            if self.view_mode == "history"
            else "Queue"
        )

        dialog.setWindowTitle(f"{view_name} Sort")
        dialog.setModal(True)

        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("Sort By"))

        sort_combo = QComboBox()
        sort_combo.addItem("Queue Position", "position")
        sort_combo.addItem("Title", "title")
        sort_combo.addItem(
            "Channel / Creator",
            "channel",
        )
        sort_combo.addItem("Platform", "platform")
        sort_combo.addItem("Submitter", "submitted_by")
        sort_combo.addItem("Added", "created_at")

        sort_combo.addItem(
            "Video Length",
            "duration",
        )
        sort_combo.addItem("Played", "played_at")
        layout.addWidget(sort_combo)

        if self._sort_by is not None:
            index = sort_combo.findData(self._sort_by)

            if index >= 0:
                sort_combo.setCurrentIndex(index)

        layout.addWidget(QLabel("Direction"))

        direction_combo = QComboBox()
        direction_combo.addItem("Ascending", False)
        direction_combo.addItem("Descending", True)
        direction_combo.setCurrentIndex(
            1 if self._sort_descending else 0
        )
        layout.addWidget(direction_combo)

        button_row = QHBoxLayout()

        clear_button = QPushButton("Clear")
        apply_button = QPushButton("Apply")

        button_row.addWidget(clear_button)
        button_row.addWidget(apply_button)
        layout.addLayout(button_row)

        def clear_sort() -> None:
            self.apply_sort()
            dialog.accept()

        def apply_selected_sort() -> None:
            self.apply_sort(
                sort_by=sort_combo.currentData(),
                descending=bool(
                    direction_combo.currentData()
                ),
            )
            dialog.accept()

        clear_button.clicked.connect(clear_sort)
        apply_button.clicked.connect(
            apply_selected_sort
        )

        dialog.exec()

    def _show_queue_context_menu(
        self,
        pos,
        move_to_beginning_callback: Callable[[], None],
        move_up_callback: Callable[[], None],
        move_down_callback: Callable[[], None],
        move_to_end_callback: Callable[[], None],
        move_to_position_callback: Callable[[], None],
        remove_callback: Callable[[], None],
    ) -> None:
        index = self.queue_table.indexAt(pos)

        if not index.isValid():
            return

        row = index.row()
        self.queue_table.selectRow(row)

        model_item = self.queue_table.item(row, 0)

        if model_item is None:
            return

        position = model_item.data(
            Qt.ItemDataRole.UserRole + 1
        )

        try:
            position = int(position)
        except (TypeError, ValueError):
            position = None

        row_count = self.queue_table.rowCount()

        menu = QMenu(self.queue_table)

        move_beginning_action = menu.addAction(
            "Move to Beginning"
        )
        move_up_action = menu.addAction("Move Up")
        move_down_action = menu.addAction("Move Down")
        move_end_action = menu.addAction("Move to End")
        move_position_action = menu.addAction(
            "Move to Position..."
        )

        menu.addSeparator()

        card = self.queue_table.cellWidget(row, 0)
        open_link_action = menu.addAction("Open Link")
        open_link_action.setEnabled(
            isinstance(card, QueueCard)
            and card.open_link_button.isEnabled()
        )

        menu.addSeparator()

        remove_action = menu.addAction("Remove")
        is_queue_item = position is not None
        remove_action.setEnabled(is_queue_item)


        if is_queue_item:
            at_top = position <= 1
            at_bottom = position >= row_count

            move_beginning_action.setEnabled(not at_top)
            move_up_action.setEnabled(not at_top)
            move_down_action.setEnabled(not at_bottom)
            move_end_action.setEnabled(not at_bottom)
            move_position_action.setEnabled(True)
        else:
            move_beginning_action.setEnabled(False)
            move_up_action.setEnabled(False)
            move_down_action.setEnabled(False)
            move_end_action.setEnabled(False)
            move_position_action.setEnabled(False)

        selected_action = menu.exec(
            self.queue_table.viewport().mapToGlobal(pos)
        )

        if selected_action is move_beginning_action:
            move_to_beginning_callback()
        elif selected_action is move_up_action:
            move_up_callback()
        elif selected_action is move_down_action:
            move_down_callback()
        elif selected_action is move_end_action:
            move_to_end_callback()
        elif selected_action is move_position_action:
            move_to_position_callback()
        elif selected_action is open_link_action:
            if isinstance(card, QueueCard):
                card.open_link_button.click()
        elif selected_action is remove_action:
            remove_callback()

    def max_queue_position(self) -> int:
        positions = []

        for item in self._queue_items:
            position = item.get("position")

            try:
                position = int(position)
            except (TypeError, ValueError):
                continue

            if position >= 1:
                positions.append(position)

        return max(positions, default=0)

    def render_items(self, items: list[dict]) -> None:
        self._queue_items = list(items)
        self._refresh_local_view()

    def set_playback_mode(self, mode: str) -> None:
        round_robin = mode == "round_robin"
        self.playback_mode_notice.setText(
            "Round Robin playback is active. Queue reordering "
            "is saved, but does not affect the active playback "
            "order. Standard mode will use the saved queue order."
        )
        self.playback_mode_notice.setVisible(round_robin)

    def apply_search(self, query: str) -> None:
        self._search_query = query.strip().casefold()

        self.search_button.setText(
            "Clear Search"
            if self._search_query
            else "Search"
        )

        self._refresh_local_view()

    def apply_filters(
        self,
        *,
        platform: str | None = None,
        status: str | None = None,
        submitter: str | None = None,
        submission_source: str | None = None,
    ) -> None:
        self._filter_platform = (
            platform.strip().casefold()
            if platform
            else None
        )
        self._filter_status = (
            status.strip().casefold()
            if status
            else None
        )
        self._filter_submitter = (
            submitter.strip().casefold()
            if submitter
            else None
        )
        self._filter_submission_source = (
            submission_source.strip().casefold()
            if submission_source
            else None
        )

        active_filters = []

        if self._filter_platform:
            active_filters.append(
                "Platform: "
                + self._filter_platform.title()
            )

        if self._filter_status:
            active_filters.append(
                "Status: "
                + self._filter_status.title()
            )

        if self._filter_submitter:
            active_filters.append(
                "Submitted by: "
                + self._filter_submitter
            )

        if self._filter_submission_source:
            active_filters.append(
                "Source: "
                + self._filter_submission_source.title()
            )

        active_count = len(active_filters)

        self.filters_button.setText(
            f"Filters ({active_count})"
            if active_count
            else "Filters"
        )

        self.filters_button.setToolTip(
            "; ".join(active_filters)
            if active_filters
            else "Filter the current view"
        )

        self.filter_status_label.setText(
            (
                "Filters: "
                + "; ".join(active_filters)
            )
            if active_filters
            else "Filters: None"
        )

        self._refresh_local_view()

    def apply_sort(
        self,
        *,
        sort_by: str | None = None,
        descending: bool = False,
    ) -> None:
        self._sort_by = (
            sort_by.strip().casefold()
            if sort_by
            else None
        )
        self._sort_descending = (
            bool(descending)
            if self._sort_by is not None
            else False
        )

        self.sort_button.setText(
            "Sort (Active)"
            if self._sort_by is not None
            else "Sort"
        )

        sort_labels = {
            "position": "Queue Position",
            "title": "Title",
            "channel": "Video Channel",
            "platform": "Platform",
            "submitted_by": "Submitted By",
            "created_at": "Date Added",
            "duration": "Video Length",
        }

        if self._sort_by is None:
            sort_text = "Sort: Queue Order"
        else:
            label = sort_labels.get(
                self._sort_by,
                self._sort_by.replace(
                    "_",
                    " ",
                ).title(),
            )
            direction = (
                "Descending"
                if self._sort_descending
                else "Ascending"
            )
            sort_text = (
                f"Sort: {label} ({direction})"
            )

        self.sort_status_label.setText(
            sort_text
        )

        self._refresh_local_view()

    def _refresh_local_view(self) -> None:
        if (
            self._drag_reorder_enabled
            and not self._drag_reorder_is_available()
        ):
            self.set_drag_reorder_enabled(False)

        searchable_fields = (
            "title",
            "video_channel",
            "channel",
            "url",
            "submitted_by",
            "platform",
        )

        visible_items = []

        for item in self._queue_items:
            if self._search_query and not any(
                self._search_query
                in str(item.get(field) or "").casefold()
                for field in searchable_fields
            ):
                continue

            if (
                self._filter_platform is not None
                and str(item.get("platform") or "").casefold()
                != self._filter_platform
            ):
                continue

            if (
                self._filter_status is not None
                and str(item.get("status") or "").casefold()
                != self._filter_status
            ):
                continue

            if (
                self._filter_submitter is not None
                and str(
                    item.get("submitted_by") or ""
                ).casefold()
                != self._filter_submitter
            ):
                continue

            item_source = str(
                item.get("submission_source") or ""
            ).casefold()

            if (
                self._filter_submission_source == "chat"
                and item_source not in {
                    "chat",
                    "twitch",
                }
            ):
                continue

            if (
                self._filter_submission_source
                not in {
                    None,
                    "chat",
                }
                and item_source
                != self._filter_submission_source
            ):
                continue

            visible_items.append(item)

        if self._sort_by is not None:
            populated_items = []
            missing_items = []

            for item in visible_items:
                if self._sort_by == "channel":
                    value = (
                        item.get("video_channel")
                        or item.get("channel")
                    )
                else:
                    value = item.get(self._sort_by)

                if value is None or value == "":
                    missing_items.append(item)
                    continue

                populated_items.append(item)

            def sort_key(item: dict):
                if self._sort_by == "channel":
                    value = (
                        item.get("video_channel")
                        or item.get("channel")
                        or ""
                    )
                else:
                    value = item.get(self._sort_by)

                if self._sort_by in {
                    "position",
                    "duration",
                }:
                    try:
                        return int(value)
                    except (TypeError, ValueError):
                        return 0

                return str(value or "").casefold()

            populated_items.sort(
                key=sort_key,
                reverse=self._sort_descending,
            )

            visible_items = (
                populated_items + missing_items
            )

        self._render_visible_items(visible_items)

    def _render_visible_items(self, items: list[dict]) -> None:
        self.video_count_label.setText(f"Videos: {len(items)}")
        selected_item_id = None
        selected_row = self.queue_table.currentRow()

        if selected_row >= 0:
            selected_item = self.queue_table.item(
                selected_row,
                0,
            )

            if selected_item is not None:
                selected_item_id = selected_item.data(
                    Qt.ItemDataRole.UserRole
                )

        self.queue_table.clearContents()
        self.queue_table.setRowCount(len(items))

        for row, item in enumerate(items):
            position = item.get("position")

            model_item = QTableWidgetItem("")
            model_item.setData(
                Qt.ItemDataRole.UserRole,
                item.get("id"),
            )
            model_item.setData(
                Qt.ItemDataRole.UserRole + 1,
                position,
            )

            self.queue_table.setItem(
                row,
                0,
                model_item,
            )

            card = QueueCard(
                item,
                lambda row=row: self.queue_table.selectRow(row),
                self.queue_table,
                drag_callback=(
                    lambda row=row:
                    self.queue_table.begin_row_drag(row)
                ),
            )

            self.queue_table.setCellWidget(
                row,
                0,
                card,
            )

            self.queue_table.setRowHeight(
                row,
                118,
            )

            thumbnail_url = item.get("thumbnail")

            if (
                selected_item_id is not None
                and item.get("id") == selected_item_id
            ):
                self.queue_table.selectRow(row)

            if thumbnail_url:
                self._load_thumbnail(
                    str(thumbnail_url),
                    card,
                )

    def _load_thumbnail(
        self,
        url: str,
        card: QueueCard,
    ) -> None:
        request = QNetworkRequest(QUrl(url))
        reply = self._network_manager.get(request)

        reply.finished.connect(
            lambda reply=reply, card=card:
            self._thumbnail_finished(
                reply,
                card,
            )
        )

    def _thumbnail_finished(
        self,
        reply: QNetworkReply,
        card: QueueCard,
    ) -> None:
        try:
            if (
                reply.error()
                != QNetworkReply.NetworkError.NoError
            ):
                return

            pixmap = QPixmap()
            pixmap.loadFromData(reply.readAll())

            try:
                card.set_thumbnail(pixmap)
            except RuntimeError as exc:
                if "already deleted" not in str(exc):
                    raise
        finally:
            reply.deleteLater()
