from collections.abc import Callable

from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class TwitchPage(QWidget):
    def __init__(
        self,
        join_callback: Callable[[], None],
        leave_callback: Callable[[], None],
        refresh_callback: Callable[[], None],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 12)
        layout.setSpacing(10)

        group = QGroupBox("Twitch Channels")
        group_layout = QVBoxLayout(group)

        controls = QHBoxLayout()

        self.channel_input = QLineEdit()
        self.channel_input.setObjectName("channelInput")
        self.channel_input.setPlaceholderText(
            "Twitch channel name"
        )

        self.join_button = QPushButton("Join Channel")
        self.join_button.setObjectName("joinButton")
        self.join_button.clicked.connect(
            join_callback
        )

        self.leave_button = QPushButton("Leave Channel")
        self.leave_button.setObjectName("leaveButton")
        self.leave_button.clicked.connect(
            leave_callback
        )

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName(
            "refreshTwitchButton"
        )
        self.refresh_button.clicked.connect(
            refresh_callback
        )

        controls.addWidget(self.channel_input, 1)
        controls.addWidget(self.join_button)
        controls.addWidget(self.leave_button)
        controls.addWidget(self.refresh_button)

        group_layout.addLayout(controls)

        self.status_label = QLabel("Not checked")
        self.status_label.setObjectName(
            "twitchStatusLabel"
        )
        group_layout.addWidget(self.status_label)

        self.channel_list = QListWidget()
        self.channel_list.setObjectName("channelList")
        self.channel_list.setMaximumHeight(90)
        group_layout.addWidget(self.channel_list)

        layout.addWidget(group)
        layout.addStretch()

    def entered_channel(self) -> str:
        return self.channel_input.text().strip()

    def set_channel(self, channel: str) -> None:
        self.channel_input.setText(channel)

    def selected_channel(self) -> str:
        selected = self.channel_list.currentItem()

        if selected is None:
            return ""

        return selected.text()

    def clear_channel_input(self) -> None:
        self.channel_input.clear()

    def apply_status(
        self,
        result: dict,
        use_connected_flag: bool = False,
    ) -> None:
        channels = result.get("channels", [])

        self.channel_list.clear()
        self.channel_list.addItems(channels)

        if use_connected_flag:
            active = bool(result.get("connected"))
        else:
            active = bool(channels)

        if active:
            self.status_label.setText(
                f"Active - {len(channels)} channel(s)"
            )
        else:
            self.status_label.setText("Inactive")
