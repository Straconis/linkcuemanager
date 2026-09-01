import os
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.bot_client import BotClient, BotClientError
from app.config import APP_NAME, APP_VERSION, DEFAULT_BOT_URL
from app.queue_event_listener import (
    QueueEventListener,
    websocket_events_url,
)


class ManagerWindow(QMainWindow):
    queue_refresh_requested = Signal(dict)

    def __init__(self):
        super().__init__()

        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.resize(1000, 700)

        base_url = os.getenv(
            "LINKCUE_BOT_URL",
            DEFAULT_BOT_URL,
        )
        self.bot_client = BotClient(base_url)

        root = QWidget()
        self.setCentralWidget(root)

        layout = QVBoxLayout(root)
        layout.setContentsMargins(10, 10, 10, 8)
        layout.setSpacing(8)

        layout.addWidget(self._build_bot_section())
        layout.addWidget(self._build_player_section())
        layout.addWidget(self._build_twitch_section())
        layout.addWidget(self._build_queue_section(), 1)

        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("statusLabel")
        layout.addWidget(self.status_label)

        self.queue_refresh_requested.connect(
            self.refresh_queue
        )

        self.queue_event_listener = QueueEventListener(
            base_url,
            self.queue_refresh_requested.emit,
        )
        self.queue_event_listener.start()

        # Establish the initial Player state once the UI event loop starts.
        QTimer.singleShot(0, self.refresh_player_status)

    def _build_bot_section(self) -> QGroupBox:
        group = QGroupBox("LinkCue Bot")
        layout = QHBoxLayout(group)

        layout.addWidget(QLabel("Bot URL:"))

        self.bot_url_input = QLineEdit(self.bot_client.base_url)
        self.bot_url_input.setObjectName("botUrlInput")
        layout.addWidget(self.bot_url_input, 1)

        self.test_connection_button = QPushButton("Test Connection")
        self.test_connection_button.setObjectName(
            "testConnectionButton"
        )
        self.test_connection_button.clicked.connect(
            self.test_connection
        )
        layout.addWidget(self.test_connection_button)

        layout.addWidget(QLabel("Status:"))

        self.bot_status_label = QLabel("Not checked")
        self.bot_status_label.setObjectName("botStatusLabel")
        self.bot_status_label.setMinimumWidth(120)
        layout.addWidget(self.bot_status_label)

        self.dark_mode_button = QPushButton("Dark Mode")
        self.dark_mode_button.setObjectName("darkModeButton")
        self.dark_mode_button.setCheckable(True)
        self.dark_mode_button.toggled.connect(
            self.set_dark_mode
        )
        layout.addWidget(self.dark_mode_button)

        return group

    def _build_player_section(self) -> QGroupBox:
        group = QGroupBox("LinkCue Player")
        layout = QHBoxLayout(group)

        layout.addWidget(QLabel("Player:"))

        self.player_status_label = QLabel("Not checked")
        self.player_status_label.setObjectName(
            "playerStatusLabel"
        )
        layout.addWidget(self.player_status_label)

        layout.addSpacing(20)
        layout.addWidget(QLabel("Playback:"))

        self.playback_status_label = QLabel("Not checked")
        self.playback_status_label.setObjectName(
            "playbackStatusLabel"
        )
        layout.addWidget(self.playback_status_label)

        layout.addSpacing(20)
        layout.addWidget(QLabel("Now Playing:"))

        self.now_playing_label = QLabel("None")
        self.now_playing_label.setObjectName(
            "nowPlayingLabel"
        )
        layout.addWidget(self.now_playing_label, 1)

        self.refresh_player_button = QPushButton("Refresh Player")
        self.refresh_player_button.setObjectName(
            "refreshPlayerButton"
        )
        self.refresh_player_button.clicked.connect(
            self.refresh_player_status
        )
        layout.addWidget(self.refresh_player_button)

        return group

    def _build_twitch_section(self) -> QGroupBox:
        group = QGroupBox("Twitch Channels")
        layout = QVBoxLayout(group)

        controls = QHBoxLayout()

        self.channel_input = QLineEdit()
        self.channel_input.setObjectName("channelInput")
        self.channel_input.setPlaceholderText(
            "Twitch channel name"
        )

        self.join_button = QPushButton("Join Channel")
        self.join_button.setObjectName("joinButton")
        self.join_button.clicked.connect(
            self.join_channel
        )

        self.leave_button = QPushButton("Leave Channel")
        self.leave_button.setObjectName("leaveButton")
        self.leave_button.clicked.connect(
            self.leave_channel
        )

        self.refresh_twitch_button = QPushButton("Refresh")
        self.refresh_twitch_button.setObjectName(
            "refreshTwitchButton"
        )
        self.refresh_twitch_button.clicked.connect(
            self.refresh_twitch_status
        )

        controls.addWidget(self.channel_input, 1)
        controls.addWidget(self.join_button)
        controls.addWidget(self.leave_button)
        controls.addWidget(self.refresh_twitch_button)

        layout.addLayout(controls)

        self.twitch_status_label = QLabel("Not checked")
        self.twitch_status_label.setObjectName(
            "twitchStatusLabel"
        )
        layout.addWidget(self.twitch_status_label)

        self.channel_list = QListWidget()
        self.channel_list.setObjectName("channelList")
        self.channel_list.setMaximumHeight(90)
        layout.addWidget(self.channel_list)

        return group

    def _build_queue_section(self) -> QGroupBox:
        group = QGroupBox("Queue")
        layout = QVBoxLayout(group)

        header = QHBoxLayout()

        title = QLabel("Current Bot Queue")
        title.setStyleSheet("font-weight: bold;")

        self.player_count_label = QLabel("Players Connected: 0")
        self.player_count_label.setObjectName("playerCountLabel")

        self.manager_count_label = QLabel("Managers Connected: 0 (including this instance)")
        self.manager_count_label.setObjectName("managerCountLabel")


        self.refresh_queue_button = QPushButton("Refresh Queue")
        self.refresh_queue_button.setObjectName(
            "refreshQueueButton"
        )
        self.refresh_queue_button.clicked.connect(
            self.refresh_queue
        )

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.player_count_label)
        header.addSpacing(12)
        header.addWidget(self.manager_count_label)
        header.addSpacing(12)
        header.addWidget(self.refresh_queue_button)

        layout.addLayout(header)

        controls = QHBoxLayout()

        self.queue_url_input = QLineEdit()
        self.queue_url_input.setObjectName("queueUrlInput")
        self.queue_url_input.setPlaceholderText(
            "YouTube or TikTok URL"
        )

        self.add_queue_button = QPushButton("Add to Queue")
        self.add_queue_button.setObjectName("addQueueButton")
        self.add_queue_button.clicked.connect(
            self.add_to_queue
        )

        self.add_next_button = QPushButton("Add Next")
        self.add_next_button.setObjectName("addNextButton")
        self.add_next_button.clicked.connect(
            self.add_next
        )

        self.remove_selected_button = QPushButton("Remove Selected")
        self.remove_selected_button.setObjectName(
            "removeSelectedButton"
        )
        self.remove_selected_button.clicked.connect(
            self.remove_selected
        )

        controls.addWidget(self.queue_url_input, 1)
        controls.addWidget(self.add_queue_button)
        controls.addWidget(self.add_next_button)
        controls.addWidget(self.remove_selected_button)

        layout.addLayout(controls)

        self.queue_table = QTableWidget(0, 5)
        self.queue_table.setObjectName("queueTable")
        self.queue_table.setHorizontalHeaderLabels(
            [
                "Position",
                "Title",
                "Platform",
                "Submitted By",
                "Status",
            ]
        )
        self.queue_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.queue_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.queue_table.horizontalHeader().setStretchLastSection(
            True
        )

        layout.addWidget(self.queue_table)

        return group

    def set_dark_mode(self, enabled: bool) -> None:
        if enabled:
            self.setStyleSheet(
                """
                QMainWindow,
                QWidget {
                    background-color: #202124;
                    color: #e8eaed;
                }

                QGroupBox {
                    border: 1px solid #5f6368;
                    border-radius: 5px;
                    margin-top: 8px;
                    padding-top: 8px;
                }

                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 8px;
                    padding: 0 4px;
                }

                QLineEdit,
                QListWidget,
                QTableWidget {
                    background-color: #292a2d;
                    color: #e8eaed;
                    border: 1px solid #5f6368;
                    selection-background-color: #3c4043;
                }

                QHeaderView::section {
                    background-color: #303134;
                    color: #e8eaed;
                    border: 1px solid #5f6368;
                    padding: 4px;
                }

                QPushButton {
                    background-color: #303134;
                    color: #e8eaed;
                    border: 1px solid #5f6368;
                    border-radius: 4px;
                    padding: 4px 8px;
                }

                QPushButton:hover {
                    background-color: #3c4043;
                }

                QPushButton:checked {
                    background-color: #4d5156;
                }
                """
            )
            self.status_label.setText("Dark mode enabled.")
        else:
            self.setStyleSheet("")
            self.status_label.setText("Dark mode disabled.")
    def _update_client(self) -> None:
        base_url = self.bot_url_input.text().strip()

        self.bot_client = BotClient(base_url)

        if (
            hasattr(self, "queue_event_listener")
            and self.queue_event_listener.url
            != websocket_events_url(base_url)
        ):
            self.queue_event_listener.stop()
            self.queue_event_listener = QueueEventListener(
                base_url,
                self.queue_refresh_requested.emit,
            )
            self.queue_event_listener.start()

    def _stop_background_services(self) -> None:
        self.queue_event_listener.stop()

    def closeEvent(self, event) -> None:
        self._stop_background_services()
        super().closeEvent(event)

    def _show_error(self, exc: Exception) -> None:
        self.status_label.setText(str(exc))

    def test_connection(self) -> None:
        self._update_client()

        try:
            result = self.bot_client.health()
        except BotClientError as exc:
            self.bot_status_label.setText("Offline")
            self._show_error(exc)
            return

        version = result.get("version", "unknown")
        self.bot_status_label.setText(
            f"Connected - Bot {version}"
        )
        self.status_label.setText("Bot connection successful.")

    def refresh_player_status(self) -> None:
        self._update_client()

        try:
            presence = self.bot_client.player_status()
            playback = self.bot_client.player_state()
        except BotClientError as exc:
            self.player_status_label.setText("Offline")
            self.playback_status_label.setText("Unknown")
            self.now_playing_label.setText("None")
            self._show_error(exc)
            return

        if presence.get("active"):
            self.player_status_label.setText("Active")
        else:
            self.player_status_label.setText("Offline")

        state = playback.get("state", "unknown")

        if state == "playing":
            self.playback_status_label.setText("Playing")
        elif state == "idle":
            self.playback_status_label.setText("Idle")
        else:
            self.playback_status_label.setText(
                str(state).title()
            )

        item = playback.get("item")

        if item:
            title = item.get("title") or item.get("url") or "Untitled video"
            self.now_playing_label.setText(str(title))
        else:
            self.now_playing_label.setText("None")

        self.status_label.setText("Player status refreshed.")


    def refresh_twitch_status(self) -> None:
        self._update_client()

        try:
            result = self.bot_client.twitch_status()
        except BotClientError as exc:
            self._show_error(exc)
            return

        channels = result.get("channels", [])

        self.channel_list.clear()
        self.channel_list.addItems(channels)

        if result.get("connected"):
            self.twitch_status_label.setText(
                f"Active - {{len(channels)}} channel(s)"
            )
        else:
            self.twitch_status_label.setText("Inactive")

        self.status_label.setText(
            "Twitch status refreshed."
        )

    def join_channel(self) -> None:
        channel = self.channel_input.text().strip()

        if not channel:
            self.status_label.setText(
                "Enter a Twitch channel name."
            )
            return

        self._update_client()

        try:
            result = self.bot_client.join_twitch_channel(
                channel
            )
        except BotClientError as exc:
            self._show_error(exc)
            return

        self.channel_input.clear()
        self._apply_twitch_result(result)

    def leave_channel(self) -> None:
        channel = self.channel_input.text().strip()

        if not channel:
            selected = self.channel_list.currentItem()

            if selected is not None:
                channel = selected.text()

        if not channel:
            self.status_label.setText(
                "Enter or select a Twitch channel."
            )
            return

        self._update_client()

        try:
            result = self.bot_client.leave_twitch_channel(
                channel
            )
        except BotClientError as exc:
            self._show_error(exc)
            return

        self.channel_input.clear()
        self._apply_twitch_result(result)

    def _apply_twitch_result(self, result: dict) -> None:
        channels = result.get("channels", [])

        self.channel_list.clear()
        self.channel_list.addItems(channels)

        if channels:
            self.twitch_status_label.setText(
                f"Active - {{len(channels)}} channel(s)"
            )
        else:
            self.twitch_status_label.setText("Inactive")

        self.status_label.setText(
            result.get("status", "Twitch state updated.")
        )

    def add_to_queue(self) -> None:
        url = self.queue_url_input.text().strip()

        if not url:
            self.status_label.setText("Enter a video URL.")
            return

        self._update_client()

        try:
            self.bot_client.add_queue_item(url)
        except BotClientError as exc:
            self._show_error(exc)
            return

        self.queue_url_input.clear()
        self.refresh_queue()
        self.status_label.setText("Video added to queue.")

    def add_next(self) -> None:
        url = self.queue_url_input.text().strip()

        if not url:
            self.status_label.setText("Enter a video URL.")
            return

        self._update_client()

        try:
            result = self.bot_client.add_queue_item(url)
            item_id = result.get("id")

            if item_id is None:
                raise BotClientError(
                    "Bot did not return a queue item ID"
                )

            self.bot_client.move_queue_item(
                int(item_id),
                1,
            )
        except BotClientError as exc:
            self._show_error(exc)
            return

        self.queue_url_input.clear()
        self.refresh_queue()
        self.status_label.setText("Video added next.")

    def remove_selected(self) -> None:
        row = self.queue_table.currentRow()

        if row < 0:
            self.status_label.setText("Select a queue item first.")
            return

        first_item = self.queue_table.item(row, 0)

        if first_item is None:
            self.status_label.setText("Selected queue item is invalid.")
            return

        item_id = first_item.data(Qt.ItemDataRole.UserRole)

        if item_id is None:
            self.status_label.setText("Selected queue item has no ID.")
            return

        self._update_client()

        try:
            self.bot_client.remove_queue_item(int(item_id))
        except BotClientError as exc:
            self._show_error(exc)
            return

        self.refresh_queue()
        self.status_label.setText("Queue item removed.")


    def _update_presence_counts(self, event: dict) -> None:
        self.player_count_label.setText(
            f"Players Connected: {event.get('player_count', 0)}"
        )
        self.manager_count_label.setText(
            f"Managers Connected: {event.get('manager_count', 0)} (including this instance)"
        )


    def refresh_queue(self, event: dict | None = None) -> None:
        if event:
            event_type = event.get("type")

            if event_type == "connected":
                self._update_presence_counts(event)

                snapshot = event.get("snapshot")
                if snapshot is not None:
                    self._apply_queue_snapshot(snapshot)
                    return
            elif event_type == "manager_presence_changed":
                self.manager_count_label.setText(
                    f"Managers Connected: {event.get('manager_count', 0)} (including this instance)"
                )
            elif event_type == "player_presence_changed":
                self.player_count_label.setText(
                    f"Players Connected: {event.get('player_count', 0)}"
                )

            if event_type in {
                "manager_presence_changed",
                "player_presence_changed",
            }:
                return

            if event_type == "queue_changed":
                snapshot = event.get("snapshot")

                if snapshot is not None:
                    self._apply_queue_snapshot(snapshot)
                    return

        self._update_client()

        try:
            items = self.bot_client.queue()
        except BotClientError as exc:
            self._show_error(exc)
            return

        self._render_queue(items)

    def _apply_queue_snapshot(self, snapshot: dict) -> None:
        items = snapshot.get("queued", [])
        self._render_queue(items)

    def _render_queue(self, items: list[dict]) -> None:
        self.queue_table.setRowCount(len(items))

        for row, item in enumerate(items):
            values = [
                item.get("position"),
                item.get("title") or item.get("url"),
                item.get("platform"),
                item.get("submitted_by"),
                item.get("status"),
            ]

            for column, value in enumerate(values):
                table_item = QTableWidgetItem(
                    "" if value is None else str(value)
                )
                table_item.setTextAlignment(
                    Qt.AlignmentFlag.AlignVCenter
                    | Qt.AlignmentFlag.AlignLeft
                )

                if column == 0:
                    table_item.setData(
                        Qt.ItemDataRole.UserRole,
                        item.get("id"),
                    )

                self.queue_table.setItem(
                    row,
                    column,
                    table_item,
                )

        self.queue_table.resizeColumnsToContents()
        self.status_label.setText(
            f"Queue synchronized - {len(items)} item(s)."
        )
