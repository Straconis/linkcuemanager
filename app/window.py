from PySide6.QtCore import Qt
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


class ManagerWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.resize(900, 650)

        self.bot_client = BotClient(DEFAULT_BOT_URL)

        root = QWidget()
        self.setCentralWidget(root)

        layout = QVBoxLayout(root)

        layout.addWidget(self._build_bot_section())
        layout.addWidget(self._build_twitch_section())
        layout.addWidget(self._build_queue_section(), 1)

        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("statusLabel")
        layout.addWidget(self.status_label)

    def _build_bot_section(self) -> QGroupBox:
        group = QGroupBox("LinkCue Bot")
        form = QFormLayout(group)

        url_row = QHBoxLayout()

        self.bot_url_input = QLineEdit(DEFAULT_BOT_URL)
        self.bot_url_input.setObjectName("botUrlInput")

        self.test_connection_button = QPushButton("Test Connection")
        self.test_connection_button.setObjectName(
            "testConnectionButton"
        )
        self.test_connection_button.clicked.connect(
            self.test_connection
        )

        url_row.addWidget(self.bot_url_input, 1)
        url_row.addWidget(self.test_connection_button)

        form.addRow("Bot URL:", url_row)

        self.bot_status_label = QLabel("Not checked")
        self.bot_status_label.setObjectName("botStatusLabel")
        form.addRow("Status:", self.bot_status_label)

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
        layout.addWidget(self.channel_list)

        return group

    def _build_queue_section(self) -> QGroupBox:
        group = QGroupBox("Queue")
        layout = QVBoxLayout(group)

        header = QHBoxLayout()

        title = QLabel("Current Bot Queue")
        title.setStyleSheet("font-weight: bold;")

        self.refresh_queue_button = QPushButton("Refresh Queue")
        self.refresh_queue_button.setObjectName(
            "refreshQueueButton"
        )
        self.refresh_queue_button.clicked.connect(
            self.refresh_queue
        )

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.refresh_queue_button)

        layout.addLayout(header)

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

    def _update_client(self) -> None:
        self.bot_client = BotClient(
            self.bot_url_input.text().strip()
        )

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
            f"Connected — Bot {version}"
        )
        self.status_label.setText("Bot connection successful.")

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
                f"Active — {len(channels)} channel(s)"
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
                f"Active — {len(channels)} channel(s)"
            )
        else:
            self.twitch_status_label.setText("Inactive")

        self.status_label.setText(
            result.get("status", "Twitch state updated.")
        )

    def refresh_queue(self) -> None:
        self._update_client()

        try:
            items = self.bot_client.queue()
        except BotClientError as exc:
            self._show_error(exc)
            return

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
                self.queue_table.setItem(
                    row,
                    column,
                    table_item,
                )

        self.queue_table.resizeColumnsToContents()
        self.status_label.setText(
            f"Queue refreshed — {len(items)} item(s)."
        )
