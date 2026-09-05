from collections.abc import Callable
from urllib.parse import urlsplit

from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.pages.manager_page import ToggleSwitch


class StreamerPage(QWidget):
    def __init__(
        self,
        save_callback: Callable[[], None],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 12)
        layout.setSpacing(10)

        title = QLabel("STREAMER SETTINGS")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        description = QLabel(
            "Streamer identity and Twitch channel settings."
        )
        description.setObjectName("pageDescription")
        layout.addWidget(description)

        streamer_group = QGroupBox("Streamer")
        streamer_layout = QVBoxLayout(streamer_group)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Streamer Name:"))

        self.streamer_name_input = QLineEdit()
        self.streamer_name_input.setObjectName(
            "streamerNameInput"
        )
        self.streamer_name_input.setPlaceholderText(
            "Streamer Name"
        )

        name_row.addWidget(
            self.streamer_name_input,
            1,
        )
        streamer_layout.addLayout(name_row)

        populate_name_row = QHBoxLayout()
        populate_name_row.addWidget(
            QLabel(
                "Populate Streamer Name from "
                "Twitch Channel URL:"
            )
        )

        self.populate_streamer_name_from_url_toggle = (
            ToggleSwitch()
        )
        self.populate_streamer_name_from_url_toggle.setObjectName(
            "populateStreamerNameFromUrlToggle"
        )
        self.populate_streamer_name_from_url_toggle.setAccessibleName(
            "Populate Streamer Name from Twitch Channel URL"
        )
        self.populate_streamer_name_from_url_toggle.setChecked(True)

        populate_name_row.addWidget(
            self.populate_streamer_name_from_url_toggle
        )
        populate_name_row.addStretch()

        streamer_layout.addLayout(populate_name_row)

        url_row = QHBoxLayout()
        url_row.addWidget(QLabel("Twitch Channel URL:"))

        self.channel_url_input = QLineEdit()
        self.channel_url_input.setObjectName(
            "twitchChannelUrlInput"
        )
        self.channel_url_input.setPlaceholderText(
            "https://www.twitch.tv/channel"
        )

        url_row.addWidget(
            self.channel_url_input,
            1,
        )
        streamer_layout.addLayout(url_row)

        channel_row = QHBoxLayout()
        channel_row.addWidget(QLabel("Twitch Channel:"))

        self.configured_channel_input = QLineEdit()
        self.configured_channel_input.setObjectName(
            "configuredTwitchChannelInput"
        )
        self.configured_channel_input.setPlaceholderText(
            "Twitch channel name"
        )

        channel_row.addWidget(
            self.configured_channel_input,
            1,
        )
        streamer_layout.addLayout(channel_row)

        populate_row = QHBoxLayout()
        populate_row.addWidget(
            QLabel(
                "Populate Twitch Channel from "
                "Twitch Channel URL:"
            )
        )

        self.populate_channel_from_url_toggle = (
            ToggleSwitch()
        )
        self.populate_channel_from_url_toggle.setObjectName(
            "populateTwitchChannelFromUrlToggle"
        )
        self.populate_channel_from_url_toggle.setAccessibleName(
            "Populate Twitch Channel from Twitch Channel URL"
        )
        self.populate_channel_from_url_toggle.setChecked(True)

        populate_row.addWidget(
            self.populate_channel_from_url_toggle
        )
        populate_row.addStretch()

        streamer_layout.addLayout(populate_row)

        button_row = QHBoxLayout()
        button_row.addStretch()

        self.save_settings_button = QPushButton(
            "Save Settings"
        )
        self.save_settings_button.setObjectName(
            "saveStreamerSettingsButton"
        )
        self.save_settings_button.clicked.connect(
            save_callback
        )

        button_row.addWidget(
            self.save_settings_button
        )
        streamer_layout.addLayout(button_row)

        layout.addWidget(streamer_group)
        layout.addStretch()

        self.channel_url_input.textChanged.connect(
            self._channel_url_changed
        )
        self.populate_streamer_name_from_url_toggle.toggled.connect(
            self._populate_streamer_name_setting_changed
        )
        self.populate_channel_from_url_toggle.toggled.connect(
            self._populate_setting_changed
        )

        self._apply_populate_mode()

    def streamer_name(self) -> str:
        return self.streamer_name_input.text().strip()

    def set_streamer_name(
        self,
        streamer_name: str,
    ) -> None:
        self.streamer_name_input.setText(
            streamer_name
        )

    def channel_url(self) -> str:
        return self.channel_url_input.text().strip()

    def configured_channel(self) -> str:
        return self.configured_channel_input.text().strip()

    def populate_streamer_name_from_url_enabled(self) -> bool:
        return (
            self.populate_streamer_name_from_url_toggle.isChecked()
        )

    def populate_channel_from_url_enabled(self) -> bool:
        return (
            self.populate_channel_from_url_toggle.isChecked()
        )

    @staticmethod
    def _channel_from_url(channel_url: str) -> str:
        value = channel_url.strip()

        if not value:
            return ""

        parse_url = value

        if "://" not in parse_url:
            parse_url = f"https://{parse_url}"

        parsed = urlsplit(parse_url)
        host = parsed.netloc.lower()

        if host.startswith("www."):
            host = host[4:]

        if host != "twitch.tv":
            return ""

        path_parts = [
            part
            for part in parsed.path.split("/")
            if part
        ]

        if not path_parts:
            return ""

        return path_parts[0].strip().lower()

    def _populate_streamer_name(self) -> None:
        self.streamer_name_input.setText(
            self._channel_from_url(
                self.channel_url()
            )
        )

    def _populate_configured_channel(self) -> None:
        self.configured_channel_input.setText(
            self._channel_from_url(
                self.channel_url()
            )
        )

    def _channel_url_changed(self) -> None:
        if self.populate_streamer_name_from_url_enabled():
            self._populate_streamer_name()

        if self.populate_channel_from_url_enabled():
            self._populate_configured_channel()

    def _populate_streamer_name_setting_changed(self) -> None:
        self._apply_populate_mode()

        if self.populate_streamer_name_from_url_enabled():
            self._populate_streamer_name()

    def _populate_setting_changed(self) -> None:
        self._apply_populate_mode()

        if self.populate_channel_from_url_enabled():
            self._populate_configured_channel()

    def _apply_populate_mode(self) -> None:
        self.streamer_name_input.setReadOnly(
            self.populate_streamer_name_from_url_enabled()
        )
        self.configured_channel_input.setReadOnly(
            self.populate_channel_from_url_enabled()
        )

    def load_settings(
        self,
        streamer_name: str,
        channel_url: str | None,
        channel: str | None,
        populate_streamer_name_from_url: bool,
        populate_channel_from_url: bool,
    ) -> None:
        self.populate_streamer_name_from_url_toggle.blockSignals(
            True
        )
        self.populate_channel_from_url_toggle.blockSignals(
            True
        )
        self.channel_url_input.blockSignals(True)

        self.populate_streamer_name_from_url_toggle.setChecked(
            populate_streamer_name_from_url
        )
        self.populate_channel_from_url_toggle.setChecked(
            populate_channel_from_url
        )
        self.channel_url_input.setText(
            channel_url or ""
        )

        self.populate_streamer_name_from_url_toggle.blockSignals(
            False
        )
        self.populate_channel_from_url_toggle.blockSignals(
            False
        )
        self.channel_url_input.blockSignals(False)

        self._apply_populate_mode()

        if populate_streamer_name_from_url:
            derived_streamer_name = self._channel_from_url(
                self.channel_url()
            )

            if derived_streamer_name:
                self.streamer_name_input.setText(
                    derived_streamer_name
                )
            else:
                self.streamer_name_input.setText(
                    streamer_name
                )
        else:
            self.streamer_name_input.setText(
                streamer_name
            )

        if populate_channel_from_url:
            self._populate_configured_channel()
        else:
            self.configured_channel_input.setText(
                channel or ""
            )
