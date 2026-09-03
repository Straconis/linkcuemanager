from collections.abc import Callable

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
            "Streamer-specific settings used by LinkCue integrations."
        )
        description.setObjectName("pageDescription")
        layout.addWidget(description)

        twitch_group = QGroupBox("Twitch")
        twitch_layout = QVBoxLayout(twitch_group)

        identity_row = QHBoxLayout()

        identity_row.addWidget(
            QLabel("Streamer Name:")
        )

        self.streamer_name_input = QLineEdit()
        self.streamer_name_input.setObjectName(
            "streamerNameInput"
        )
        self.streamer_name_input.setPlaceholderText(
            "Streamer Name"
        )
        self.streamer_name_input.setMaximumWidth(220)

        identity_row.addWidget(
            self.streamer_name_input
        )

        identity_row.addSpacing(18)

        identity_row.addWidget(
            QLabel("Twitch URL:")
        )

        self.twitch_url_input = QLineEdit()
        self.twitch_url_input.setObjectName(
            "streamerTwitchUrlInput"
        )
        self.twitch_url_input.setPlaceholderText(
            "https://www.twitch.tv/channel"
        )
        self.twitch_url_input.setMaximumWidth(420)

        identity_row.addWidget(
            self.twitch_url_input,
            1,
        )
        identity_row.addStretch()

        twitch_layout.addLayout(identity_row)

        populate_row = QHBoxLayout()

        populate_row.addWidget(
            QLabel("Populate Fields from Twitch URL:")
        )

        self.populate_from_twitch_toggle = ToggleSwitch()
        self.populate_from_twitch_toggle.setObjectName(
            "populateFromTwitchToggle"
        )
        self.populate_from_twitch_toggle.setAccessibleName(
            "Populate Fields from Twitch URL"
        )

        populate_row.addWidget(
            self.populate_from_twitch_toggle
        )
        populate_row.addStretch()

        twitch_layout.addLayout(populate_row)

        mapping_label = QLabel(
            "Fields populated from the Twitch URL:"
        )
        twitch_layout.addWidget(mapping_label)

        self.twitch_mapping_label = QLabel(
            "Streamer Name\n"
            "Twitch Channel"
        )
        self.twitch_mapping_label.setObjectName(
            "twitchMappingLabel"
        )

        twitch_layout.addWidget(
            self.twitch_mapping_label
        )

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

        twitch_layout.addLayout(button_row)

        layout.addWidget(twitch_group)
        layout.addStretch()

    def streamer_name(self) -> str:
        return self.streamer_name_input.text().strip()

    def set_streamer_name(
        self,
        streamer_name: str,
    ) -> None:
        self.streamer_name_input.setText(
            streamer_name
        )

    def twitch_url(self) -> str:
        return self.twitch_url_input.text().strip()

    def populate_from_twitch_enabled(self) -> bool:
        return self.populate_from_twitch_toggle.isChecked()

    def load_settings(
        self,
        streamer_name: str,
        twitch_url: str,
        populate_from_twitch: bool,
    ) -> None:
        self.streamer_name_input.setText(
            streamer_name
        )
        self.twitch_url_input.setText(
            twitch_url
        )

        self.populate_from_twitch_toggle.blockSignals(True)
        self.populate_from_twitch_toggle.setChecked(
            populate_from_twitch
        )
        self.populate_from_twitch_toggle.blockSignals(False)
