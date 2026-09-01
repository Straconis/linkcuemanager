import os
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
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


class ManagerWindow(QMainWindow):
    queue_refresh_requested = Signal(dict)

    def __init__(self):
        super().__init__()

        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.resize(1000, 700)

        base_url = os.getenv(
            "LINKCUE_BOT_URL",
            DEFAULT_BOT_URL,
        )
        self.bot_client = BotClient(base_url)

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
            ("queue", "?  Queue"),
            ("bot", "?  Bot"),
            ("twitch", "?  Twitch"),
            ("streamer", "?  Streamer"),
            ("player", "?  Player"),
            ("about", "?  About"),
        ):
            button = QPushButton(label)
            button.setObjectName("navigationButton")
            button.setCheckable(True)
            navigation_layout.addWidget(button)
            self.navigation_buttons[key] = button

        navigation_layout.addStretch()

        self.dark_mode_button = QPushButton("Dark Mode")
        self.dark_mode_button.setObjectName("darkModeButton")
        self.dark_mode_button.setCheckable(True)
        self.dark_mode_button.toggled.connect(
            self.set_dark_mode
        )
        navigation_layout.addWidget(self.dark_mode_button)

        root_layout.addWidget(self.navigation)

        # -----------------------------------------------------
        # Main content stack
        # -----------------------------------------------------

        self.page_stack = QStackedWidget()
        self.page_stack.setObjectName("pageStack")

        self.queue_page = QWidget()
        queue_layout = QVBoxLayout(self.queue_page)
        queue_layout.setContentsMargins(18, 18, 18, 12)
        queue_layout.setSpacing(10)

        self.queue_page_title = QLabel("QUEUE MANAGEMENT")
        self.queue_page_title.setObjectName("pageTitle")
        queue_layout.addWidget(self.queue_page_title)

        queue_layout.addWidget(self._build_queue_section(), 1)

        self.bot_page = QWidget()
        bot_layout = QVBoxLayout(self.bot_page)
        bot_layout.setContentsMargins(18, 18, 18, 12)
        bot_layout.addWidget(self._build_bot_section())
        bot_layout.addStretch()

        self.twitch_page = QWidget()
        twitch_layout = QVBoxLayout(self.twitch_page)
        twitch_layout.setContentsMargins(18, 18, 18, 12)
        twitch_layout.addWidget(self._build_twitch_section())
        twitch_layout.addStretch()

        self.player_page = QWidget()
        player_layout = QVBoxLayout(self.player_page)
        player_layout.setContentsMargins(18, 18, 18, 12)
        player_layout.addWidget(self._build_player_section())
        player_layout.addStretch()

        self.streamer_page = QWidget()
        streamer_layout = QVBoxLayout(self.streamer_page)
        streamer_layout.setContentsMargins(18, 18, 18, 12)

        streamer_title = QLabel("STREAMER")
        streamer_title.setObjectName("pageTitle")
        streamer_layout.addWidget(streamer_title)

        streamer_info = QLabel(
            "Streamer-specific controls will appear here."
        )
        streamer_info.setObjectName("pageDescription")
        streamer_layout.addWidget(streamer_info)
        streamer_layout.addStretch()

        self.about_page = QWidget()
        about_layout = QVBoxLayout(self.about_page)
        about_layout.setContentsMargins(18, 18, 18, 12)

        about_title = QLabel("ABOUT LINKCUE")
        about_title.setObjectName("pageTitle")
        about_layout.addWidget(about_title)

        about_info = QLabel(
            f"{APP_NAME} {APP_VERSION}\n\n"
            "Central management console for the LinkCue Bot."
        )
        about_info.setObjectName("pageDescription")
        about_layout.addWidget(about_info)
        about_layout.addStretch()

        for page in (
            self.queue_page,
            self.bot_page,
            self.twitch_page,
            self.streamer_page,
            self.player_page,
            self.about_page,
        ):
            self.page_stack.addWidget(page)

        root_layout.addWidget(self.page_stack, 1)

        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("statusLabel")

        self.navigation_buttons["queue"].clicked.connect(
            lambda: self._show_page(0, "queue")
        )
        self.navigation_buttons["bot"].clicked.connect(
            lambda: self._show_page(1, "bot")
        )
        self.navigation_buttons["twitch"].clicked.connect(
            lambda: self._show_page(2, "twitch")
        )
        self.navigation_buttons["streamer"].clicked.connect(
            lambda: self._show_page(3, "streamer")
        )
        self.navigation_buttons["player"].clicked.connect(
            lambda: self._show_page(4, "player")
        )
        self.navigation_buttons["about"].clicked.connect(
            lambda: self._show_page(5, "about")
        )

        self._show_page(0, "queue")
        self.set_dark_mode(False)

        self.queue_refresh_requested.connect(
            self.refresh_queue
        )

        self.queue_event_listener = QueueEventListener(
            base_url,
            self.queue_refresh_requested.emit,
        )
        self.queue_event_listener.start()

        # Establish the initial Player state once the UI event loop starts.
        QTimer.singleShot(0, self.refresh_player_status)

    def _build_bot_section(self) -> QGroupBox:
        group = QGroupBox("LinkCue Bot")
        layout = QHBoxLayout(group)

        layout.addWidget(QLabel("Bot URL:"))

        self.bot_url_input = QLineEdit(self.bot_client.base_url)
        self.bot_url_input.setObjectName("botUrlInput")
        layout.addWidget(self.bot_url_input, 1)

        self.test_connection_button = QPushButton("Test Connection")
        self.test_connection_button.setObjectName(
            "testConnectionButton"
        )
        self.test_connection_button.clicked.connect(
            self.test_connection
        )
        layout.addWidget(self.test_connection_button)

        layout.addWidget(QLabel("Status:"))

        self.bot_status_label = QLabel("Not checked")
        self.bot_status_label.setObjectName("botStatusLabel")
        self.bot_status_label.setMinimumWidth(120)
        layout.addWidget(self.bot_status_label)

        return group

    def _build_player_section(self) -> QGroupBox:
        group = QGroupBox("LinkCue Player")
        layout = QHBoxLayout(group)

        layout.addWidget(QLabel("Player:"))

        self.player_status_label = QLabel("Not checked")
        self.player_status_label.setObjectName(
            "playerStatusLabel"
        )
        layout.addWidget(self.player_status_label)

        layout.addSpacing(20)
        layout.addWidget(QLabel("Playback:"))

        self.playback_status_label = QLabel("Not checked")
        self.playback_status_label.setObjectName(
            "playbackStatusLabel"
        )
        layout.addWidget(self.playback_status_label)

        layout.addSpacing(20)
        layout.addWidget(QLabel("Now Playing:"))

        self.now_playing_label = QLabel("None")
        self.now_playing_label.setObjectName(
            "nowPlayingLabel"
        )
        layout.addWidget(self.now_playing_label, 1)

        self.refresh_player_button = QPushButton("Refresh Player")
        self.refresh_player_button.setObjectName(
            "refreshPlayerButton"
        )
        self.refresh_player_button.clicked.connect(
            self.refresh_player_status
        )
        layout.addWidget(self.refresh_player_button)

        return group

    def _build_twitch_section(self) -> QGroupBox:
        group = QGroupBox("Twitch Channels")
        layout = QVBoxLayout(group)

        controls = QHBoxLayout()

        self.channel_input = QLineEdit()
        self.channel_input.setObjectName("channelInput")
        self.channel_input.setPlaceholderText(
            "Twitch channel name"
        )

        self.join_button = QPushButton("Join Channel")
        self.join_button.setObjectName("joinButton")
        self.join_button.clicked.connect(
            self.join_channel
        )

        self.leave_button = QPushButton("Leave Channel")
        self.leave_button.setObjectName("leaveButton")
        self.leave_button.clicked.connect(
            self.leave_channel
        )

        self.refresh_twitch_button = QPushButton("Refresh")
        self.refresh_twitch_button.setObjectName(
            "refreshTwitchButton"
        )
        self.refresh_twitch_button.clicked.connect(
            self.refresh_twitch_status
        )

        controls.addWidget(self.channel_input, 1)
        controls.addWidget(self.join_button)
        controls.addWidget(self.leave_button)
        controls.addWidget(self.refresh_twitch_button)

        layout.addLayout(controls)

        self.twitch_status_label = QLabel("Not checked")
        self.twitch_status_label.setObjectName(
            "twitchStatusLabel"
        )
        layout.addWidget(self.twitch_status_label)

        self.channel_list = QListWidget()
        self.channel_list.setObjectName("channelList")
        self.channel_list.setMaximumHeight(90)
        layout.addWidget(self.channel_list)

        return group

    def _build_queue_section(self) -> QGroupBox:
        group = QGroupBox("Queue")
        layout = QVBoxLayout(group)

        header = QHBoxLayout()

        title = QLabel("Current Bot Queue")
        title.setStyleSheet("font-weight: bold;")

        self.player_count_label = QLabel("Players Connected: 0")
        self.player_count_label.setObjectName("playerCountLabel")

        self.manager_count_label = QLabel("Managers Connected: 0 (including this instance)")
        self.manager_count_label.setObjectName("managerCountLabel")


        self.refresh_queue_button = QPushButton("Refresh Queue")
        self.refresh_queue_button.setObjectName(
            "refreshQueueButton"
        )
        self.refresh_queue_button.clicked.connect(
            self.refresh_queue
        )

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.player_count_label)
        header.addSpacing(12)
        header.addWidget(self.manager_count_label)
        header.addSpacing(12)
        header.addWidget(self.refresh_queue_button)

        layout.addLayout(header)

        controls = QHBoxLayout()

        self.queue_url_input = QLineEdit()
        self.queue_url_input.setObjectName("queueUrlInput")
        self.queue_url_input.setPlaceholderText(
            "YouTube or TikTok URL"
        )

        self.add_queue_button = QPushButton("Add to Queue")
        self.add_queue_button.setObjectName("addQueueButton")
        self.add_queue_button.clicked.connect(
            self.add_to_queue
        )

        self.add_next_button = QPushButton("Add Next")
        self.add_next_button.setObjectName("addNextButton")
        self.add_next_button.clicked.connect(
            self.add_next
        )

        self.remove_selected_button = QPushButton("Remove Selected")
        self.remove_selected_button.setObjectName(
            "removeSelectedButton"
        )
        self.remove_selected_button.clicked.connect(
            self.remove_selected
        )

        self.move_up_button = QPushButton("Move Up")
        self.move_up_button.setObjectName("moveUpButton")
        self.move_up_button.clicked.connect(
            self.move_selected_up
        )

        self.move_down_button = QPushButton("Move Down")
        self.move_down_button.setObjectName("moveDownButton")
        self.move_down_button.clicked.connect(
            self.move_selected_down
        )

        controls.addWidget(self.queue_url_input, 1)
        controls.addWidget(self.add_queue_button)
        controls.addWidget(self.add_next_button)
        controls.addWidget(self.move_up_button)
        controls.addWidget(self.move_down_button)
        controls.addWidget(self.remove_selected_button)

        layout.addLayout(controls)

        self.queue_table = QTableWidget(0, 5)
        self.queue_table.setObjectName("queueTable")
        self.queue_table.setHorizontalHeaderLabels(
            [
                "Position",
                "Title",
                "Platform",
                "Submitted By",
                "Status",
            ]
        )
        self.queue_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.queue_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.queue_table.horizontalHeader().setStretchLastSection(
            True
        )

        layout.addWidget(self.queue_table)

        return group

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

                QLabel#statusLabel {
                    color: #727d90;
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

                QLabel#statusLabel {
                    color: #687789;
                }
                """
            )
            self.status_label.setText("Dark mode disabled.")

    def _update_client(self) -> None:
        base_url = self.bot_url_input.text().strip()

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

    def closeEvent(self, event) -> None:
        self._stop_background_services()
        super().closeEvent(event)

    def _show_error(self, exc: Exception) -> None:
        self.status_label.setText(str(exc))

    def test_connection(self) -> None:
        self._update_client()

        try:
            result = self.bot_client.health()
        except BotClientError as exc:
            self.bot_status_label.setText("Offline")
            self._show_error(exc)
            return

        version = result.get("version", "unknown")
        self.bot_status_label.setText(
            f"Connected - Bot {version}"
        )
        self.status_label.setText("Bot connection successful.")

    def refresh_player_status(self) -> None:
        self._update_client()

        try:
            presence = self.bot_client.player_status()
            playback = self.bot_client.player_state()
        except BotClientError as exc:
            self.player_status_label.setText("Offline")
            self.playback_status_label.setText("Unknown")
            self.now_playing_label.setText("None")
            self._show_error(exc)
            return

        if presence.get("active"):
            self.player_status_label.setText("Active")
        else:
            self.player_status_label.setText("Offline")

        state = playback.get("state", "unknown")

        if state == "playing":
            self.playback_status_label.setText("Playing")
        elif state == "idle":
            self.playback_status_label.setText("Idle")
        else:
            self.playback_status_label.setText(
                str(state).title()
            )

        item = playback.get("item")

        if item:
            title = item.get("title") or item.get("url") or "Untitled video"
            self.now_playing_label.setText(str(title))
        else:
            self.now_playing_label.setText("None")

        self.status_label.setText("Player status refreshed.")


    def refresh_twitch_status(self) -> None:
        self._update_client()

        try:
            result = self.bot_client.twitch_status()
        except BotClientError as exc:
            self._show_error(exc)
            return

        channels = result.get("channels", [])

        self.channel_list.clear()
        self.channel_list.addItems(channels)

        if result.get("connected"):
            self.twitch_status_label.setText(
                f"Active - {{len(channels)}} channel(s)"
            )
        else:
            self.twitch_status_label.setText("Inactive")

        self.status_label.setText(
            "Twitch status refreshed."
        )

    def join_channel(self) -> None:
        channel = self.channel_input.text().strip()

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

        self.channel_input.clear()
        self._apply_twitch_result(result)

    def leave_channel(self) -> None:
        channel = self.channel_input.text().strip()

        if not channel:
            selected = self.channel_list.currentItem()

            if selected is not None:
                channel = selected.text()

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

        self.channel_input.clear()
        self._apply_twitch_result(result)

    def _apply_twitch_result(self, result: dict) -> None:
        channels = result.get("channels", [])

        self.channel_list.clear()
        self.channel_list.addItems(channels)

        if channels:
            self.twitch_status_label.setText(
                f"Active - {{len(channels)}} channel(s)"
            )
        else:
            self.twitch_status_label.setText("Inactive")

        self.status_label.setText(
            result.get("status", "Twitch state updated.")
        )

    def add_to_queue(self) -> None:
        url = self.queue_url_input.text().strip()

        if not url:
            self.status_label.setText("Enter a video URL.")
            return

        self._update_client()

        try:
            self.bot_client.add_queue_item(url)
        except BotClientError as exc:
            self._show_error(exc)
            return

        self.queue_url_input.clear()
        self.refresh_queue()
        self.status_label.setText("Video added to queue.")

    def add_next(self) -> None:
        url = self.queue_url_input.text().strip()

        if not url:
            self.status_label.setText("Enter a video URL.")
            return

        self._update_client()

        try:
            result = self.bot_client.add_queue_item(url)
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

        self.queue_url_input.clear()
        self.refresh_queue()
        self.status_label.setText("Video added next.")

    def _move_selected(self, delta: int) -> None:
        row = self.queue_table.currentRow()

        if row < 0:
            self.status_label.setText("Select a queue item first.")
            return

        first_item = self.queue_table.item(row, 0)

        if first_item is None:
            self.status_label.setText("Selected queue item is invalid.")
            return

        item_id = first_item.data(Qt.ItemDataRole.UserRole)

        if item_id is None:
            self.status_label.setText("Selected queue item has no ID.")
            return

        position_item = self.queue_table.item(
            row,
            0,
        )

        if position_item is None:
            self.status_label.setText("Selected queue item has no position.")
            return

        try:
            current_position = int(position_item.text())
        except ValueError:
            self.status_label.setText(
                "Selected queue item has an invalid position."
            )
            return

        target_position = current_position + delta

        if target_position < 1:
            self.status_label.setText("Queue item is already at the top.")
            return

        if target_position > self.queue_table.rowCount():
            self.status_label.setText("Queue item is already at the bottom.")
            return

        self._update_client()

        try:
            self.bot_client.move_queue_item(
                int(item_id),
                target_position,
            )
        except BotClientError as exc:
            self._show_error(exc)
            return

        self.refresh_queue()

        if delta < 0:
            self.status_label.setText("Queue item moved up.")
        else:
            self.status_label.setText("Queue item moved down.")

    def move_selected_up(self) -> None:
        self._move_selected(-1)

    def move_selected_down(self) -> None:
        self._move_selected(1)

    def remove_selected(self) -> None:
        row = self.queue_table.currentRow()

        if row < 0:
            self.status_label.setText("Select a queue item first.")
            return

        first_item = self.queue_table.item(row, 0)

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


    def _update_presence_counts(self, event: dict) -> None:
        self.player_count_label.setText(
            f"Players Connected: {event.get('player_count', 0)}"
        )
        self.manager_count_label.setText(
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
                self.manager_count_label.setText(
                    f"Managers Connected: {event.get('manager_count', 0)} (including this instance)"
                )
            elif event_type == "player_presence_changed":
                self.player_count_label.setText(
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
        self.queue_table.setRowCount(len(items))

        for row, item in enumerate(items):
            values = [
                item.get("position"),
                item.get("title") or item.get("url"),
                item.get("platform"),
                item.get("submitted_by"),
                item.get("status"),
            ]

            for column, value in enumerate(values):
                table_item = QTableWidgetItem(
                    "" if value is None else str(value)
                )
                table_item.setTextAlignment(
                    Qt.AlignmentFlag.AlignVCenter
                    | Qt.AlignmentFlag.AlignLeft
                )

                if column == 0:
                    table_item.setData(
                        Qt.ItemDataRole.UserRole,
                        item.get("id"),
                    )

                self.queue_table.setItem(
                    row,
                    column,
                    table_item,
                )

        self.queue_table.resizeColumnsToContents()
        self.status_label.setText(
            f"Queue synchronized - {len(items)} item(s)."
        )
