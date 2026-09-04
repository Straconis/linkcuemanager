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
    QComboBox,
    QDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QMenu,
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


class QueueCard(QFrame):
    def __init__(
        self,
        item: dict,
        select_callback: Callable[[], None],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        self._select_callback = select_callback

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
            f"Submitted by: {submitted_by}"
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
        super().mousePressEvent(event)

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
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        self._network_manager = QNetworkAccessManager(self)
        self._queue_items: list[dict] = []
        self.view_mode = "queue"
        self._search_query = ""
        self._filter_platform: str | None = None
        self._filter_status: str | None = None

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
        header.addSpacing(12)
        header.addWidget(self.video_count_label)
        header.addStretch()
        header.addWidget(self.player_count_label)
        header.addSpacing(12)
        header.addWidget(self.manager_count_label)

        group_layout.addLayout(header)

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
            self.search_button
        )
        queue_controls.addWidget(
            self.filters_button
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

        self.queue_table = QTableWidget(0, 1)
        self.queue_table.setObjectName("queueTable")

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
        dialog.setWindowTitle("Queue Filters")
        dialog.setModal(True)

        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("Platform"))

        platform_combo = QComboBox()
        platform_combo.addItem("Any", None)
        platform_combo.addItem("YouTube", "youtube")
        platform_combo.addItem("TikTok", "tiktok")
        layout.addWidget(platform_combo)

        layout.addWidget(QLabel("Status"))

        status_combo = QComboBox()
        status_combo.addItem("Any", None)
        status_combo.addItem("Queued", "queued")
        status_combo.addItem("Playing", "playing")
        status_combo.addItem("Played", "played")
        layout.addWidget(status_combo)

        button_row = QHBoxLayout()

        clear_button = QPushButton("Clear")
        apply_button = QPushButton("Apply")

        button_row.addWidget(clear_button)
        button_row.addWidget(apply_button)
        layout.addLayout(button_row)

        def clear_filters() -> None:
            self.apply_filters()
            dialog.accept()

        def apply_selected_filters() -> None:
            self.apply_filters(
                platform=platform_combo.currentData(),
                status=status_combo.currentData(),
            )
            dialog.accept()

        clear_button.clicked.connect(clear_filters)
        apply_button.clicked.connect(
            apply_selected_filters
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
        self._refresh_local_view()

    def _refresh_local_view(self) -> None:
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

            visible_items.append(item)

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
