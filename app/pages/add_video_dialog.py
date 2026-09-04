from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)


class AddVideoDialog(QDialog):
    ADD_TO_END = "Add to End of Queue"
    ADD_NEXT = "Add Next"

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Add Video")
        self.setModal(True)
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Video URL"))

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText(
            "YouTube or TikTok URL"
        )
        layout.addWidget(self.url_input)

        layout.addWidget(QLabel("Queue Behavior"))

        self.behavior_combo = QComboBox()
        self.behavior_combo.addItems(
            [
                self.ADD_TO_END,
                self.ADD_NEXT,
            ]
        )
        layout.addWidget(self.behavior_combo)

        button_row = QHBoxLayout()
        button_row.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        add_button = QPushButton("Add")
        add_button.setObjectName("addVideoDialogAddButton")
        add_button.clicked.connect(self.accept)
        add_button.setDefault(True)

        button_row.addWidget(cancel_button)
        button_row.addWidget(add_button)

        layout.addLayout(button_row)

    def video_url(self) -> str:
        return self.url_input.text().strip()

    def behavior(self) -> str:
        return self.behavior_combo.currentText()
