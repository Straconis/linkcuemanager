from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.config import APP_NAME, APP_VERSION


def build_about_page() -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(18, 18, 18, 12)

    title = QLabel("ABOUT LINKCUE")
    title.setObjectName("pageTitle")
    layout.addWidget(title)

    info = QLabel(
        f"{APP_NAME} {APP_VERSION}\n\n"
        "Central management console for the LinkCue Bot."
    )
    info.setObjectName("pageDescription")
    layout.addWidget(info)

    layout.addStretch()

    return page

