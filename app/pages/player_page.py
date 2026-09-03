from collections.abc import Callable

from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class PlayerPage(QWidget):
    def __init__(
        self,
        refresh_callback: Callable[[], None],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 12)

        group = QGroupBox("LinkCue Player")
        group_layout = QHBoxLayout(group)

        group_layout.addWidget(QLabel("Player:"))

        self.player_status_label = QLabel("Not checked")
        self.player_status_label.setObjectName(
            "playerStatusLabel"
        )
        group_layout.addWidget(self.player_status_label)

        group_layout.addSpacing(20)
        group_layout.addWidget(QLabel("Playback:"))

        self.playback_status_label = QLabel("Not checked")
        self.playback_status_label.setObjectName(
            "playbackStatusLabel"
        )
        group_layout.addWidget(self.playback_status_label)

        group_layout.addSpacing(20)
        group_layout.addWidget(QLabel("Now Playing:"))

        self.now_playing_label = QLabel("None")
        self.now_playing_label.setObjectName(
            "nowPlayingLabel"
        )
        group_layout.addWidget(
            self.now_playing_label,
            1,
        )

        self.refresh_button = QPushButton("Refresh Player")
        self.refresh_button.setObjectName(
            "refreshPlayerButton"
        )
        self.refresh_button.clicked.connect(
            refresh_callback
        )
        group_layout.addWidget(self.refresh_button)

        layout.addWidget(group)
        layout.addStretch()

    def show_unavailable(self) -> None:
        self.player_status_label.setText("Offline")
        self.playback_status_label.setText("Unknown")
        self.now_playing_label.setText("None")

    def apply_status(
        self,
        presence: dict,
        playback: dict,
    ) -> None:
        if presence.get("active"):
            self.player_status_label.setText("Active")
        else:
            self.player_status_label.setText("Offline")

        state = playback.get("state", "unknown")

        if state == "playing":
            playback_text = "Playing"
        elif state == "idle":
            playback_text = "Idle"
        else:
            playback_text = str(state).title()

        self.playback_status_label.setText(
            playback_text
        )

        item = playback.get("item")

        if item:
            title = (
                item.get("title")
                or item.get("url")
                or "Untitled video"
            )
            self.now_playing_label.setText(
                str(title)
            )
        else:
            self.now_playing_label.setText("None")
