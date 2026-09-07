from collections.abc import Callable
from urllib.parse import urlsplit

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class BotPage(QWidget):
    def _show_public_link_context_menu(
        self,
        label: QLabel,
        position,
    ) -> None:
        href = label.text()

        start = href.find('href="')
        if start == -1:
            return

        start += len('href="')
        end = href.find('"', start)

        if end == -1:
            return

        url = href[start:end]

        if not url:
            return

        menu = QMenu(label)
        copy_action = menu.addAction("Copy Link")

        selected_action = menu.exec(
            label.mapToGlobal(position)
        )

        if selected_action is copy_action:
            QApplication.clipboard().setText(url)

    def __init__(
        self,
        base_url: str,
        bot_port: int,
        save_bot_url_callback: Callable[[], None],
        test_connection_callback: Callable[[], None],
        save_public_web_callback: Callable[[], None],
        refresh_public_web_callback: Callable[[], None],
        save_logging_callback: Callable[[], None],
        refresh_logging_callback: Callable[[], None],
        save_host_control_callback: Callable[[], None],
        restart_bot_callback: Callable[[], None],
        *,
        pair_manager_callback: Callable[[], None] | None = None,
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

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(
            QScrollArea.Shape.NoFrame
        )
        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        group = QGroupBox("LinkCue Bot")
        group_layout = QVBoxLayout(group)

        self.connection_group = QGroupBox(
            "Bot Connection"
        )
        self.connection_group.setObjectName(
            "botConnectionGroup"
        )
        connection_layout = QVBoxLayout(
            self.connection_group
        )

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

        connection_layout.addLayout(
            connection_row
        )

        connection_action_row = QHBoxLayout()
        connection_action_row.addStretch()

        self.save_bot_url_button = QPushButton(
            "Save Connection"
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

        connection_layout.addLayout(
            connection_action_row
        )

        group_layout.addWidget(
            self.connection_group
        )

        self.security_group = QGroupBox(
            "LinkCue Security"
        )
        self.security_group.setObjectName(
            "linkCueSecurityGroup"
        )
        security_layout = QVBoxLayout(
            self.security_group
        )

        security_row = QHBoxLayout()

        security_row.addWidget(
            QLabel("Control Network Password:")
        )

        self.control_password_input = QLineEdit()
        self.control_password_input.setObjectName(
            "controlNetworkPasswordInput"
        )
        self.control_password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )
        self.control_password_input.setPlaceholderText(
            "Enter Control Network password"
        )
        security_row.addWidget(
            self.control_password_input,
            1,
        )

        self.pair_manager_button = QPushButton(
            "Pair This Manager"
        )
        self.pair_manager_button.setObjectName(
            "pairManagerButton"
        )

        if pair_manager_callback is not None:
            self.pair_manager_button.clicked.connect(
                pair_manager_callback
            )

        security_row.addWidget(
            self.pair_manager_button
        )

        security_layout.addLayout(
            security_row
        )

        pairing_status_row = QHBoxLayout()
        pairing_status_row.addWidget(
            QLabel("Pairing Status:")
        )

        self.pairing_status_label = QLabel(
            "Not paired"
        )
        self.pairing_status_label.setObjectName(
            "pairingStatusLabel"
        )
        pairing_status_row.addWidget(
            self.pairing_status_label,
            1,
        )

        security_layout.addLayout(
            pairing_status_row
        )

        group_layout.addWidget(
            self.security_group
        )

        self.public_web_group = QGroupBox(
            "Public Web"
        )
        self.public_web_group.setObjectName(
            "publicWebGroup"
        )
        public_web_layout = QVBoxLayout(
            self.public_web_group
        )

        web_row = QHBoxLayout()
        web_row.addWidget(QLabel("Public Web:"))

        self.public_web_toggle = QPushButton("Unknown")
        self.public_web_toggle.setObjectName(
            "publicWebToggle"
        )
        self.public_web_toggle.setCheckable(True)
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

        public_web_layout.addLayout(
            web_row
        )

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

        self.save_public_web_button = QPushButton(
            "Save Public Web"
        )
        self.save_public_web_button.setObjectName(
            "savePublicWebButton"
        )
        self.save_public_web_button.clicked.connect(
            save_public_web_callback
        )
        web_config_row.addWidget(
            self.save_public_web_button
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

        public_web_layout.addLayout(
            web_config_row
        )

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
        self.live_queue_link.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.live_queue_link.customContextMenuRequested.connect(
            lambda position:
            self._show_public_link_context_menu(
                self.live_queue_link,
                position,
            )
        )
        public_web_links_layout.addWidget(
            self.live_queue_link
        )

        self.history_link = QLabel()
        self.history_link.setOpenExternalLinks(True)
        self.history_link.setTextInteractionFlags(
            self.history_link.textInteractionFlags()
        )
        self.history_link.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.history_link.customContextMenuRequested.connect(
            lambda position:
            self._show_public_link_context_menu(
                self.history_link,
                position,
            )
        )
        public_web_links_layout.addWidget(
            self.history_link
        )

        self.help_link = QLabel()
        self.help_link.setOpenExternalLinks(True)
        self.help_link.setTextInteractionFlags(
            self.help_link.textInteractionFlags()
        )
        self.help_link.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.help_link.customContextMenuRequested.connect(
            lambda position:
            self._show_public_link_context_menu(
                self.help_link,
                position,
            )
        )
        public_web_links_layout.addWidget(
            self.help_link
        )

        self.architecture_link = QLabel()
        self.architecture_link.setOpenExternalLinks(True)
        self.architecture_link.setTextInteractionFlags(
            self.architecture_link.textInteractionFlags()
        )
        self.architecture_link.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.architecture_link.customContextMenuRequested.connect(
            lambda position:
            self._show_public_link_context_menu(
                self.architecture_link,
                position,
            )
        )
        public_web_links_layout.addWidget(
            self.architecture_link
        )

        self.public_web_links_group.setVisible(False)
        public_web_layout.addWidget(
            self.public_web_links_group
        )

        group_layout.addWidget(
            self.public_web_group
        )

        self.logging_group = QGroupBox(
            "Logging"
        )
        self.logging_group.setObjectName(
            "loggingGroup"
        )
        logging_layout = QVBoxLayout(
            self.logging_group
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
            self.logging_group
        )

        self.maintenance_group = QGroupBox(
            "Maintenance"
        )
        self.maintenance_group.setObjectName(
            "maintenanceGroup"
        )
        maintenance_layout = QVBoxLayout(
            self.maintenance_group
        )

        host_control_form = QFormLayout()

        self.bot_hosting_deployment_id_input = QLineEdit()
        self.bot_hosting_deployment_id_input.setObjectName(
            "botHostingDeploymentIdInput"
        )
        host_control_form.addRow(
            "Deployment ID:",
            self.bot_hosting_deployment_id_input,
        )

        self.bot_hosting_api_key_input = QLineEdit()
        self.bot_hosting_api_key_input.setObjectName(
            "botHostingApiKeyInput"
        )
        self.bot_hosting_api_key_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )
        self.bot_hosting_api_key_input.setPlaceholderText(
            "Bot-Hosting API key stored securely in the OS credential store"
        )
        host_control_form.addRow(
            "Bot-Hosting API Key:",
            self.bot_hosting_api_key_input,
        )

        self.restart_mode_input = QComboBox()
        self.restart_mode_input.setObjectName(
            "restartModeInput"
        )
        self.restart_mode_input.addItem(
            "Simulated Restart",
            "simulated",
        )
        self.restart_mode_input.addItem(
            "Direct Restart",
            "direct",
        )
        host_control_form.addRow(
            "Restart Mode:",
            self.restart_mode_input,
        )

        maintenance_layout.addLayout(
            host_control_form
        )

        maintenance_button_row = QHBoxLayout()

        self.save_host_control_button = QPushButton(
            "Save Host Control"
        )
        self.save_host_control_button.setObjectName(
            "saveHostControlButton"
        )
        self.save_host_control_button.clicked.connect(
            save_host_control_callback
        )
        maintenance_button_row.addWidget(
            self.save_host_control_button
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
        maintenance_button_row.addWidget(
            self.restart_bot_button
        )

        maintenance_button_row.addStretch()

        maintenance_layout.addLayout(
            maintenance_button_row
        )

        group_layout.addWidget(
            self.maintenance_group
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

        scroll_area.setWidget(group)
        layout.addWidget(scroll_area)

    def control_network_password(self) -> str:
        return self.control_password_input.text().strip()

    def apply_pairing_state(
        self,
        *,
        paired: bool,
        client_id: str | None = None,
        password_saved: bool = False,
    ) -> None:
        self.control_password_input.clear()

        if password_saved:
            self.control_password_input.setPlaceholderText(
                "Control Network password saved securely"
            )
        else:
            self.control_password_input.setPlaceholderText(
                "Enter Control Network password"
            )

        if paired:
            if client_id:
                self.pairing_status_label.setText(
                    f"Paired as {client_id}"
                )
            else:
                self.pairing_status_label.setText(
                    "Paired"
                )
        else:
            self.pairing_status_label.setText(
                "Not paired"
            )

    def bot_hosting_deployment_id(self) -> str:
        return (
            self.bot_hosting_deployment_id_input
            .text()
            .strip()
        )

    def bot_hosting_api_key(self) -> str:
        return (
            self.bot_hosting_api_key_input
            .text()
            .strip()
        )

    def restart_mode(self) -> str:
        value = self.restart_mode_input.currentData()

        if value in {
            "simulated",
            "direct",
        }:
            return value

        return "simulated"

    def load_host_control_settings(
        self,
        deployment_id: str,
        restart_mode: str,
        *,
        api_key_saved: bool = False,
    ) -> None:
        self.bot_hosting_deployment_id_input.setText(
            deployment_id
        )

        normalized_mode = (
            restart_mode
            if restart_mode in {
                "simulated",
                "direct",
            }
            else "simulated"
        )

        index = self.restart_mode_input.findData(
            normalized_mode
        )

        if index >= 0:
            self.restart_mode_input.setCurrentIndex(
                index
            )

        self.bot_hosting_api_key_input.clear()

        if api_key_saved:
            self.bot_hosting_api_key_input.setPlaceholderText(
                "Bot-Hosting API key saved securely"
            )
        else:
            self.bot_hosting_api_key_input.setPlaceholderText(
                "Bot-Hosting API key stored securely in the OS credential store"
            )

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
            self.history_link.clear()
            self.help_link.clear()
            self.architecture_link.clear()
            return

        if self.public_web_mode() == "automatic":
            base_url = host
        else:
            if port is None:
                self.live_queue_link.clear()
                self.history_link.clear()
                self.help_link.clear()
                self.architecture_link.clear()
                return

            base_url = f"{host}:{port}"

        live_url = f"{base_url}/queue"
        history_url = f"{base_url}/history"
        help_url = f"{base_url}/help"
        architecture_url = (
            f"{base_url}/help/architecture"
        )

        self.live_queue_link.setText(
            f'Queue: '
            f'<a href="{live_url}">{live_url}</a>'
        )
        self.history_link.setText(
            f'History: '
            f'<a href="{history_url}">{history_url}</a>'
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
