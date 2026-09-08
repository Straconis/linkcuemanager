from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


def _optional_text(value: str) -> str | None:
    normalized = value.strip()
    return normalized or None


def _configure_platform_input(
    input_widget: QComboBox,
) -> None:
    input_widget.addItem(
        "YouTube",
        "youtube",
    )
    input_widget.addItem(
        "TikTok",
        "tiktok",
    )


class CreatorBanDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Add Creator Ban")
        self.setModal(True)
        self.setMinimumWidth(480)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        explanation = QLabel(
            "Block every submission from a creator or "
            "channel on the selected platform."
        )
        explanation.setWordWrap(True)
        layout.addWidget(explanation)

        form = QFormLayout()
        form.setSpacing(10)

        self.platform_input = QComboBox()
        self.platform_input.setObjectName(
            "creatorBanPlatformInput"
        )
        _configure_platform_input(
            self.platform_input
        )
        form.addRow(
            "Platform:",
            self.platform_input,
        )

        self.channel_input = QLineEdit()
        self.channel_input.setObjectName(
            "creatorBanChannelInput"
        )
        self.channel_input.setPlaceholderText(
            "Creator or channel name"
        )
        form.addRow(
            "Channel / Creator:",
            self.channel_input,
        )

        self.creator_id_input = QLineEdit()
        self.creator_id_input.setObjectName(
            "creatorBanIdInput"
        )
        self.creator_id_input.setPlaceholderText(
            "Stable platform creator ID (optional)"
        )
        form.addRow(
            "Creator ID:",
            self.creator_id_input,
        )

        self.reason_input = QLineEdit()
        self.reason_input.setObjectName(
            "creatorBanReasonInput"
        )
        self.reason_input.setPlaceholderText(
            "Reason for ban (optional)"
        )
        form.addRow(
            "Reason:",
            self.reason_input,
        )

        layout.addLayout(form)

        buttons = QHBoxLayout()
        buttons.addStretch()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(
            self.reject
        )
        buttons.addWidget(self.cancel_button)

        self.add_button = QPushButton("Add Ban")
        self.add_button.setDefault(True)
        self.add_button.clicked.connect(
            self._validate_and_accept
        )
        buttons.addWidget(self.add_button)

        layout.addLayout(buttons)

    def values(self) -> dict:
        return {
            "platform": (
                self.platform_input.currentData()
            ),
            "video_channel": (
                self.channel_input.text().strip()
            ),
            "video_creator_id": _optional_text(
                self.creator_id_input.text()
            ),
            "reason": _optional_text(
                self.reason_input.text()
            ),
        }

    def _validate_and_accept(self) -> None:
        if not self.channel_input.text().strip():
            QMessageBox.warning(
                self,
                "Creator Required",
                "Enter a creator or channel name.",
            )
            self.channel_input.setFocus()
            return

        self.accept()


class VideoBanDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Add Video Ban")
        self.setModal(True)
        self.setMinimumWidth(520)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        explanation = QLabel(
            "Block one specific video using its stable "
            "platform video ID."
        )
        explanation.setWordWrap(True)
        layout.addWidget(explanation)

        form = QFormLayout()
        form.setSpacing(10)

        self.platform_input = QComboBox()
        self.platform_input.setObjectName(
            "videoBanPlatformInput"
        )
        _configure_platform_input(
            self.platform_input
        )
        form.addRow(
            "Platform:",
            self.platform_input,
        )

        self.video_id_input = QLineEdit()
        self.video_id_input.setObjectName(
            "videoBanIdInput"
        )
        self.video_id_input.setPlaceholderText(
            "Stable platform video ID"
        )
        form.addRow(
            "Video ID:",
            self.video_id_input,
        )

        self.title_input = QLineEdit()
        self.title_input.setObjectName(
            "videoBanTitleInput"
        )
        self.title_input.setPlaceholderText(
            "Video title (optional)"
        )
        form.addRow(
            "Title:",
            self.title_input,
        )

        self.url_input = QLineEdit()
        self.url_input.setObjectName(
            "videoBanUrlInput"
        )
        self.url_input.setPlaceholderText(
            "Video URL (optional)"
        )
        form.addRow(
            "URL:",
            self.url_input,
        )

        self.reason_input = QLineEdit()
        self.reason_input.setObjectName(
            "videoBanReasonInput"
        )
        self.reason_input.setPlaceholderText(
            "Reason for ban (optional)"
        )
        form.addRow(
            "Reason:",
            self.reason_input,
        )

        layout.addLayout(form)

        buttons = QHBoxLayout()
        buttons.addStretch()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(
            self.reject
        )
        buttons.addWidget(self.cancel_button)

        self.add_button = QPushButton("Add Ban")
        self.add_button.setDefault(True)
        self.add_button.clicked.connect(
            self._validate_and_accept
        )
        buttons.addWidget(self.add_button)

        layout.addLayout(buttons)

    def values(self) -> dict:
        return {
            "platform": (
                self.platform_input.currentData()
            ),
            "video_platform_id": (
                self.video_id_input.text().strip()
            ),
            "title": _optional_text(
                self.title_input.text()
            ),
            "url": _optional_text(
                self.url_input.text()
            ),
            "reason": _optional_text(
                self.reason_input.text()
            ),
        }

    def _validate_and_accept(self) -> None:
        if not self.video_id_input.text().strip():
            QMessageBox.warning(
                self,
                "Video ID Required",
                "Enter the stable platform video ID.",
            )
            self.video_id_input.setFocus()
            return

        self.accept()


class AuditHistoryDialog(QDialog):
    def __init__(
        self,
        title: str,
        entries: list[dict],
        parent=None,
    ):
        super().__init__(parent)

        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(760, 400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        self.audit_table = QTableWidget(
            len(entries),
            4,
        )
        self.audit_table.setObjectName(
            "banAuditTable"
        )
        self.audit_table.setHorizontalHeaderLabels(
            [
                "Action",
                "Actor",
                "Reason",
                "Date",
            ]
        )
        self.audit_table.verticalHeader().hide()
        self.audit_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.audit_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        header = self.audit_table.horizontalHeader()
        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.Stretch,
        )
        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        for row_index, entry in enumerate(entries):
            values = [
                str(
                    entry.get("action") or "Unknown"
                ).strip().title(),
                str(
                    entry.get("actor") or "Unknown"
                ).strip(),
                str(
                    entry.get("reason") or "None"
                ).strip(),
                str(
                    entry.get("created_at") or "Unknown"
                ).strip(),
            ]

            for column_index, value in enumerate(values):
                self.audit_table.setItem(
                    row_index,
                    column_index,
                    QTableWidgetItem(value),
                )

        layout.addWidget(self.audit_table, 1)

        buttons = QHBoxLayout()
        buttons.addStretch()

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(
            self.accept
        )
        buttons.addWidget(self.close_button)

        layout.addLayout(buttons)
