from collections.abc import Callable

from PySide6.QtWidgets import (
    QAbstractItemView,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class SoftwarePage(QWidget):
    def __init__(
        self,
        refresh_callback: Callable[[], None],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 12)
        layout.setSpacing(16)

        self.bot_group = QGroupBox("LinkCue Bot")
        bot_layout = QHBoxLayout(self.bot_group)

        bot_layout.addWidget(QLabel("Status:"))
        self.bot_status_label = QLabel("Not checked")
        self.bot_status_label.setObjectName(
            "softwareBotStatusLabel"
        )
        bot_layout.addWidget(self.bot_status_label)

        bot_layout.addSpacing(24)
        bot_layout.addWidget(QLabel("Version:"))
        self.bot_version_label = QLabel("Unknown")
        self.bot_version_label.setObjectName(
            "softwareBotVersionLabel"
        )
        bot_layout.addWidget(self.bot_version_label)

        bot_layout.addSpacing(24)
        bot_layout.addWidget(QLabel("API Version:"))
        self.bot_api_version_label = QLabel("Unknown")
        self.bot_api_version_label.setObjectName(
            "softwareBotApiVersionLabel"
        )
        bot_layout.addWidget(self.bot_api_version_label)

        bot_layout.addStretch()

        self.refresh_button = QPushButton("Refresh Software")
        self.refresh_button.setObjectName(
            "refreshSoftwareButton"
        )
        self.refresh_button.clicked.connect(
            refresh_callback
        )
        bot_layout.addWidget(self.refresh_button)

        layout.addWidget(self.bot_group)

        self.manager_group = QGroupBox(
            "Connected Managers"
        )
        manager_layout = QVBoxLayout(
            self.manager_group
        )

        self.manager_table = QTableWidget(0, 3)
        self.manager_table.setObjectName(
            "softwareManagerTable"
        )
        self.manager_table.setHorizontalHeaderLabels(
            [
                "Username",
                "Version",
                "Client ID",
            ]
        )
        self._configure_table(
            self.manager_table,
            stretch_column=2,
        )
        self.manager_table.setMinimumHeight(150)
        manager_layout.addWidget(self.manager_table)

        layout.addWidget(self.manager_group)

        self.player_group = QGroupBox(
            "Connected Players"
        )
        player_layout = QVBoxLayout(
            self.player_group
        )

        self.player_table = QTableWidget(0, 5)
        self.player_table.setObjectName(
            "softwarePlayerTable"
        )
        self.player_table.setHorizontalHeaderLabels(
            [
                "Streamer",
                "Version",
                "Client ID",
                "Playback",
                "Now Playing",
            ]
        )
        self._configure_table(
            self.player_table,
            stretch_column=4,
        )
        self.player_table.setMinimumHeight(170)
        player_layout.addWidget(self.player_table)

        layout.addWidget(self.player_group)
        layout.addStretch()

    @staticmethod
    def _configure_table(
        table: QTableWidget,
        *,
        stretch_column: int,
    ) -> None:
        table.verticalHeader().hide()
        table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        header = table.horizontalHeader()

        for column in range(table.columnCount()):
            resize_mode = (
                QHeaderView.ResizeMode.Stretch
                if column == stretch_column
                else QHeaderView.ResizeMode.ResizeToContents
            )
            header.setSectionResizeMode(
                column,
                resize_mode,
            )

    @staticmethod
    def _display_text(value) -> str:
        normalized = str(value or "").strip()
        return normalized or "Unknown"

    @staticmethod
    def _set_rows(
        table: QTableWidget,
        rows: list[list[str]],
    ) -> None:
        table.clearContents()
        table.setRowCount(len(rows))

        for row_index, values in enumerate(rows):
            for column_index, value in enumerate(values):
                table.setItem(
                    row_index,
                    column_index,
                    QTableWidgetItem(value),
                )

    def show_unavailable(self) -> None:
        self.bot_status_label.setText("Offline")
        self.bot_version_label.setText("Unknown")
        self.bot_api_version_label.setText("Unknown")
        self.manager_table.setRowCount(0)
        self.player_table.setRowCount(0)

    def apply_status(
        self,
        software: dict,
        playback: dict,
    ) -> None:
        bot = software.get("bot") or {}

        self.bot_status_label.setText(
            self._display_text(
                bot.get("status")
            ).title()
        )
        self.bot_version_label.setText(
            self._display_text(
                bot.get("version")
            )
        )
        self.bot_api_version_label.setText(
            self._display_text(
                bot.get("api_version")
            )
        )

        managers = software.get("managers") or []
        manager_rows = [
            [
                self._display_text(
                    manager.get("display_name")
                ),
                self._display_text(
                    manager.get("version")
                ),
                self._display_text(
                    manager.get("client_id")
                ),
            ]
            for manager in managers
        ]
        self._set_rows(
            self.manager_table,
            manager_rows,
        )

        state = self._display_text(
            playback.get("state")
        ).title()
        item = playback.get("item") or {}
        now_playing = (
            item.get("title")
            or item.get("url")
            or "None"
        )

        players = software.get("players") or []
        player_rows = [
            [
                self._display_text(
                    player.get("display_name")
                ),
                self._display_text(
                    player.get("version")
                ),
                self._display_text(
                    player.get("client_id")
                ),
                state,
                str(now_playing),
            ]
            for player in players
        ]
        self._set_rows(
            self.player_table,
            player_rows,
        )
