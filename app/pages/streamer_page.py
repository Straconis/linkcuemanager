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
        authorize_twitch_callback: Callable[[], None],
        generate_streamer_auth_callback: Callable[[], None],
        copy_streamer_auth_callback: Callable[[], None],
        parent: QWidget | None = None,
        *,
        refresh_master_callback: Callable[[], None] | None = None,
        force_release_master_callback: Callable[[], None] | None = None,
        reset_streamer_sync_callback: Callable[[], None] | None = None,
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

        self.streamer_auth_status_label = QLabel(
            "Streamer channel: Not authorized"
        )
        self.streamer_auth_status_label.setObjectName(
            "streamerAuthorizationStatus"
        )
        streamer_layout.addWidget(
            self.streamer_auth_status_label
        )

        auth_link_row = QHBoxLayout()

        self.streamer_auth_link_input = QLineEdit()
        self.streamer_auth_link_input.setObjectName(
            "streamerAuthorizationLink"
        )
        self.streamer_auth_link_input.setReadOnly(True)
        self.streamer_auth_link_input.setPlaceholderText(
            "Generate a link to send to the streamer"
        )

        self.generate_streamer_auth_link_button = QPushButton(
            "Generate Streamer Authorization Link"
        )
        self.generate_streamer_auth_link_button.setObjectName(
            "generateStreamerAuthorizationLinkButton"
        )
        self.generate_streamer_auth_link_button.setToolTip(
            "Create a secure Twitch authorization link "
            "to send to the streamer."
        )
        self.generate_streamer_auth_link_button.clicked.connect(
            generate_streamer_auth_callback
        )

        self.copy_streamer_auth_link_button = QPushButton(
            "Copy Link"
        )
        self.copy_streamer_auth_link_button.setObjectName(
            "copyStreamerAuthorizationLinkButton"
        )
        self.copy_streamer_auth_link_button.setEnabled(False)
        self.copy_streamer_auth_link_button.clicked.connect(
            copy_streamer_auth_callback
        )

        auth_link_row.addWidget(
            self.streamer_auth_link_input,
            1,
        )
        auth_link_row.addWidget(
            self.generate_streamer_auth_link_button
        )
        auth_link_row.addWidget(
            self.copy_streamer_auth_link_button
        )

        streamer_layout.addLayout(auth_link_row)

        master_group = QGroupBox("Master Player")
        master_layout = QVBoxLayout(master_group)

        self.master_player_status_label = QLabel(
            "Master Player: Status not checked"
        )
        self.master_player_status_label.setObjectName(
            "masterPlayerStatus"
        )
        self.master_player_status_label.setWordWrap(True)
        master_layout.addWidget(
            self.master_player_status_label
        )

        master_help = QLabel(
            "The master Player is the only Player allowed "
            "to register Bot-level Now Playing state for "
            "this Twitch channel."
        )
        master_help.setWordWrap(True)
        master_layout.addWidget(master_help)

        master_buttons = QHBoxLayout()

        self.refresh_master_status_button = QPushButton(
            "Refresh Master Status"
        )
        self.refresh_master_status_button.setObjectName(
            "refreshMasterPlayerStatusButton"
        )

        self.force_release_master_button = QPushButton(
            "Force Release Master Player"
        )
        self.force_release_master_button.setObjectName(
            "forceReleaseMasterPlayerButton"
        )

        if refresh_master_callback is not None:
            self.refresh_master_status_button.clicked.connect(
                refresh_master_callback
            )

        if force_release_master_callback is not None:
            self.force_release_master_button.clicked.connect(
                force_release_master_callback
            )

        master_buttons.addWidget(
            self.refresh_master_status_button
        )
        master_buttons.addWidget(
            self.force_release_master_button
        )
        master_buttons.addStretch()

        master_layout.addLayout(master_buttons)
        streamer_layout.addWidget(master_group)

        password_group = QGroupBox(
            "Streamer Sync Password"
        )
        password_layout = QVBoxLayout(password_group)

        password_warning = QLabel(
            "Resetting this password revokes every paired "
            "Player and clears the active master lease. "
            "Each Player must pair again using the new password."
        )
        password_warning.setWordWrap(True)
        password_layout.addWidget(password_warning)

        current_password_row = QHBoxLayout()
        current_password_row.addWidget(
            QLabel("Current Password:")
        )

        self.current_streamer_sync_password_input = (
            QLineEdit()
        )
        self.current_streamer_sync_password_input.setObjectName(
            "currentStreamerSyncPasswordInput"
        )
        self.current_streamer_sync_password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )
        current_password_row.addWidget(
            self.current_streamer_sync_password_input,
            1,
        )
        password_layout.addLayout(current_password_row)

        new_password_row = QHBoxLayout()
        new_password_row.addWidget(
            QLabel("New Password:")
        )

        self.new_streamer_sync_password_input = QLineEdit()
        self.new_streamer_sync_password_input.setObjectName(
            "newStreamerSyncPasswordInput"
        )
        self.new_streamer_sync_password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )
        new_password_row.addWidget(
            self.new_streamer_sync_password_input,
            1,
        )
        password_layout.addLayout(new_password_row)

        confirm_password_row = QHBoxLayout()
        confirm_password_row.addWidget(
            QLabel("Confirm New Password:")
        )

        self.confirm_streamer_sync_password_input = (
            QLineEdit()
        )
        self.confirm_streamer_sync_password_input.setObjectName(
            "confirmStreamerSyncPasswordInput"
        )
        self.confirm_streamer_sync_password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )
        confirm_password_row.addWidget(
            self.confirm_streamer_sync_password_input,
            1,
        )
        password_layout.addLayout(confirm_password_row)

        reset_password_row = QHBoxLayout()

        self.reset_streamer_sync_password_button = QPushButton(
            "Reset Streamer Sync Password"
        )
        self.reset_streamer_sync_password_button.setObjectName(
            "resetStreamerSyncPasswordButton"
        )

        if reset_streamer_sync_callback is not None:
            self.reset_streamer_sync_password_button.clicked.connect(
                reset_streamer_sync_callback
            )

        reset_password_row.addWidget(
            self.reset_streamer_sync_password_button
        )
        reset_password_row.addStretch()

        password_layout.addLayout(reset_password_row)
        streamer_layout.addWidget(password_group)

        button_row = QHBoxLayout()

        self.authorize_twitch_button = QPushButton(
            "Authorize LinkCue Bot Account"
        )
        self.authorize_twitch_button.setObjectName(
            "authorizeBotWithTwitchButton"
        )
        self.authorize_twitch_button.setToolTip(
            "Testing and maintenance only: authorize while "
            "signed into the LinkCue Twitch account."
        )
        self.authorize_twitch_button.clicked.connect(
            authorize_twitch_callback
        )

        button_row.addWidget(
            self.authorize_twitch_button
        )
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

    def set_master_player_status(
        self,
        status: dict,
    ) -> None:
        active = bool(status.get("active"))
        channel = str(
            status.get("channel") or ""
        ).strip()
        owner = str(
            status.get("display_name")
            or status.get("client_id")
            or ""
        ).strip()

        if active:
            text = "Master Player: Active"

            if owner:
                text += f" - {owner}"

            if channel:
                text += f" for {channel}"
        else:
            text = "Master Player: None active"

            if channel:
                text += f" for {channel}"

        self.master_player_status_label.setText(text)

    def set_master_player_status_message(
        self,
        message: str,
    ) -> None:
        self.master_player_status_label.setText(
            message.strip()
        )

    def current_streamer_sync_password(self) -> str:
        return (
            self.current_streamer_sync_password_input
            .text()
        )

    def new_streamer_sync_password(self) -> str:
        return (
            self.new_streamer_sync_password_input
            .text()
        )

    def confirmed_streamer_sync_password(self) -> str:
        return (
            self.confirm_streamer_sync_password_input
            .text()
        )

    def clear_streamer_sync_password_fields(
        self,
    ) -> None:
        self.current_streamer_sync_password_input.clear()
        self.new_streamer_sync_password_input.clear()
        self.confirm_streamer_sync_password_input.clear()

    def set_streamer_authorization_link(
        self,
        authorization_url: str,
    ) -> None:
        normalized = authorization_url.strip()

        self.streamer_auth_link_input.setText(
            normalized
        )
        self.copy_streamer_auth_link_button.setEnabled(
            bool(normalized)
        )

    def streamer_authorization_link(self) -> str:
        return self.streamer_auth_link_input.text().strip()

    def set_streamer_authorization_status(
        self,
        *,
        authorized: bool,
        login: str | None,
    ) -> None:
        normalized_login = (login or "").strip().lower()

        if authorized and normalized_login:
            text = (
                "Streamer channel: Authorized as "
                f"{normalized_login}"
            )
        else:
            text = "Streamer channel: Not authorized"

        self.streamer_auth_status_label.setText(text)

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
