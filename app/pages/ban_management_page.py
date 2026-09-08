from collections.abc import Callable

from PySide6.QtCore import QTimer, Qt
from app.pages.manager_page import ToggleSwitch

from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class BanManagementPage(QWidget):
    def __init__(
        self,
        refresh_callback: Callable[[], None],
        add_creator_callback: Callable[[], None],
        creator_state_callback: Callable[[], None],
        creator_audit_callback: Callable[[], None],
        add_video_callback: Callable[[], None],
        video_state_callback: Callable[[], None],
        video_audit_callback: Callable[[], None],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 12)
        layout.setSpacing(12)

        top_controls = QHBoxLayout()

        self.refresh_button = QPushButton("Refresh Bans")
        self.refresh_button.setObjectName(
            "refreshBansButton"
        )
        self.refresh_button.clicked.connect(
            refresh_callback
        )
        top_controls.addWidget(self.refresh_button)

        self.full_history_label = QLabel(
            "Show Full Ban History:"
        )
        self.full_history_label.setObjectName(
            "fullBanHistoryLabel"
        )
        top_controls.addWidget(
            self.full_history_label
        )

        self.include_inactive_toggle = ToggleSwitch()
        self.include_inactive_toggle.setObjectName(
            "includeInactiveBansToggle"
        )
        self.include_inactive_toggle.setAccessibleName(
            "Show Full Ban History"
        )
        self.include_inactive_toggle.setChecked(True)
        self.include_inactive_toggle.toggled.connect(
            lambda checked: QTimer.singleShot(
                0,
                refresh_callback,
            )
        )
        top_controls.addWidget(
            self.include_inactive_toggle
        )

        top_controls.addStretch()
        layout.addLayout(top_controls)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("banManagementTabs")

        self.creator_tab = QWidget()
        self.creator_tab.setObjectName(
            "creatorBanTab"
        )
        creator_layout = QVBoxLayout(
            self.creator_tab
        )
        creator_layout.setContentsMargins(
            8,
            12,
            8,
            8,
        )
        creator_layout.setSpacing(10)

        creator_controls = QHBoxLayout()

        self.add_creator_button = QPushButton(
            "Add Creator Ban"
        )
        self.add_creator_button.setObjectName(
            "addCreatorBanButton"
        )
        self.add_creator_button.clicked.connect(
            add_creator_callback
        )
        creator_controls.addWidget(
            self.add_creator_button
        )

        self.creator_state_button = QPushButton(
            "Unban Selected"
        )
        self.creator_state_button.setObjectName(
            "creatorBanStateButton"
        )
        self.creator_state_button.clicked.connect(
            creator_state_callback
        )
        creator_controls.addWidget(
            self.creator_state_button
        )

        self.creator_audit_button = QPushButton(
            "Audit History"
        )
        self.creator_audit_button.setObjectName(
            "creatorBanAuditButton"
        )
        self.creator_audit_button.clicked.connect(
            creator_audit_callback
        )
        creator_controls.addWidget(
            self.creator_audit_button
        )

        creator_controls.addStretch()
        creator_layout.addLayout(creator_controls)

        self.creator_table = QTableWidget(0, 8)
        self.creator_table.setObjectName(
            "creatorBanTable"
        )
        self.creator_table.setHorizontalHeaderLabels(
            [
                "Platform",
                "Channel / Creator",
                "Creator ID",
                "Reason",
                "Banned By",
                "Status",
                "Created",
                "Updated",
            ]
        )
        self._configure_table(
            self.creator_table,
            stretch_column=3,
        )
        self.creator_table.itemSelectionChanged.connect(
            self._update_creator_state_button
        )
        creator_layout.addWidget(
            self.creator_table
        )

        self.tabs.addTab(
            self.creator_tab,
            "Creators / Channels",
        )

        self.video_tab = QWidget()
        self.video_tab.setObjectName(
            "videoBanTab"
        )
        video_layout = QVBoxLayout(
            self.video_tab
        )
        video_layout.setContentsMargins(
            8,
            12,
            8,
            8,
        )
        video_layout.setSpacing(10)

        video_controls = QHBoxLayout()

        self.add_video_button = QPushButton(
            "Add Video Ban"
        )
        self.add_video_button.setObjectName(
            "addVideoBanButton"
        )
        self.add_video_button.clicked.connect(
            add_video_callback
        )
        video_controls.addWidget(
            self.add_video_button
        )

        self.video_state_button = QPushButton(
            "Unban Selected"
        )
        self.video_state_button.setObjectName(
            "videoBanStateButton"
        )
        self.video_state_button.clicked.connect(
            video_state_callback
        )
        video_controls.addWidget(
            self.video_state_button
        )

        self.video_audit_button = QPushButton(
            "Audit History"
        )
        self.video_audit_button.setObjectName(
            "videoBanAuditButton"
        )
        self.video_audit_button.clicked.connect(
            video_audit_callback
        )
        video_controls.addWidget(
            self.video_audit_button
        )

        video_controls.addStretch()
        video_layout.addLayout(video_controls)

        self.video_table = QTableWidget(0, 9)
        self.video_table.setObjectName(
            "videoBanTable"
        )
        self.video_table.setHorizontalHeaderLabels(
            [
                "Platform",
                "Title",
                "Video ID",
                "URL",
                "Reason",
                "Banned By",
                "Status",
                "Created",
                "Updated",
            ]
        )
        self._configure_table(
            self.video_table,
            stretch_column=4,
        )
        self.video_table.itemSelectionChanged.connect(
            self._update_video_state_button
        )
        video_layout.addWidget(
            self.video_table
        )

        self.tabs.addTab(
            self.video_tab,
            "Individual Videos",
        )

        layout.addWidget(self.tabs, 1)

        self._update_creator_state_button()
        self._update_video_state_button()

    @staticmethod
    def _configure_table(
        table: QTableWidget,
        *,
        stretch_column: int,
    ) -> None:
        table.verticalHeader().hide()
        table.setAlternatingRowColors(True)
        table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        header = table.horizontalHeader()

        for column in range(table.columnCount()):
            mode = (
                QHeaderView.ResizeMode.Stretch
                if column == stretch_column
                else QHeaderView.ResizeMode.ResizeToContents
            )
            header.setSectionResizeMode(
                column,
                mode,
            )

    @staticmethod
    def _text(
        value,
        *,
        fallback: str = "Unknown",
    ) -> str:
        normalized = str(
            value
            if value is not None
            else ""
        ).strip()

        return normalized or fallback

    @classmethod
    def _platform_text(
        cls,
        value,
    ) -> str:
        normalized = cls._text(
            value
        ).casefold()

        names = {
            "youtube": "YouTube",
            "tiktok": "TikTok",
        }

        return names.get(
            normalized,
            cls._text(value).title(),
        )

    @staticmethod
    def _set_row(
        table: QTableWidget,
        row_index: int,
        *,
        ban_id: int,
        active: bool,
        values: list[str],
    ) -> None:
        for column_index, value in enumerate(values):
            item = QTableWidgetItem(value)

            if column_index == 0:
                item.setData(
                    Qt.ItemDataRole.UserRole,
                    ban_id,
                )
                item.setData(
                    Qt.ItemDataRole.UserRole + 1,
                    active,
                )

            table.setItem(
                row_index,
                column_index,
                item,
            )

    @staticmethod
    def _selected_ban(
        table: QTableWidget,
    ) -> tuple[int, bool] | None:
        rows = (
            table.selectionModel()
            .selectedRows()
        )

        if not rows:
            return None

        item = table.item(
            rows[0].row(),
            0,
        )

        if item is None:
            return None

        ban_id = item.data(
            Qt.ItemDataRole.UserRole
        )
        active = item.data(
            Qt.ItemDataRole.UserRole + 1
        )

        if ban_id is None:
            return None

        return int(ban_id), bool(active)

    def selected_creator_ban(
        self,
    ) -> tuple[int, bool] | None:
        return self._selected_ban(
            self.creator_table
        )

    def selected_video_ban(
        self,
    ) -> tuple[int, bool] | None:
        return self._selected_ban(
            self.video_table
        )

    def _update_creator_state_button(
        self,
    ) -> None:
        selected = self.selected_creator_ban()

        self.creator_state_button.setText(
            "Unban Selected"
            if selected is None or selected[1]
            else "Re-ban Selected"
        )

        has_selection = selected is not None
        self.creator_state_button.setEnabled(
            has_selection
        )
        self.creator_audit_button.setEnabled(
            has_selection
        )

    def _update_video_state_button(
        self,
    ) -> None:
        selected = self.selected_video_ban()

        self.video_state_button.setText(
            "Unban Selected"
            if selected is None or selected[1]
            else "Re-ban Selected"
        )

        has_selection = selected is not None
        self.video_state_button.setEnabled(
            has_selection
        )
        self.video_audit_button.setEnabled(
            has_selection
        )

    def apply_bans(
        self,
        *,
        creators: list[dict],
        videos: list[dict],
    ) -> None:
        self.creator_table.clearContents()
        self.creator_table.setRowCount(
            len(creators)
        )

        for row_index, ban in enumerate(creators):
            active = bool(ban.get("active"))

            self._set_row(
                self.creator_table,
                row_index,
                ban_id=int(ban["id"]),
                active=active,
                values=[
                    self._platform_text(
                        ban.get("platform")
                    ),
                    self._text(
                        ban.get("video_channel")
                    ),
                    self._text(
                        ban.get("video_creator_id")
                    ),
                    self._text(
                        ban.get("reason"),
                        fallback="None",
                    ),
                    self._text(
                        ban.get("created_by")
                    ),
                    (
                        "Active"
                        if active
                        else "Inactive"
                    ),
                    self._text(
                        ban.get("created_at")
                    ),
                    self._text(
                        ban.get("updated_at")
                    ),
                ],
            )

        self.video_table.clearContents()
        self.video_table.setRowCount(
            len(videos)
        )

        for row_index, ban in enumerate(videos):
            active = bool(ban.get("active"))

            self._set_row(
                self.video_table,
                row_index,
                ban_id=int(ban["id"]),
                active=active,
                values=[
                    self._platform_text(
                        ban.get("platform")
                    ),
                    self._text(
                        ban.get("title")
                    ),
                    self._text(
                        ban.get("video_platform_id")
                    ),
                    self._text(
                        ban.get("url")
                    ),
                    self._text(
                        ban.get("reason"),
                        fallback="None",
                    ),
                    self._text(
                        ban.get("created_by")
                    ),
                    (
                        "Active"
                        if active
                        else "Inactive"
                    ),
                    self._text(
                        ban.get("created_at")
                    ),
                    self._text(
                        ban.get("updated_at")
                    ),
                ],
            )

        self._update_creator_state_button()
        self._update_video_state_button()

    def show_unavailable(self) -> None:
        self.creator_table.setRowCount(0)
        self.video_table.setRowCount(0)
        self._update_creator_state_button()
        self._update_video_state_button()
