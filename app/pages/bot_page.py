from collections.abc import Callable
from urllib.parse import urlsplit

from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class BotPage(QWidget):
    def __init__(
        self,
        base_url: str,
        bot_port: int,
        save_bot_url_callback: Callable[[], None],
        test_connection_callback: Callable[[], None],
        toggle_public_web_callback: Callable[[], None],
        refresh_public_web_callback: Callable[[], None],
        save_logging_callback: Callable[[], None],
        refresh_logging_callback: Callable[[], None],
        restart_bot_callback: Callable[[], None],
        *,
        connection_mode: str = "automatic",
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        self._connection_mode = (
            connection_mode
            if connection_mode in {"automatic", "manual"}
            else "automatic"
        )

        parsed_base_url = urlsplit(
            base_url
            if "://" in base_url
            else f"https://{base_url}"
        )
        initial_protocol = (
            f"{parsed_base_url.scheme}://"
            if parsed_base_url.scheme
            else "https://"
        )
        initial_host = (
            parsed_base_url.hostname
            or base_url
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 12)

        group = QGroupBox("LinkCue Bot")
        group_layout = QVBoxLayout(group)

        connection_row = QHBoxLayout()

        connection_row.addWidget(QLabel("Mode:"))

        self.connection_mode_input = QComboBox()
        self.connection_mode_input.setObjectName(
            "connectionModeInput"
        )
        self.connection_mode_input.addItem(
            "Automatic",
            "automatic",
        )
        self.connection_mode_input.addItem(
            "Manual",
            "manual",
        )

        mode_index = self.connection_mode_input.findData(
            self._connection_mode
        )
        self.connection_mode_input.setCurrentIndex(
            mode_index if mode_index >= 0 else 0
        )

        connection_row.addWidget(
            self.connection_mode_input
        )

        connection_row.addWidget(QLabel("Protocol:"))

        self.bot_protocol_input = QComboBox()
        self.bot_protocol_input.setObjectName(
            "botProtocolInput"
        )
        self.bot_protocol_input.addItems(
            ["http://", "https://"]
        )
        self.bot_protocol_input.setCurrentText(
            initial_protocol
        )
        connection_row.addWidget(
            self.bot_protocol_input
        )

        connection_row.addWidget(QLabel("Host:"))

        self.bot_url_input = QLineEdit(initial_host)
        self.bot_url_input.setObjectName("botUrlInput")
        self.bot_url_input.setMinimumWidth(280)
        connection_row.addWidget(
            self.bot_url_input,
            1,
        )

        connection_row.addWidget(QLabel("Port:"))

        self.bot_port_input = QLineEdit(str(bot_port))
        self.bot_port_input.setObjectName("botPortInput")
        self.bot_port_input.setMaximumWidth(90)
        connection_row.addWidget(
            self.bot_port_input
        )

        group_layout.addLayout(connection_row)

        connection_action_row = QHBoxLayout()
        connection_action_row.addStretch()

        self.save_bot_url_button = QPushButton(
            "Save"
        )
        self.save_bot_url_button.setObjectName(
            "saveBotUrlButton"
        )
        self.save_bot_url_button.clicked.connect(
            save_bot_url_callback
        )
        connection_action_row.addWidget(
            self.save_bot_url_button
        )

        self.test_connection_button = QPushButton(
            "Test Connection"
        )
        self.test_connection_button.setObjectName(
            "testConnectionButton"
        )
        self.test_connection_button.clicked.connect(
            test_connection_callback
        )
        connection_action_row.addWidget(
            self.test_connection_button
        )

        connection_action_row.addWidget(QLabel("Status:"))

        self.bot_status_label = QLabel("Not checked")
        self.bot_status_label.setObjectName(
            "botStatusLabel"
        )
        self.bot_status_label.setMinimumWidth(120)
        connection_action_row.addWidget(
            self.bot_status_label
        )

        group_layout.addLayout(connection_action_row)

        web_row = QHBoxLayout()
        web_row.addWidget(QLabel("Public Web:"))

        self.public_web_toggle = QPushButton("Unknown")
        self.public_web_toggle.setObjectName(
            "publicWebToggle"
        )
        self.public_web_toggle.setCheckable(True)
        self.public_web_toggle.clicked.connect(
            toggle_public_web_callback
        )
        web_row.addWidget(
            self.public_web_toggle
        )

        self.public_web_status_label = QLabel(
            "Not checked"
        )
        self.public_web_status_label.setObjectName(
            "publicWebStatusLabel"
        )
        web_row.addWidget(
            self.public_web_status_label,
            1,
        )

        group_layout.addLayout(web_row)

        web_config_row = QHBoxLayout()
        web_config_row.addWidget(QLabel("Protocol:"))

        self.public_web_protocol_input = QComboBox()
        self.public_web_protocol_input.setObjectName(
            "publicWebProtocolInput"
        )
        self.public_web_protocol_input.addItems(
            ["http://", "https://"]
        )
        self.public_web_protocol_input.setCurrentText(
            "https://"
        )
        web_config_row.addWidget(
            self.public_web_protocol_input
        )

        web_config_row.addWidget(QLabel("Host:"))

        self.public_web_url_input = QLineEdit()
        self.public_web_url_input.setObjectName(
            "publicWebUrlInput"
        )
        self.public_web_url_input.setMinimumWidth(280)
        web_config_row.addWidget(
            self.public_web_url_input,
            1,
        )

        web_config_row.addWidget(QLabel("Port Mode:"))

        self.public_web_mode_input = QComboBox()
        self.public_web_mode_input.setObjectName(
            "publicWebModeInput"
        )
        self.public_web_mode_input.addItem(
            "Automatic",
            "automatic",
        )
        self.public_web_mode_input.addItem(
            "Manual",
            "manual",
        )
        web_config_row.addWidget(
            self.public_web_mode_input
        )

        web_config_row.addWidget(QLabel("Web Port:"))

        self.public_web_port_input = QLineEdit()
        self.public_web_port_input.setObjectName(
            "publicWebPortInput"
        )
        self.public_web_port_input.setMaximumWidth(90)
        web_config_row.addWidget(
            self.public_web_port_input
        )

        self.refresh_public_web_button = QPushButton(
            "Refresh"
        )
        self.refresh_public_web_button.setObjectName(
            "refreshPublicWebButton"
        )
        self.refresh_public_web_button.clicked.connect(
            refresh_public_web_callback
        )
        web_config_row.addWidget(
            self.refresh_public_web_button
        )

        group_layout.addLayout(web_config_row)

        self.public_web_links_group = QGroupBox(
            "Public Web Links"
        )
        public_web_links_layout = QVBoxLayout(
            self.public_web_links_group
        )

        self.live_queue_link = QLabel()
        self.live_queue_link.setOpenExternalLinks(True)
        self.live_queue_link.setTextInteractionFlags(
            self.live_queue_link.textInteractionFlags()
        )
        public_web_links_layout.addWidget(
            self.live_queue_link
        )

        self.help_link = QLabel()
        self.help_link.setOpenExternalLinks(True)
        self.help_link.setTextInteractionFlags(
            self.help_link.textInteractionFlags()
        )
        public_web_links_layout.addWidget(
            self.help_link
        )

        self.architecture_link = QLabel()
        self.architecture_link.setOpenExternalLinks(True)
        self.architecture_link.setTextInteractionFlags(
            self.architecture_link.textInteractionFlags()
        )
        public_web_links_layout.addWidget(
            self.architecture_link
        )

        self.public_web_links_group.setVisible(False)
        group_layout.addWidget(
            self.public_web_links_group
        )

        logging_group = QGroupBox("Logging")
        logging_layout = QVBoxLayout(
            logging_group
        )

        logging_row = QHBoxLayout()
        logging_row.addWidget(
            QLabel("Logging:")
        )

        self.logging_toggle = QPushButton(
            "Unknown"
        )
        self.logging_toggle.setObjectName(
            "loggingToggle"
        )
        self.logging_toggle.setCheckable(True)
        logging_row.addWidget(
            self.logging_toggle
        )

        logging_row.addWidget(
            QLabel("Time Zone:")
        )

        self.logging_timezone_input = QComboBox()
        self.logging_timezone_input.setObjectName(
            "loggingTimezoneInput"
        )
        self.logging_timezone_input.setEditable(True)
        self.logging_timezone_input.setInsertPolicy(
            QComboBox.InsertPolicy.NoInsert
        )
        self.logging_timezone_input.addItems(
            [
                "America/Detroit",
                "America/New_York",
                "America/Chicago",
                "America/Denver",
                "America/Los_Angeles",
                "America/Phoenix",
                "America/Anchorage",
                "Pacific/Honolulu",
                "UTC",
            ]
        )
        self.logging_timezone_input.setCurrentText(
            "America/Detroit"
        )
        logging_row.addWidget(
            self.logging_timezone_input,
            1,
        )

        self.save_logging_button = QPushButton(
            "Save Logging"
        )
        self.save_logging_button.setObjectName(
            "saveLoggingButton"
        )
        self.save_logging_button.clicked.connect(
            save_logging_callback
        )
        logging_row.addWidget(
            self.save_logging_button
        )

        self.refresh_logging_button = QPushButton(
            "Refresh"
        )
        self.refresh_logging_button.setObjectName(
            "refreshLoggingButton"
        )
        self.refresh_logging_button.clicked.connect(
            refresh_logging_callback
        )
        logging_row.addWidget(
            self.refresh_logging_button
        )

        logging_layout.addLayout(
            logging_row
        )

        self.logging_status_label = QLabel(
            "Not checked"
        )
        self.logging_status_label.setObjectName(
            "loggingStatusLabel"
        )
        logging_layout.addWidget(
            self.logging_status_label
        )

        group_layout.addWidget(
            logging_group
        )

        maintenance_group = QGroupBox(
            "Maintenance"
        )
        maintenance_layout = QHBoxLayout(
            maintenance_group
        )

        self.restart_bot_button = QPushButton(
            "Restart Bot"
        )
        self.restart_bot_button.setObjectName(
            "restartBotButton"
        )
        self.restart_bot_button.clicked.connect(
            restart_bot_callback
        )
        maintenance_layout.addWidget(
            self.restart_bot_button
        )

        self.restart_bot_note = QLabel(
            "Restart control is currently a "
            "development placeholder."
        )
        self.restart_bot_note.setObjectName(
            "restartBotNote"
        )
        maintenance_layout.addWidget(
            self.restart_bot_note,
            1,
        )

        group_layout.addWidget(
            maintenance_group
        )

        self.connection_mode_input.currentIndexChanged.connect(
            self._connection_mode_changed
        )
        self.bot_url_input.editingFinished.connect(
            self.normalize_bot_url_input
        )
        self.public_web_url_input.textChanged.connect(
            self._refresh_public_web_links
        )
        self.public_web_url_input.editingFinished.connect(
            self.normalize_public_web_url_input
        )
        self.public_web_protocol_input.currentIndexChanged.connect(
            self._refresh_public_web_links
        )
        self.public_web_mode_input.currentIndexChanged.connect(
            self._refresh_public_web_links
        )
        self.public_web_port_input.textChanged.connect(
            self._refresh_public_web_links
        )

        self._refresh_public_web_links()

        layout.addWidget(group)
        layout.addStretch()

    def bot_host(self) -> str:
        host = self.bot_url_input.text().strip().rstrip("/")

        if not host:
            return ""

        return f"{self.bot_protocol_input.currentText()}{host}"

    def normalize_bot_url_input(self) -> None:
        value = self.bot_url_input.text().strip()

        if "://" not in value:
            return

        parsed = urlsplit(value)

        if parsed.scheme in {"http", "https"}:
            self.bot_protocol_input.setCurrentText(
                f"{parsed.scheme}://"
            )

        if parsed.hostname:
            self.bot_url_input.setText(parsed.hostname)

    def normalize_public_web_url_input(self) -> None:
        value = self.public_web_url_input.text().strip()

        if "://" not in value:
            return

        parsed = urlsplit(value)

        if parsed.scheme in {"http", "https"}:
            self.public_web_protocol_input.setCurrentText(
                f"{parsed.scheme}://"
            )

        if parsed.hostname:
            self.public_web_url_input.setText(
                parsed.hostname
            )

    def connection_mode(self) -> str:
        mode = self.connection_mode_input.currentData()

        if mode in {"automatic", "manual"}:
            return mode

        return "automatic"

    def _connection_mode_changed(self) -> None:
        self._connection_mode = self.connection_mode()
        self._refresh_public_web_links()

    def bot_port(self) -> int:
        value = self.bot_port_input.text().strip()

        try:
            return int(value)
        except ValueError:
            return 8000

    def bot_url(self) -> str:
        host = self.bot_host()

        if not host:
            return ""

        if self.connection_mode() == "automatic":
            return host

        return f"{host}:{self.bot_port()}"

    def set_connection_offline(self) -> None:
        self.bot_status_label.setText("Offline")

    def set_connection_version(
        self,
        version: str,
    ) -> None:
        self.bot_status_label.setText(
            f"Connected - Bot {version}"
        )

    def requested_public_web_enabled(self) -> bool:
        return self.public_web_toggle.isChecked()

    def public_web_mode(self) -> str:
        mode = self.public_web_mode_input.currentData()

        if mode in {"automatic", "manual"}:
            return mode

        return "automatic"

    def public_web_host(self) -> str:
        host = (
            self.public_web_url_input
            .text()
            .strip()
            .rstrip("/")
        )

        if not host:
            return ""

        return (
            f"{self.public_web_protocol_input.currentText()}"
            f"{host}"
        )

    def public_web_port(self) -> int | None:
        value = self.public_web_port_input.text().strip()

        if not value:
            return None

        try:
            return int(value)
        except ValueError:
            return None

    def _refresh_public_web_links(self) -> None:
        host = self.public_web_host()
        port = self.public_web_port()

        if not host:
            self.live_queue_link.clear()
            self.help_link.clear()
            self.architecture_link.clear()
            return

        if self.public_web_mode() == "automatic":
            base_url = host
        else:
            if port is None:
                self.live_queue_link.clear()
                self.help_link.clear()
                self.architecture_link.clear()
                return

            base_url = f"{host}:{port}"

        live_url = f"{base_url}/live"
        help_url = f"{base_url}/help"
        architecture_url = (
            f"{base_url}/help/architecture"
        )

        self.live_queue_link.setText(
            f'Live Queue: '
            f'<a href="{live_url}">{live_url}</a>'
        )
        self.help_link.setText(
            f'Help: '
            f'<a href="{help_url}">{help_url}</a>'
        )
        self.architecture_link.setText(
            f'Architecture: '
            f'<a href="{architecture_url}">'
            f'{architecture_url}</a>'
        )

    def requested_logging_enabled(self) -> bool:
        return self.logging_toggle.isChecked()

    def logging_timezone(self) -> str:
        return (
            self.logging_timezone_input
            .currentText()
            .strip()
        )

    def set_logging_unavailable(self) -> None:
        self.logging_status_label.setText(
            "Unavailable"
        )

    def apply_logging_setting(
        self,
        enabled: bool,
        timezone_name: str,
    ) -> None:
        self.logging_toggle.blockSignals(True)
        self.logging_toggle.setChecked(enabled)
        self.logging_toggle.setText(
            "Enabled" if enabled else "Disabled"
        )
        self.logging_toggle.blockSignals(False)

        self.logging_timezone_input.setCurrentText(
            timezone_name
        )

        self.logging_status_label.setText(
            (
                f"Logging enabled - {timezone_name}"
                if enabled
                else f"Logging disabled - {timezone_name}"
            )
        )

    def set_public_web_unavailable(self) -> None:
        self.public_web_status_label.setText(
            "Unavailable"
        )
        self.public_web_links_group.setVisible(False)

    def apply_public_web_setting(
        self,
        enabled: bool,
        port: int | None = None,
        public_url: str | None = None,
        connection_mode: str | None = None,
    ) -> None:
        if public_url:
            parsed = urlsplit(public_url)

            if parsed.scheme in {"http", "https"}:
                self.public_web_protocol_input.setCurrentText(
                    f"{parsed.scheme}://"
                )

            if parsed.hostname:
                self.public_web_url_input.setText(
                    parsed.hostname
                )

        if connection_mode in {"automatic", "manual"}:
            self.public_web_mode_input.setCurrentText(
                connection_mode.capitalize()
            )

        self.public_web_toggle.blockSignals(True)
        self.public_web_toggle.setChecked(enabled)
        self.public_web_toggle.setText(
            "Enabled" if enabled else "Disabled"
        )
        self.public_web_toggle.blockSignals(False)

        self.public_web_status_label.setText(
            "Public pages available"
            if enabled
            else "Public pages disabled"
        )

        if port is not None:
            self.public_web_port_input.setText(
                str(port)
            )

        self._refresh_public_web_links()
        self.public_web_links_group.setVisible(
            enabled
        )
