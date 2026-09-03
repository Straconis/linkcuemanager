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
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
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

        self.position_label = QLabel(
            "" if position is None else str(position),
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
        export_history_callback: Callable[[], None],
        import_queue_callback: Callable[[], None],
        move_to_beginning_callback: Callable[[], None],
        move_up_callback: Callable[[], None],
        move_down_callback: Callable[[], None],
        move_to_end_callback: Callable[[], None],
        remove_callback: Callable[[], None],
        clear_queue_callback: Callable[[], None],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        self._network_manager = QNetworkAccessManager(self)

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
        header.addWidget(self.player_count_label)
        header.addSpacing(12)
        header.addWidget(self.manager_count_label)

        group_layout.addLayout(header)

        queue_controls = QHBoxLayout()

        self.add_video_button = QPushButton(
            "Add Video"
        )
        self.add_video_button.setObjectName(
            "addVideoButton"
        )
        self.add_video_button.clicked.connect(
            add_video_callback
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

        self.export_queue_button = QPushButton(
            "Export Queue"
        )
        self.export_queue_button.setObjectName(
            "exportQueueButton"
        )
        self.export_queue_button.clicked.connect(
            export_queue_callback
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
            self.add_video_button
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

        maintenance_controls.addWidget(
            self.import_queue_button
        )
        maintenance_controls.addWidget(
            self.export_queue_button
        )
        maintenance_controls.addWidget(
            self.export_history_button
        )

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
            QAbstractItemView.SelectionMode.SingleSelection
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
                remove_callback,
            )
        )

        group_layout.addWidget(self.queue_table)

        layout.addWidget(group, 1)

    def _show_queue_context_menu(
        self,
        pos,
        move_to_beginning_callback: Callable[[], None],
        move_up_callback: Callable[[], None],
        move_down_callback: Callable[[], None],
        move_to_end_callback: Callable[[], None],
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

        menu.addSeparator()

        card = self.queue_table.cellWidget(row, 0)
        open_link_action = menu.addAction("Open Link")
        open_link_action.setEnabled(
            isinstance(card, QueueCard)
            and card.open_link_button.isEnabled()
        )

        menu.addSeparator()

        remove_action = menu.addAction("Remove")

        if position is not None:
            at_top = position <= 1
            at_bottom = position >= row_count

            move_beginning_action.setEnabled(not at_top)
            move_up_action.setEnabled(not at_top)
            move_down_action.setEnabled(not at_bottom)
            move_end_action.setEnabled(not at_bottom)

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
        elif selected_action is open_link_action:
            if isinstance(card, QueueCard):
                card.open_link_button.click()
        elif selected_action is remove_action:
            remove_callback()

    def render_items(self, items: list[dict]) -> None:
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
