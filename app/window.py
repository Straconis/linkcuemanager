import csv
import os
from urllib.parse import urlsplit
from PySide6.QtCore import QTimer, Qt, Signal
from datetime import datetime
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.bot_client import BotClient, BotClientError
from app.config import APP_NAME, APP_VERSION, DEFAULT_BOT_URL
from app.queue_event_listener import (
    QueueEventListener,
    websocket_events_url,
)
from app.pages.about_page import build_about_page
from app.pages.add_video_dialog import AddVideoDialog
from app.pages.bot_page import BotPage
from app.pages.queue_page import QueuePage
from app.pages.manager_page import ManagerPage
from app.pages.player_page import PlayerPage
from app.pages.streamer_page import StreamerPage
from app.pages.twitch_page import TwitchPage
from app.settings_store import (
    load_manager_settings,
    load_shared_settings,
    save_manager_settings,
    save_shared_settings,
)


class ManagerWindow(QMainWindow):
    queue_refresh_requested = Signal(dict)

    def __init__(self):
        super().__init__()

        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.resize(1000, 700)

        self.shared_settings = load_shared_settings()
        self.manager_settings = load_manager_settings()

        configured_url = os.getenv(
            "LINKCUE_BOT_URL",
            self.shared_settings.get(
                "bot_url",
                DEFAULT_BOT_URL,
            ),
        )

        parsed_url = urlsplit(configured_url)

        scheme = parsed_url.scheme or "http"
        hostname = parsed_url.hostname or "127.0.0.1"

        configured_port = os.getenv(
            "LINKCUE_BOT_PORT"
        )

        if configured_port is None:
            configured_port = self.shared_settings.get(
                "bot_port"
            )

        if configured_port is None:
            try:
                configured_port = parsed_url.port
            except ValueError:
                configured_port = None

        bot_port = int(configured_port or 8000)
        base_url = f"{scheme}://{hostname}"

        self.bot_client = BotClient(
            f"{base_url}:{bot_port}"
        )

        root = QWidget()
        root.setObjectName("managerRoot")
        self.setCentralWidget(root)

        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # -----------------------------------------------------
        # Navigation rail
        # -----------------------------------------------------

        self.navigation = QWidget()
        self.navigation.setObjectName("navigationRail")
        self.navigation.setMinimumWidth(170)
        self.navigation.setMaximumWidth(190)

        navigation_layout = QVBoxLayout(self.navigation)
        navigation_layout.setContentsMargins(12, 18, 12, 12)
        navigation_layout.setSpacing(6)

        logo = QLabel("LINKCUE")
        logo.setObjectName("navigationLogo")
        navigation_layout.addWidget(logo)

        subtitle = QLabel("MANAGER")
        subtitle.setObjectName("navigationSubtitle")
        navigation_layout.addWidget(subtitle)

        navigation_layout.addSpacing(18)

        self.navigation_buttons = {}

        for key, label in (
            ("queue", "Queue"),
            ("manager", "Manager"),
            ("bot", "Bot"),
            ("streamer", "Streamer"),
            ("twitch", "Twitch"),
            ("player", "Player"),
            ("about", "About"),
        ):
            button = QPushButton(label)
            button.setObjectName("navigationButton")
            button.setCheckable(True)
            navigation_layout.addWidget(button)
            self.navigation_buttons[key] = button

        navigation_layout.addStretch()

        root_layout.addWidget(self.navigation)

        # -----------------------------------------------------
        # Main content stack
        # -----------------------------------------------------

        self.page_stack = QStackedWidget()
        self.page_stack.setObjectName("pageStack")

        self.queue_page = QueuePage(
            self.refresh_queue,
            self.show_add_video_dialog,
            self.refresh_queue_metadata,
            self.export_queue_csv,
            self.export_history_csv,
            self.import_queue_csv,
            self.move_selected_to_beginning,
            self.move_selected_up,
            self.move_selected_down,
            self.move_selected_to_end,
            self.remove_selected,
            self.clear_queue,
        )

        self.manager_page = ManagerPage(
            self.set_dark_mode,
            self.save_manager_preferences,
            self.restore_manager_defaults,
        )

        self.bot_page = BotPage(
            base_url,
            bot_port,
            self.save_bot_url,
            self.test_connection,
            self.toggle_public_web,
            self.refresh_public_web_setting,
            self.save_logging_setting,
            self.refresh_logging_setting,
            self.restart_bot,
        )

        self.twitch_page = TwitchPage(
            self.join_channel,
            self.leave_channel,
            self.refresh_twitch_status,
        )

        self.player_page = PlayerPage(
            self.refresh_player_status
        )

        self.streamer_page = StreamerPage(
            self.save_streamer_settings
        )

        self.about_page = build_about_page()

        for page in (
            self.queue_page,
            self.manager_page,
            self.bot_page,
            self.streamer_page,
            self.twitch_page,
            self.player_page,
            self.about_page,
        ):
            self.page_stack.addWidget(page)

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        content_layout.addWidget(self.page_stack, 1)

        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("statusLabel")
        content_layout.addWidget(self.status_label)

        root_layout.addLayout(content_layout, 1)

        self.navigation_buttons["queue"].clicked.connect(
            lambda: self._show_page(0, "queue")
        )
        self.navigation_buttons["manager"].clicked.connect(
            lambda: self._show_page(1, "manager")
        )
        self.navigation_buttons["bot"].clicked.connect(
            lambda: self._show_page(2, "bot")
        )
        self.navigation_buttons["streamer"].clicked.connect(
            lambda: self._show_page(3, "streamer")
        )
        self.navigation_buttons["twitch"].clicked.connect(
            lambda: self._show_page(4, "twitch")
        )
        self.navigation_buttons["player"].clicked.connect(
            lambda: self._show_page(5, "player")
        )
        self.navigation_buttons["about"].clicked.connect(
            lambda: self._show_page(6, "about")
        )

        self._show_page(0, "queue")

        manager_username = str(
            self.manager_settings.get(
                "manager_username",
                "",
            )
        )

        dark_mode_enabled = bool(
            self.manager_settings.get(
                "dark_mode",
                False,
            )
        )

        self.manager_page.load_settings(
            manager_username,
            dark_mode_enabled,
        )

        streamer_name = str(
            self.manager_settings.get(
                "streamer_name",
                "",
            )
        )

        streamer_twitch_url = str(
            self.manager_settings.get(
                "streamer_twitch_url",
                "",
            )
        )

        populate_from_twitch = bool(
            self.manager_settings.get(
                "populate_from_twitch_url",
                False,
            )
        )

        self.streamer_page.load_settings(
            streamer_name,
            streamer_twitch_url,
            populate_from_twitch,
        )

        if (
            populate_from_twitch
            and streamer_name
        ):
            self.twitch_page.set_channel(
                streamer_name
            )

        self.set_dark_mode(
            dark_mode_enabled
        )

        self.queue_refresh_requested.connect(
            self.refresh_queue
        )

        self.queue_event_listener = QueueEventListener(
            base_url,
            self.queue_refresh_requested.emit,
        )
        self.queue_event_listener.start()

        # Establish initial state once the UI event loop starts.
        QTimer.singleShot(0, self.refresh_queue)
        QTimer.singleShot(0, self.refresh_player_status)
        QTimer.singleShot(
            0,
            self.refresh_public_web_setting,
        )
        QTimer.singleShot(
            0,
            self.refresh_logging_setting,
        )

    def _show_page(self, index: int, key: str) -> None:
        self.page_stack.setCurrentIndex(index)

        for name, button in self.navigation_buttons.items():
            button.setChecked(name == key)

    def set_dark_mode(self, enabled: bool) -> None:
        if enabled:
            self.setStyleSheet(
                """
                /* =====================================================
                   LINKCUE MANAGER
                   Dark dashboard theme
                   ===================================================== */

                QMainWindow,
                QWidget#managerRoot {
                    background-color: #111318;
                    color: #f1f3f5;
                }

                /* -----------------------------------------------------
                   Navigation rail
                   ----------------------------------------------------- */

                QWidget#navigationRail {
                    background-color: #171a20;
                    border-right: 1px solid #292e38;
                }

                QLabel#navigationLogo {
                    color: #f4f7fb;
                    font-size: 18px;
                    font-weight: 800;
                    letter-spacing: 1px;
                }

                QLabel#navigationSubtitle {
                    color: #7f8ba3;
                    font-size: 11px;
                    font-weight: 700;
                    letter-spacing: 2px;
                }

                QPushButton#navigationButton {
                    background-color: transparent;
                    color: #aeb7c7;
                    border: 1px solid transparent;
                    border-radius: 8px;
                    padding: 12px 14px;
                    min-height: 44px;
                    text-align: left;
                    font-size: 13px;
                    font-weight: 600;
                }

                QPushButton#navigationButton:hover {
                    background-color: #202631;
                    color: #f1f3f5;
                }

                QPushButton#navigationButton:checked {
                    background-color: #294b7d;
                    color: #ffffff;
                    border: 1px solid #3e6eaf;
                }

                QPushButton#darkModeButton {
                    background-color: #20242c;
                    color: #aeb7c7;
                    border: 1px solid #343b48;
                    border-radius: 8px;
                    padding: 9px 12px;
                    min-height: 38px;
                }

                QPushButton#darkModeButton:hover {
                    background-color: #292f39;
                    color: #ffffff;
                }

                /* -----------------------------------------------------
                   Main content
                   ----------------------------------------------------- */

                QWidget#pageStack {
                    background-color: #111318;
                }

                QLabel#pageTitle {
                    color: #6fa8ff;
                    font-size: 12px;
                    font-weight: 800;
                    letter-spacing: 1px;
                }

                QLabel#pageDescription {
                    color: #8993a5;
                    font-size: 13px;
                }

                QGroupBox QLabel {
                    color: #d7dde8;
                }

                /* -----------------------------------------------------
                   Cards / group boxes
                   ----------------------------------------------------- */

                QGroupBox {
                    background-color: #171a20;
                    border: 1px solid #2d3542;
                    border-radius: 12px;
                    margin-top: 12px;
                    padding: 20px 16px 16px 16px;
                    font-size: 12px;
                    font-weight: 700;
                    color: #6fa8ff;
                }

                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 14px;
                    padding: 0 7px;
                    color: #6fa8ff;
                    background-color: #171a20;
                }

                /* -----------------------------------------------------
                   Inputs
                   ----------------------------------------------------- */

                QLineEdit {
                    background-color: #101217;
                    color: #f1f3f5;
                    border: 1px solid #343c49;
                    border-radius: 9px;
                    padding: 9px 12px;
                    min-height: 36px;
                    selection-background-color: #315a99;
                }

                QLineEdit:focus {
                    border: 1px solid #4f8fe8;
                }

                QLineEdit::placeholder {
                    color: #697386;
                }

                /* -----------------------------------------------------
                   Buttons
                   ----------------------------------------------------- */

                QPushButton {
                    background-color: #20252d;
                    color: #e8ecf2;
                    border: 1px solid #343c49;
                    border-radius: 9px;
                    padding: 9px 15px;
                    min-height: 36px;
                    font-size: 12px;
                    font-weight: 600;
                }

                QPushButton:hover {
                    background-color: #2a313c;
                    border-color: #4b596d;
                }

                QPushButton:pressed {
                    background-color: #1b2028;
                }

                QPushButton:disabled {
                    background-color: #191c22;
                    color: #555d6b;
                    border-color: #252a32;
                }

                QPushButton#addQueueButton,
                QPushButton#addNextButton {
                    background-color: #3568ad;
                    border-color: #4d82cc;
                    color: #ffffff;
                }

                QPushButton#addQueueButton:hover,
                QPushButton#addNextButton:hover {
                    background-color: #4078c3;
                    border-color: #6b9ee1;
                }

                QPushButton#removeSelectedButton,
                QPushButton#leaveButton {
                    background-color: #292127;
                    border-color: #553740;
                    color: #e7aeb8;
                }

                QPushButton#removeSelectedButton:hover,
                QPushButton#leaveButton:hover {
                    background-color: #3a252d;
                    border-color: #754653;
                }

                /* -----------------------------------------------------
                   Queue
                   ----------------------------------------------------- */

                QLabel#playerCountLabel,
                QLabel#managerCountLabel {
                    color: #8f9aad;
                    font-size: 11px;
                }

                QTableWidget {
                    background-color: #12151a;
                    alternate-background-color: #151920;
                    color: #e7ebf1;
                    border: 1px solid #2d3542;
                    border-radius: 10px;
                    gridline-color: #252c36;
                    selection-background-color: #263c63;
                    selection-color: #ffffff;
                }

                QTableWidget::item {
                    padding: 7px;
                    border-bottom: 1px solid #20252e;
                }

                QTableWidget::item:selected {
                    background-color: #263c63;
                }

                QHeaderView::section {
                    background-color: #1d2129;
                    color: #8792a4;
                    border: none;
                    border-right: 1px solid #2b313d;
                    border-bottom: 1px solid #303744;
                    padding: 8px;
                    font-size: 11px;
                    font-weight: 700;
                }

                /* -----------------------------------------------------
                   Status / secondary lists
                   ----------------------------------------------------- */

                QListWidget {
                    background-color: #12151a;
                    color: #e7ebf1;
                    border: 1px solid #2d3542;
                    border-radius: 10px;
                    padding: 5px;
                }

                QLabel#queuePositionBadge {
                    background-color: #151a22;
                    color: #f1f3f5;
                    border: 1px solid #486581;
                    border-radius: 6px;
                    font-weight: 600;
                    font-size: 14px;
                }

                QLabel#statusLabel {
                    background-color: #171b22;
                    color: #aeb8c7;
                    border: 1px solid #2b3442;
                    border-radius: 5px;
                    padding: 7px 10px;
                    margin: 6px 8px 8px 8px;
                    font-size: 11px;
                }

                /* -----------------------------------------------------
                   Scrollbars
                   ----------------------------------------------------- */

                QScrollBar:vertical {
                    background: #111318;
                    width: 10px;
                    margin: 2px;
                }

                QScrollBar::handle:vertical {
                    background: #343b48;
                    border-radius: 5px;
                    min-height: 30px;
                }

                QScrollBar::handle:vertical:hover {
                    background: #465163;
                }

                QScrollBar::add-line:vertical,
                QScrollBar::sub-line:vertical {
                    height: 0px;
                }
                """
            )
            self.status_label.setText("Dark mode enabled.")
        else:
            self.setStyleSheet(
                """
                /* =====================================================
                   LINKCUE MANAGER
                   Light dashboard theme
                   ===================================================== */

                QMainWindow,
                QWidget#managerRoot {
                    background-color: #f4f6f9;
                    color: #20252d;
                }

                /* -----------------------------------------------------
                   Navigation rail
                   ----------------------------------------------------- */

                QWidget#navigationRail {
                    background-color: #e9edf3;
                    border-right: 1px solid #d5dbe4;
                }

                QLabel#navigationLogo {
                    color: #1d2735;
                    font-size: 18px;
                    font-weight: 800;
                    letter-spacing: 1px;
                }

                QLabel#navigationSubtitle {
                    color: #718096;
                    font-size: 11px;
                    font-weight: 700;
                    letter-spacing: 2px;
                }

                QPushButton#navigationButton {
                    background-color: transparent;
                    color: #536174;
                    border: 1px solid transparent;
                    border-radius: 8px;
                    padding: 12px 14px;
                    min-height: 44px;
                    text-align: left;
                    font-size: 13px;
                    font-weight: 600;
                }

                QPushButton#navigationButton:hover {
                    background-color: #dfe6ef;
                    color: #1f2a38;
                }

                QPushButton#navigationButton:checked {
                    background-color: #d8e5f7;
                    color: #1f579b;
                    border: 1px solid #a9c7ec;
                }

                QPushButton#darkModeButton {
                    background-color: #f1f3f6;
                    color: #536174;
                    border: 1px solid #cfd6e0;
                    border-radius: 8px;
                    padding: 9px 12px;
                    min-height: 38px;
                }

                QPushButton#darkModeButton:hover {
                    background-color: #e5e9ef;
                    color: #263445;
                }

                /* -----------------------------------------------------
                   Main content
                   ----------------------------------------------------- */

                QWidget#pageStack {
                    background-color: #f4f6f9;
                }

                QLabel#pageTitle {
                    color: #3568ad;
                    font-size: 12px;
                    font-weight: 800;
                    letter-spacing: 1px;
                }

                QLabel#pageDescription {
                    color: #697789;
                    font-size: 13px;
                }

                /* -----------------------------------------------------
                   Cards / group boxes
                   ----------------------------------------------------- */

                QGroupBox {
                    background-color: #f8fafc;
                    border: 1px solid #d5dce6;
                    border-radius: 12px;
                    margin-top: 12px;
                    padding: 20px 16px 16px 16px;
                    font-size: 12px;
                    font-weight: 700;
                    color: #3568ad;
                }

                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 14px;
                    padding: 0 7px;
                    color: #3568ad;
                    background-color: #f8fafc;
                }

                /* -----------------------------------------------------
                   Inputs
                   ----------------------------------------------------- */

                QLineEdit {
                    background-color: #ffffff;
                    color: #20252d;
                    border: 1px solid #cfd6e0;
                    border-radius: 9px;
                    padding: 9px 12px;
                    min-height: 36px;
                    selection-background-color: #bcd4f3;
                    selection-color: #182230;
                }

                QLineEdit:focus {
                    border: 1px solid #4f8fe8;
                }

                QLineEdit::placeholder {
                    color: #8b96a5;
                }

                /* -----------------------------------------------------
                   Buttons
                   ----------------------------------------------------- */

                QPushButton {
                    background-color: #eef1f5;
                    color: #354253;
                    border: 1px solid #cbd3de;
                    border-radius: 9px;
                    padding: 9px 15px;
                    min-height: 36px;
                }

                QPushButton:hover {
                    background-color: #e2e7ee;
                    border-color: #b9c4d2;
                }

                QPushButton:pressed {
                    background-color: #d7dee8;
                }

                QPushButton:disabled {
                    background-color: #eef0f3;
                    color: #a0a8b3;
                    border-color: #d9dee5;
                }

                /* Primary actions */

                QPushButton#addQueueButton,
                QPushButton#addNextButton {
                    background-color: #3568ad;
                    border-color: #4d82cc;
                    color: #ffffff;
                }

                QPushButton#addQueueButton:hover,
                QPushButton#addNextButton:hover {
                    background-color: #4078c3;
                    border-color: #6093dc;
                }

                QPushButton#addQueueButton:pressed,
                QPushButton#addNextButton:pressed {
                    background-color: #2d5d9e;
                }

                /* Destructive action */

                QPushButton#removeSelectedButton {
                    background-color: #faf4f5;
                    color: #a33d4b;
                    border: 1px solid #d9aeb5;
                }

                QPushButton#removeSelectedButton:hover {
                    background-color: #f5e5e8;
                    border-color: #c98b95;
                    color: #8e2f3d;
                }

                /* -----------------------------------------------------
                   Tables
                   ----------------------------------------------------- */

                QTableWidget {
                    background-color: #ffffff;
                    alternate-background-color: #f7f9fb;
                    color: #273343;
                    border: 1px solid #d5dce6;
                    border-radius: 10px;
                    gridline-color: #e2e6ec;
                    selection-background-color: #dbe9fa;
                    selection-color: #1f2f43;
                }

                QHeaderView::section {
                    background-color: #eef1f5;
                    color: #526174;
                    border: none;
                    border-right: 1px solid #d9dfe7;
                    border-bottom: 1px solid #d5dce6;
                    padding: 7px 8px;
                    font-weight: 700;
                }

                QTableWidget::item {
                    padding: 6px;
                }

                QTableWidget::item:selected {
                    background-color: #dbe9fa;
                    color: #1f2f43;
                }

                /* -----------------------------------------------------
                   Lists / combo boxes
                   ----------------------------------------------------- */

                QListWidget,
                QComboBox {
                    background-color: #ffffff;
                    color: #273343;
                    border: 1px solid #d5dce6;
                    border-radius: 10px;
                    padding: 5px;
                }

                QListWidget::item:selected {
                    background-color: #dbe9fa;
                    color: #1f2f43;
                }

                QComboBox:focus {
                    border: 1px solid #4f8fe8;
                }

                /* -----------------------------------------------------
                   Status text
                   ----------------------------------------------------- */

                QLabel#playerCountLabel,
                QLabel#managerCountLabel {
                    color: #66758a;
                }

                QLabel#queuePositionBadge {
                    background-color: #eef3f8;
                    color: #203040;
                    border: 1px solid #9eb3c9;
                    border-radius: 6px;
                    font-weight: 600;
                    font-size: 14px;
                }

                QLabel#statusLabel {
                    background-color: #ffffff;
                    color: #4f5d6d;
                    border: 1px solid #cbd3dd;
                    border-radius: 5px;
                    padding: 7px 10px;
                    margin: 6px 8px 8px 8px;
                    font-size: 11px;
                }
                """
            )
            self.status_label.setText("Dark mode disabled.")

    def _update_client(self) -> None:
        base_url = self.bot_page.bot_url()

        self.bot_client = BotClient(base_url)

        if (
            hasattr(self, "queue_event_listener")
            and self.queue_event_listener.url
            != websocket_events_url(base_url)
        ):
            self.queue_event_listener.stop()
            self.queue_event_listener = QueueEventListener(
                base_url,
                self.queue_refresh_requested.emit,
            )
            self.queue_event_listener.start()

    def _stop_background_services(self) -> None:
        self.queue_event_listener.stop()

    def save_manager_preferences(self) -> None:
        manager_settings = load_manager_settings()
        manager_settings["manager_username"] = (
            self.manager_page.manager_username()
        )
        manager_settings["dark_mode"] = (
            self.manager_page.dark_mode_enabled()
        )

        save_manager_settings(manager_settings)
        self.manager_settings = manager_settings

        self.status_label.setText(
            "Manager settings saved."
        )

    def restore_manager_defaults(self) -> None:
        self.manager_page.restore_defaults()

        self.status_label.setText(
            "Manager defaults restored. "
            "Save Settings to make them permanent."
        )

    def closeEvent(self, event) -> None:
        self._stop_background_services()
        super().closeEvent(event)

    def _show_error(self, exc: Exception) -> None:
        self.status_label.setText(str(exc))

    def save_bot_url(self) -> None:
        bot_host = self.bot_page.bot_host()
        bot_port = self.bot_page.bot_port()

        if not bot_host:
            parsed_default = urlsplit(
                DEFAULT_BOT_URL
            )

            scheme = (
                parsed_default.scheme
                or "http"
            )
            hostname = (
                parsed_default.hostname
                or "127.0.0.1"
            )

            bot_host = (
                f"{scheme}://{hostname}"
            )

        public_web_port = (
            self.bot_page.public_web_port()
        )
        public_web_enabled = (
            self.bot_page.requested_public_web_enabled()
        )

        try:
            result = self.bot_client.set_bot_connection(
                bot_host,
                bot_port,
            )

            public_web_result = (
                self.bot_client.set_public_web_enabled(
                    public_web_enabled,
                    public_web_port,
                )
            )
        except BotClientError as exc:
            self._show_error(exc)
            return

        shared_settings = load_shared_settings()
        shared_settings["bot_url"] = bot_host
        shared_settings["bot_port"] = bot_port
        save_shared_settings(shared_settings)

        self.shared_settings = shared_settings

        self._apply_public_web_setting(
            bool(
                public_web_result.get(
                    "enabled"
                )
            ),
            public_web_result.get("port"),
        )

        restart_required = bool(
            result.get("restart_required")
        )

        self.status_label.setText(
            "Bot settings saved. Bot restart required."
            if restart_required
            else "Bot settings saved."
        )

    def test_connection(self) -> None:
        self._update_client()

        try:
            result = self.bot_client.health()
        except BotClientError as exc:
            self.bot_page.set_connection_offline()
            self._show_error(exc)
            return

        version = result.get("version", "unknown")
        self.bot_page.set_connection_version(
            str(version)
        )
        self.status_label.setText("Bot connection successful.")

    def _apply_public_web_setting(
        self,
        enabled: bool,
        port: int | None = None,
    ) -> None:
        self.bot_page.apply_public_web_setting(
            enabled,
            port,
        )

    def refresh_public_web_setting(self) -> None:
        self._update_client()

        try:
            result = self.bot_client.public_web_setting()
        except BotClientError as exc:
            self.bot_page.set_public_web_unavailable()
            self._show_error(exc)
            return

        self._apply_public_web_setting(
            bool(result.get("enabled")),
            result.get("port"),
        )

        self.status_label.setText(
            "Public web setting refreshed."
        )

    def toggle_public_web(self) -> None:
        self._update_client()

        requested = self.bot_page.requested_public_web_enabled()

        try:
            result = self.bot_client.set_public_web_enabled(
                requested,
                self.bot_page.public_web_port(),
            )
        except BotClientError as exc:
            self.refresh_public_web_setting()
            self._show_error(exc)
            return

        enabled = bool(result.get("enabled"))
        self._apply_public_web_setting(
            enabled,
            result.get("port"),
        )

        self.status_label.setText(
            "Public web enabled."
            if enabled
            else "Public web disabled."
        )

    def _apply_logging_setting(
        self,
        enabled: bool,
        timezone_name: str,
    ) -> None:
        self.bot_page.apply_logging_setting(
            enabled,
            timezone_name,
        )


    def refresh_logging_setting(self) -> None:
        self._update_client()

        try:
            result = self.bot_client.logging_setting()
        except BotClientError as exc:
            self.bot_page.set_logging_unavailable()
            self._show_error(exc)
            return

        self._apply_logging_setting(
            bool(result.get("enabled")),
            str(
                result.get(
                    "timezone",
                    "America/Detroit",
                )
            ),
        )

        self.status_label.setText(
            "Logging setting refreshed."
        )


    def save_logging_setting(self) -> None:
        self._update_client()

        try:
            result = self.bot_client.set_logging_setting(
                self.bot_page.requested_logging_enabled(),
                self.bot_page.logging_timezone(),
            )
        except BotClientError as exc:
            self._show_error(exc)
            return

        self._apply_logging_setting(
            bool(result.get("enabled")),
            str(
                result.get(
                    "timezone",
                    "America/Detroit",
                )
            ),
        )

        self.status_label.setText(
            "Logging settings saved."
        )


    def restart_bot(self) -> None:
        from PySide6.QtWidgets import QMessageBox

        message_box = QMessageBox(self)
        message_box.setWindowTitle("Restart Bot")
        message_box.setIcon(QMessageBox.Icon.Information)
        message_box.setText(
            "Restart Bot control is not implemented yet.\n\n"
            "This button is a development placeholder.\n"
            "No restart will occur."
        )
        message_box.setStandardButtons(
            QMessageBox.StandardButton.Ok
        )
        message_box.setStyleSheet(
            """
            QMessageBox {
                background-color: #1e232b;
            }

            QMessageBox QLabel {
                color: #d7dde8;
            }

            QMessageBox QPushButton {
                background-color: #2b313b;
                color: #f2f4f8;
                border: 1px solid #48515f;
                border-radius: 6px;
                padding: 6px 14px;
                min-width: 70px;
            }

            QMessageBox QPushButton:hover {
                background-color: #343b46;
            }

            QMessageBox QPushButton:pressed {
                background-color: #252b33;
            }
            """
        )
        message_box.exec()

    def refresh_player_status(self) -> None:
        self._update_client()

        try:
            presence = self.bot_client.player_status()
            playback = self.bot_client.player_state()
        except BotClientError as exc:
            self.player_page.show_unavailable()
            self._show_error(exc)
            return

        self.player_page.apply_status(
            presence,
            playback,
        )

        self.status_label.setText(
            "Player status refreshed."
        )


    def save_streamer_settings(self) -> None:
        streamer_name = (
            self.streamer_page.streamer_name()
        )
        twitch_url = (
            self.streamer_page.twitch_url()
        )
        populate_from_twitch = (
            self.streamer_page.populate_from_twitch_enabled()
        )

        if populate_from_twitch:
            parse_url = twitch_url

            if "://" not in parse_url:
                parse_url = f"https://{parse_url}"

            parsed = urlsplit(parse_url)

            hostname = (
                parsed.hostname or ""
            ).lower()

            valid_hosts = {
                "twitch.tv",
                "www.twitch.tv",
                "m.twitch.tv",
            }

            path_parts = [
                part
                for part in parsed.path.split("/")
                if part
            ]

            if (
                hostname not in valid_hosts
                or not path_parts
            ):
                self.status_label.setText(
                    "Unable to populate fields: "
                    "enter a valid Twitch channel URL."
                )
                return

            streamer_name = path_parts[0]

            self.streamer_page.set_streamer_name(
                streamer_name
            )

            self.twitch_page.set_channel(
                streamer_name
            )

        manager_settings = load_manager_settings()

        manager_settings["streamer_name"] = (
            streamer_name
        )
        manager_settings["streamer_twitch_url"] = (
            twitch_url
        )
        manager_settings["populate_from_twitch_url"] = (
            populate_from_twitch
        )

        save_manager_settings(
            manager_settings
        )

        self.manager_settings = manager_settings

        self.status_label.setText(
            "Streamer settings saved."
        )

    def refresh_twitch_status(self) -> None:
        self._update_client()

        try:
            result = self.bot_client.twitch_status()
        except BotClientError as exc:
            self._show_error(exc)
            return

        self.twitch_page.apply_status(
            result,
            use_connected_flag=True,
        )

        self.status_label.setText(
            "Twitch status refreshed."
        )

    def join_channel(self) -> None:
        channel = self.twitch_page.entered_channel()

        if not channel:
            self.status_label.setText(
                "Enter a Twitch channel name."
            )
            return

        self._update_client()

        try:
            result = self.bot_client.join_twitch_channel(
                channel
            )
        except BotClientError as exc:
            self._show_error(exc)
            return

        self.twitch_page.clear_channel_input()
        self._apply_twitch_result(result)

    def leave_channel(self) -> None:
        channel = self.twitch_page.entered_channel()

        if not channel:
            channel = self.twitch_page.selected_channel()

        if not channel:
            self.status_label.setText(
                "Enter or select a Twitch channel."
            )
            return

        self._update_client()

        try:
            result = self.bot_client.leave_twitch_channel(
                channel
            )
        except BotClientError as exc:
            self._show_error(exc)
            return

        self.twitch_page.clear_channel_input()
        self._apply_twitch_result(result)

    def _apply_twitch_result(self, result: dict) -> None:
        self.twitch_page.apply_status(result)

        self.status_label.setText(
            result.get("status", "Twitch state updated.")
        )

    def export_queue_csv(self) -> None:
        self._update_client()

        try:
            items = self.bot_client.queue()
        except BotClientError as exc:
            self._show_error(exc)
            return

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export LinkCue Queue",
            f"linkcue_queue_{timestamp}.csv",
            "CSV Files (*.csv)",
        )

        if not file_path:
            return

        fieldnames = [
            "position",
            "url",
            "title",
            "channel",
            "platform",
            "duration",
            "submitted_by",
            "status",
        ]

        try:
            with open(
                file_path,
                "w",
                newline="",
                encoding="utf-8-sig",
            ) as csv_file:
                writer = csv.DictWriter(
                    csv_file,
                    fieldnames=fieldnames,
                    extrasaction="ignore",
                )
                writer.writeheader()

                for item in items:
                    writer.writerow(
                        {
                            "position": item.get("position"),
                            "url": item.get("url"),
                            "title": item.get("title"),
                            "channel": (
                                item.get("video_channel")
                                or item.get("channel")
                            ),
                            "platform": item.get("platform"),
                            "duration": item.get("duration"),
                            "submitted_by": item.get(
                                "submitted_by"
                            ),
                            "status": item.get("status"),
                        }
                    )
        except OSError as exc:
            self.status_label.setText(
                f"Queue export failed: {exc}"
            )
            return

        self.status_label.setText(
            f"Exported {len(items)} queue item(s)."
        )

    def export_history_csv(self) -> None:
        self._update_client()

        try:
            items = self.bot_client.history()
        except BotClientError as exc:
            self._show_error(exc)
            return

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export LinkCue History",
            f"linkcue_history_{timestamp}.csv",
            "CSV Files (*.csv)",
        )

        if not file_path:
            return

        fieldnames = [
            "url",
            "title",
            "channel",
            "platform",
            "duration",
            "submitted_by",
            "status",
            "created_at",
            "started_at",
            "played_at",
        ]

        try:
            with open(
                file_path,
                "w",
                newline="",
                encoding="utf-8-sig",
            ) as csv_file:
                writer = csv.DictWriter(
                    csv_file,
                    fieldnames=fieldnames,
                    extrasaction="ignore",
                )
                writer.writeheader()

                for item in items:
                    writer.writerow(
                        {
                            "url": item.get("url"),
                            "title": item.get("title"),
                            "channel": (
                                item.get("video_channel")
                                or item.get("channel")
                            ),
                            "platform": item.get("platform"),
                            "duration": item.get("duration"),
                            "submitted_by": item.get(
                                "submitted_by"
                            ),
                            "status": item.get("status"),
                            "created_at": item.get("created_at"),
                            "started_at": item.get("started_at"),
                            "played_at": item.get("played_at"),
                        }
                    )
        except OSError as exc:
            self.status_label.setText(
                f"History export failed: {exc}"
            )
            return

        self.status_label.setText(
            f"Exported {len(items)} history item(s)."
        )

    def import_queue_csv(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import LinkCue Queue",
            "",
            "CSV Files (*.csv)",
        )

        if not file_path:
            return

        try:
            with open(
                file_path,
                "r",
                newline="",
                encoding="utf-8-sig",
            ) as csv_file:
                reader = csv.DictReader(csv_file)

                if reader.fieldnames is None:
                    self.status_label.setText(
                        "Queue import failed: CSV has no header."
                    )
                    return

                normalized_headers = {
                    header.strip()
                    for header in reader.fieldnames
                    if header is not None
                }

                missing = {
                    "position",
                    "url",
                } - normalized_headers

                if missing:
                    self.status_label.setText(
                        "Queue import failed: required column(s) "
                        + ", ".join(sorted(missing))
                        + " missing."
                    )
                    return

                rows = []

                for line_number, row in enumerate(
                    reader,
                    start=2,
                ):
                    raw_position = (
                        row.get("position") or ""
                    ).strip()
                    url = (
                        row.get("url") or ""
                    ).strip()

                    if not raw_position:
                        self.status_label.setText(
                            "Queue import failed: "
                            f"line {line_number} has no position."
                        )
                        return

                    try:
                        position = int(raw_position)
                    except ValueError:
                        self.status_label.setText(
                            "Queue import failed: "
                            f"line {line_number} has an invalid position."
                        )
                        return

                    if position < 1:
                        self.status_label.setText(
                            "Queue import failed: "
                            f"line {line_number} position must be positive."
                        )
                        return

                    if not url:
                        self.status_label.setText(
                            "Queue import failed: "
                            f"line {line_number} has no URL."
                        )
                        return

                    rows.append(
                        {
                            "position": position,
                            "url": url,
                            "title": (
                                row.get("title") or ""
                            ).strip(),
                            "channel": (
                                row.get("channel") or ""
                            ).strip(),
                            "submitted_by": (
                                row.get("submitted_by") or ""
                            ).strip(),
                        }
                    )

        except (OSError, csv.Error) as exc:
            self.status_label.setText(
                f"Queue import failed: {exc}"
            )
            return

        positions = [
            row["position"]
            for row in rows
        ]

        if len(positions) != len(set(positions)):
            self.status_label.setText(
                "Queue import failed: duplicate positions found."
            )
            return

        rows.sort(
            key=lambda row: row["position"]
        )

        self._update_client()

        imported = 0
        already_queued = 0
        failed = 0

        for row in rows:
            try:
                self.bot_client.add_queue_item(
                    row["url"],
                    title=row["title"] or None,
                    video_channel=(
                        row["channel"] or None
                    ),
                    submitted_by=(
                        row["submitted_by"] or None
                    ),
                )
                imported += 1

            except BotClientError as exc:
                if exc.status_code == 409:
                    already_queued += 1
                else:
                    failed += 1

        self.refresh_queue()

        self.status_label.setText(
            "Import complete: "
            f"{imported} added, "
            f"{already_queued} already queued, "
            f"{failed} failed."
        )

    def show_add_video_dialog(self) -> None:
        dialog = AddVideoDialog(self)

        if dialog.exec() != dialog.DialogCode.Accepted:
            return

        url = dialog.video_url()

        if not url:
            self.status_label.setText(
                "Enter a video URL."
            )
            return

        self._update_client()

        try:
            result = self.bot_client.add_queue_item(
                url,
                submitted_by=(
                    self.manager_page.manager_username()
                    or None
                ),
            )

            if dialog.behavior() == AddVideoDialog.ADD_NEXT:
                item_id = result.get("id")

                if item_id is None:
                    raise BotClientError(
                        "Bot did not return a queue item ID"
                    )

                self.bot_client.move_queue_item(
                    int(item_id),
                    1,
                )

        except BotClientError as exc:
            self._show_error(exc)
            return

        self.refresh_queue()

        if dialog.behavior() == AddVideoDialog.ADD_NEXT:
            self.status_label.setText(
                "Video added next."
            )
        else:
            self.status_label.setText(
                "Video added to end of queue."
            )

    def refresh_queue_metadata(self) -> None:
        self._update_client()

        try:
            self.bot_client.refresh_queue_metadata()
        except BotClientError as exc:
            self._show_error(exc)
            return

        self.refresh_queue()
        self.status_label.setText(
            "Queue metadata refresh requested."
        )

    def _selected_queue_item(self) -> tuple[int, int] | None:
        row = self.queue_page.queue_table.currentRow()

        if row < 0:
            self.status_label.setText("Select a queue item first.")
            return None

        model_item = self.queue_page.queue_table.item(row, 0)

        if model_item is None:
            self.status_label.setText("Selected queue item is invalid.")
            return None

        item_id = model_item.data(Qt.ItemDataRole.UserRole)
        position = model_item.data(Qt.ItemDataRole.UserRole + 1)

        if item_id is None:
            self.status_label.setText("Selected queue item has no ID.")
            return None

        if position is None:
            self.status_label.setText("Selected queue item has no position.")
            return None

        try:
            return int(item_id), int(position)
        except (TypeError, ValueError):
            self.status_label.setText(
                "Selected queue item has invalid queue data."
            )
            return None

    def _move_selected_to(
        self,
        target_position: int,
        success_message: str,
    ) -> None:
        selected = self._selected_queue_item()

        if selected is None:
            return

        item_id, current_position = selected
        queue_length = self.queue_page.queue_table.rowCount()

        if target_position < 1:
            target_position = 1

        if target_position > queue_length:
            target_position = queue_length

        if target_position == current_position:
            self.status_label.setText(
                "Queue item is already in that position."
            )
            return

        self._update_client()

        try:
            self.bot_client.move_queue_item(
                item_id,
                target_position,
            )
        except BotClientError as exc:
            self._show_error(exc)
            return

        self.refresh_queue()
        self.status_label.setText(success_message)

    def _move_selected(self, delta: int) -> None:
        selected = self._selected_queue_item()

        if selected is None:
            return

        _, current_position = selected
        target_position = current_position + delta

        if target_position < 1:
            self.status_label.setText("Queue item is already at the top.")
            return

        if target_position > self.queue_page.queue_table.rowCount():
            self.status_label.setText("Queue item is already at the bottom.")
            return

        if delta < 0:
            message = "Queue item moved up."
        else:
            message = "Queue item moved down."

        self._move_selected_to(
            target_position,
            message,
        )

    def move_selected_to_beginning(self) -> None:
        self._move_selected_to(
            1,
            "Queue item moved to beginning.",
        )

    def move_selected_up(self) -> None:
        self._move_selected(-1)

    def move_selected_down(self) -> None:
        self._move_selected(1)

    def move_selected_to_end(self) -> None:
        self._move_selected_to(
            self.queue_page.queue_table.rowCount(),
            "Queue item moved to end.",
        )

    def remove_selected(self) -> None:
        row = self.queue_page.queue_table.currentRow()

        if row < 0:
            self.status_label.setText("Select a queue item first.")
            return

        first_item = self.queue_page.queue_table.item(row, 0)

        if first_item is None:
            self.status_label.setText("Selected queue item is invalid.")
            return

        item_id = first_item.data(Qt.ItemDataRole.UserRole)

        if item_id is None:
            self.status_label.setText("Selected queue item has no ID.")
            return

        self._update_client()

        try:
            self.bot_client.remove_queue_item(int(item_id))
        except BotClientError as exc:
            self._show_error(exc)
            return

        self.refresh_queue()
        self.status_label.setText("Queue item removed.")


    def clear_queue(self) -> None:
        queue_count = self.queue_page.queue_table.rowCount()

        if queue_count == 0:
            self.status_label.setText("Queue is already empty.")
            return

        message_box = QMessageBox(self)
        message_box.setWindowTitle("Clear Queue")
        message_box.setIcon(QMessageBox.Icon.Warning)
        message_box.setText("Clear the entire queue?")
        message_box.setInformativeText(
            f"This will remove all {queue_count} queued video(s). "
            "This cannot be undone."
        )

        clear_button = message_box.addButton(
            "Clear Queue",
            QMessageBox.ButtonRole.DestructiveRole,
        )
        cancel_button = message_box.addButton(
            "Cancel",
            QMessageBox.ButtonRole.RejectRole,
        )

        message_box.setDefaultButton(cancel_button)
        message_box.setEscapeButton(cancel_button)
        message_box.exec()

        if message_box.clickedButton() is not clear_button:
            self.status_label.setText("Clear queue cancelled.")
            return

        self._update_client()

        try:
            result = self.bot_client.clear_queue()
        except BotClientError as exc:
            self._show_error(exc)
            return

        deleted_count = result.get("deleted_count", 0)

        self.refresh_queue()
        self.status_label.setText(
            f"Cleared {deleted_count} queue item(s)."
        )


    def _update_presence_counts(self, event: dict) -> None:
        self.queue_page.player_count_label.setText(
            f"Players Connected: {event.get('player_count', 0)}"
        )
        self.queue_page.manager_count_label.setText(
            f"Managers Connected: {event.get('manager_count', 0)} (including this instance)"
        )


    def refresh_queue(self, event: dict | None = None) -> None:
        if event:
            event_type = event.get("type")

            if event_type == "connected":
                self._update_presence_counts(event)

                snapshot = event.get("snapshot")
                if snapshot is not None:
                    self._apply_queue_snapshot(snapshot)
                    return
            elif event_type == "manager_presence_changed":
                self.queue_page.manager_count_label.setText(
                    f"Managers Connected: {event.get('manager_count', 0)} (including this instance)"
                )
            elif event_type == "player_presence_changed":
                self.queue_page.player_count_label.setText(
                    f"Players Connected: {event.get('player_count', 0)}"
                )

            if event_type in {
                "manager_presence_changed",
                "player_presence_changed",
            }:
                return

            if event_type == "queue_changed":
                snapshot = event.get("snapshot")

                if snapshot is not None:
                    self._apply_queue_snapshot(snapshot)
                    return

        self._update_client()

        try:
            items = self.bot_client.queue()
        except BotClientError as exc:
            self._show_error(exc)
            return

        self._render_queue(items)

    def _apply_queue_snapshot(self, snapshot: dict) -> None:
        items = snapshot.get("queued", [])
        self._render_queue(items)

    def _render_queue(self, items: list[dict]) -> None:
        self.queue_page.render_items(items)
