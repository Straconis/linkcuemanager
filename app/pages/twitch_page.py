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
        authorize_callback: Callable[[], None],
        connect_callback: Callable[[], None],
        disconnect_callback: Callable[[], None],
        join_callback: Callable[[], None],
        leave_callback: Callable[[], None],
        refresh_callback: Callable[[], None],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 12)
        layout.setSpacing(10)

        auth_group = QGroupBox("Twitch Authentication")
        auth_layout = QVBoxLayout(auth_group)

        self.authorization_label = QLabel(
            "Authorization: Not Authorized"
        )
        self.authorization_label.setObjectName(
            "twitchAuthorizationLabel"
        )

        self.connection_label = QLabel(
            "Connection: Disconnected"
        )
        self.connection_label.setObjectName(
            "twitchConnectionLabel"
        )

        auth_controls = QHBoxLayout()

        self.authorize_button = QPushButton(
            "Authorize Twitch"
        )
        self.authorize_button.setObjectName(
            "authorizeTwitchButton"
        )
        self.authorize_button.clicked.connect(
            authorize_callback
        )

        self.connect_button = QPushButton(
            "Connect to Twitch"
        )
        self.connect_button.setObjectName(
            "connectTwitchButton"
        )
        self.connect_button.clicked.connect(
            connect_callback
        )

        self.disconnect_button = QPushButton(
            "Disconnect from Twitch"
        )
        self.disconnect_button.setObjectName(
            "disconnectTwitchButton"
        )
        self.disconnect_button.clicked.connect(
            disconnect_callback
        )

        auth_controls.addWidget(self.authorize_button)
        auth_controls.addWidget(self.connect_button)
        auth_controls.addWidget(self.disconnect_button)
        auth_controls.addStretch()

        auth_layout.addWidget(self.authorization_label)
        auth_layout.addWidget(self.connection_label)
        auth_layout.addLayout(auth_controls)

        layout.addWidget(auth_group)

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

    def apply_auth_status(
        self,
        result: dict,
    ) -> None:
        authorized = bool(result.get("authorized"))
        login = result.get("login")

        if authorized:
            if login:
                self.authorization_label.setText(
                    f"Authorization: Authorized as {login}"
                )
            else:
                self.authorization_label.setText(
                    "Authorization: Authorized"
                )
        else:
            self.authorization_label.setText(
                "Authorization: Not Authorized"
            )

    def apply_status(
        self,
        result: dict,
        use_connected_flag: bool = False,
    ) -> None:
        channels = result.get("channels", [])

        self.channel_list.clear()
        self.channel_list.addItems(channels)

        connected = bool(result.get("connected"))

        if connected:
            self.connection_label.setText(
                "Connection: Connected"
            )
        else:
            self.connection_label.setText(
                "Connection: Disconnected"
            )

        if "authorized" in result:
            self.apply_auth_status(result)

        if use_connected_flag:
            active = connected
        else:
            active = bool(channels)

        if active:
            self.status_label.setText(
                f"Active - {len(channels)} channel(s)"
            )
        else:
            self.status_label.setText("Inactive")
