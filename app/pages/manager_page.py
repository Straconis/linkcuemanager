from collections.abc import Callable

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QAbstractButton,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ToggleSwitch(QAbstractButton):
    """Compact on/off slider switch."""

    def __init__(
        self,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(44, 24)

    def sizeHint(self) -> QSize:
        return QSize(44, 24)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        track = QRectF(
            1,
            3,
            self.width() - 2,
            self.height() - 6,
        )

        if self.isChecked():
            track_color = QColor("#3b82f6")
        else:
            track_color = QColor("#596273")

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(track_color)
        painter.drawRoundedRect(
            track,
            track.height() / 2,
            track.height() / 2,
        )

        knob_size = 18
        knob_y = (self.height() - knob_size) / 2

        if self.isChecked():
            knob_x = self.width() - knob_size - 3
        else:
            knob_x = 3

        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(
            QRectF(
                knob_x,
                knob_y,
                knob_size,
                knob_size,
            )
        )


class ManagerPage(QWidget):
    def __init__(
        self,
        dark_mode_callback: Callable[[bool], None],
        save_callback: Callable[[], None],
        restore_defaults_callback: Callable[[], None],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 12)
        layout.setSpacing(10)

        title = QLabel("MANAGER SETTINGS")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        description = QLabel(
            "Settings specific to this LinkCue Manager installation."
        )
        description.setObjectName("pageDescription")
        layout.addWidget(description)

        group = QGroupBox("Manager")
        group_layout = QVBoxLayout(group)

        username_row = QHBoxLayout()
        username_row.addWidget(
            QLabel("Manager Username:")
        )

        self.manager_username_input = QLineEdit()
        self.manager_username_input.setObjectName(
            "managerUsernameInput"
        )
        self.manager_username_input.setPlaceholderText(
            "Manager Username"
        )
        self.manager_username_input.setMaximumWidth(300)

        username_row.addWidget(
            self.manager_username_input
        )
        username_row.addStretch()

        group_layout.addLayout(username_row)

        dark_mode_row = QHBoxLayout()

        dark_mode_label = QLabel("Dark Mode:")
        dark_mode_row.addWidget(dark_mode_label)

        self.dark_mode_toggle = ToggleSwitch()
        self.dark_mode_toggle.setObjectName(
            "darkModeToggle"
        )
        self.dark_mode_toggle.setAccessibleName(
            "Dark Mode"
        )
        self.dark_mode_toggle.toggled.connect(
            dark_mode_callback
        )

        dark_mode_row.addWidget(
            self.dark_mode_toggle
        )
        dark_mode_row.addStretch()

        group_layout.addLayout(dark_mode_row)

        button_row = QHBoxLayout()
        button_row.addStretch()

        self.restore_defaults_button = QPushButton(
            "Restore Defaults"
        )
        self.restore_defaults_button.setObjectName(
            "restoreManagerDefaultsButton"
        )
        self.restore_defaults_button.clicked.connect(
            restore_defaults_callback
        )

        self.save_settings_button = QPushButton(
            "Save Settings"
        )
        self.save_settings_button.setObjectName(
            "saveManagerSettingsButton"
        )
        self.save_settings_button.clicked.connect(
            save_callback
        )

        button_row.addWidget(
            self.restore_defaults_button
        )
        button_row.addWidget(
            self.save_settings_button
        )

        group_layout.addLayout(button_row)

        layout.addWidget(group)
        layout.addStretch()

    def manager_username(self) -> str:
        return self.manager_username_input.text().strip()

    def dark_mode_enabled(self) -> bool:
        return self.dark_mode_toggle.isChecked()

    def load_settings(
        self,
        manager_username: str,
        dark_mode_enabled: bool,
    ) -> None:
        self.manager_username_input.setText(
            manager_username
        )

        self.dark_mode_toggle.blockSignals(True)
        self.dark_mode_toggle.setChecked(
            dark_mode_enabled
        )
        self.dark_mode_toggle.blockSignals(False)

    def restore_defaults(self) -> None:
        self.manager_username_input.clear()
        self.dark_mode_toggle.setChecked(False)
