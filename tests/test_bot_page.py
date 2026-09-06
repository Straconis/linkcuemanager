import app.pages.bot_page as bot_page_module
from app.pages.bot_page import BotPage
from PySide6.QtWidgets import QApplication


def _build_page(qtbot, *, mode="automatic"):
    page = BotPage(
        "https://linkcue.apps.bot-hosting.cloud",
        8000,
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
        connection_mode=mode,
    )
    qtbot.addWidget(page)
    return page


def test_automatic_mode_uses_portless_bot_url(qtbot):
    page = _build_page(qtbot)

    assert page.connection_mode() == "automatic"
    assert (
        page.bot_url()
        == "https://linkcue.apps.bot-hosting.cloud"
    )


def test_manual_mode_uses_bot_port(qtbot):
    page = _build_page(qtbot, mode="manual")

    assert page.connection_mode() == "manual"
    assert (
        page.bot_url()
        == "https://linkcue.apps.bot-hosting.cloud:8000"
    )


def test_automatic_mode_keeps_manual_port_value(qtbot):
    page = _build_page(qtbot)

    page.bot_port_input.setText("9123")

    assert page.bot_port() == 9123
    assert (
        page.bot_url()
        == "https://linkcue.apps.bot-hosting.cloud"
    )


def test_automatic_public_links_do_not_require_web_port(qtbot):
    page = _build_page(qtbot)

    page.apply_public_web_setting(
        True,
        public_url="https://linkcue.apps.bot-hosting.cloud",
    )

    assert (
        'href="https://linkcue.apps.bot-hosting.cloud/queue"'
        in page.live_queue_link.text()
    )
    assert (
        'href="https://linkcue.apps.bot-hosting.cloud/history"'
        in page.history_link.text()
    )
    assert (
        'href="https://linkcue.apps.bot-hosting.cloud/help"'
        in page.help_link.text()
    )


def test_bot_manual_mode_does_not_force_public_web_manual(qtbot):
    page = _build_page(qtbot, mode="manual")

    page.public_web_port_input.setText("9000")
    page.apply_public_web_setting(
        True,
        public_url="https://linkcue.apps.bot-hosting.cloud",
    )

    assert page.connection_mode() == "manual"
    assert page.public_web_mode() == "automatic"
    assert (
        'href="https://linkcue.apps.bot-hosting.cloud/queue"'
        in page.live_queue_link.text()
    )

def test_connection_mode_selector_is_available(qtbot):
    page = _build_page(qtbot)

    assert page.connection_mode_input.count() == 2
    assert page.connection_mode_input.itemData(0) == "automatic"
    assert page.connection_mode_input.itemData(1) == "manual"
    assert page.connection_mode() == "automatic"


def test_connection_mode_can_switch_to_manual(qtbot):
    page = _build_page(qtbot)

    page.connection_mode_input.setCurrentIndex(1)

    assert page.connection_mode() == "manual"
    assert (
        page.bot_url()
        == "https://linkcue.apps.bot-hosting.cloud:8000"
    )


def test_public_web_has_independent_host_and_mode(qtbot):
    page = _build_page(qtbot, mode="manual")

    assert hasattr(page, "public_web_url_input")
    assert hasattr(page, "public_web_mode_input")

    page.public_web_url_input.setText(
        "linkcue.apps.bot-hosting.cloud"
    )
    page.public_web_mode_input.setCurrentIndex(0)

    assert page.connection_mode() == "manual"
    assert page.public_web_mode() == "automatic"


def test_public_web_automatic_uses_own_portless_host(qtbot):
    page = _build_page(qtbot, mode="manual")

    page.public_web_url_input.setText(
        "linkcue.apps.bot-hosting.cloud"
    )
    page.public_web_protocol_input.setCurrentText("https://")
    page.public_web_mode_input.setCurrentIndex(0)
    page.public_web_port_input.setText("9000")

    page.apply_public_web_setting(True)

    assert (
        'href="https://linkcue.apps.bot-hosting.cloud/queue"'
        in page.live_queue_link.text()
    )


def test_public_web_manual_uses_own_port(qtbot):
    page = _build_page(qtbot)

    page.public_web_url_input.setText(
        "linkcue.apps.bot-hosting.cloud"
    )
    page.public_web_protocol_input.setCurrentText("https://")
    page.public_web_mode_input.setCurrentIndex(1)
    page.public_web_port_input.setText("9000")

    page.apply_public_web_setting(True)

    assert (
        'href="https://linkcue.apps.bot-hosting.cloud:9000/queue"'
        in page.live_queue_link.text()
    )


def test_bot_protocol_is_independent_of_host(qtbot):
    page = _build_page(qtbot, mode="manual")

    page.bot_protocol_input.setCurrentText("http://")
    page.bot_url_input.setText("de1.bot-hosting.cloud")
    page.bot_port_input.setText("25479")

    assert (
        page.bot_url()
        == "http://de1.bot-hosting.cloud:25479"
    )


def test_pasting_full_bot_url_updates_protocol_and_host(qtbot):
    page = _build_page(qtbot)

    page.bot_url_input.setText(
        "https://example.com"
    )
    page.normalize_bot_url_input()

    assert page.bot_protocol_input.currentText() == "https://"
    assert page.bot_url_input.text() == "example.com"
    assert page.bot_host() == "https://example.com"



def test_empty_bot_host_returns_empty_string(qtbot):
    page = _build_page(qtbot)

    page.bot_url_input.clear()

    assert page.bot_host() == ""




def test_pasted_public_web_url_normalizes_protocol_and_host(qtbot):
    page = _build_page(qtbot)

    page.public_web_protocol_input.setCurrentText("http://")
    page.public_web_url_input.setText(
        "https://linkcue.apps.bot-hosting.cloud"
    )

    page.normalize_public_web_url_input()

    assert (
        page.public_web_protocol_input.currentText()
        == "https://"
    )
    assert (
        page.public_web_url_input.text()
        == "linkcue.apps.bot-hosting.cloud"
    )
    assert (
        page.public_web_host()
        == "https://linkcue.apps.bot-hosting.cloud"
    )



def test_bot_and_public_web_hosts_have_room_for_hostnames(qtbot):
    page = _build_page(qtbot)

    assert page.bot_url_input.minimumWidth() >= 280
    assert page.public_web_url_input.minimumWidth() >= 280

    assert (
        page.bot_url_input.minimumWidth()
        > page.bot_port_input.maximumWidth()
    )
    assert (
        page.public_web_url_input.minimumWidth()
        > page.public_web_port_input.maximumWidth()
    )

def test_bot_connection_url_does_not_seed_public_web_url(qtbot):
    page = BotPage(
        "http://de1.bot-hosting.cloud",
        25479,
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
        connection_mode="manual",
    )
    qtbot.addWidget(page)

    assert page.bot_url_input.text() == "de1.bot-hosting.cloud"
    assert page.public_web_url_input.text() == ""


def test_bot_tab_has_scoped_settings_groups(qtbot):
    page = _build_page(qtbot)

    assert page.connection_group.title() == "Bot Connection"
    assert page.public_web_group.title() == "Public Web"
    assert page.logging_group.title() == "Logging"
    assert page.maintenance_group.title() == "Maintenance"

    assert (
        page.connection_group.objectName()
        == "botConnectionGroup"
    )
    assert (
        page.public_web_group.objectName()
        == "publicWebGroup"
    )
    assert (
        page.logging_group.objectName()
        == "loggingGroup"
    )
    assert (
        page.maintenance_group.objectName()
        == "maintenanceGroup"
    )


def test_bot_tab_save_buttons_name_their_scope(qtbot):
    page = _build_page(qtbot)

    assert (
        page.save_bot_url_button.text()
        == "Save Connection"
    )
    assert (
        page.save_public_web_button.text()
        == "Save Public Web"
    )
    assert (
        page.save_logging_button.text()
        == "Save Logging"
    )


def test_bot_tab_has_no_restart_placeholder_note(qtbot):
    page = _build_page(qtbot)

    assert not hasattr(
        page,
        "restart_bot_note",
    )

def test_public_web_links_copy_url_to_clipboard(
    qtbot,
    monkeypatch,
):
    page = _build_page(qtbot)

    page.apply_public_web_setting(
        True,
        public_url="https://linkcue.apps.bot-hosting.cloud",
    )

    class FakeMenu:
        def __init__(self, parent):
            self.action = object()

        def addAction(self, text):
            assert text == "Copy Link"
            return self.action

        def exec(self, position):
            return self.action

    monkeypatch.setattr(
        bot_page_module,
        "QMenu",
        FakeMenu,
    )

    cases = [
        (
            page.live_queue_link,
            "https://linkcue.apps.bot-hosting.cloud/queue",
        ),
        (
            page.history_link,
            "https://linkcue.apps.bot-hosting.cloud/history",
        ),
        (
            page.help_link,
            "https://linkcue.apps.bot-hosting.cloud/help",
        ),
        (
            page.architecture_link,
            "https://linkcue.apps.bot-hosting.cloud/help/architecture",
        ),
    ]

    clipboard = QApplication.clipboard()

    for label, expected_url in cases:
        clipboard.clear()

        page._show_public_link_context_menu(
            label,
            label.rect().center(),
        )

        assert clipboard.text() == expected_url



def test_host_control_defaults_to_simulated_restart(qtbot):
    page = _build_page(qtbot)

    assert page.restart_mode() == "simulated"
    assert page.bot_hosting_deployment_id() == ""
    assert page.bot_hosting_api_key() == ""


def test_host_control_settings_can_be_loaded(qtbot):
    page = _build_page(qtbot)

    page.load_host_control_settings(
        "deployment-123",
        "direct",
        api_key_saved=True,
    )

    assert (
        page.bot_hosting_deployment_id()
        == "deployment-123"
    )
    assert page.restart_mode() == "direct"
    assert page.bot_hosting_api_key() == ""
    assert (
        page.bot_hosting_api_key_input.placeholderText()
        == "Bot-Hosting API key saved securely"
    )


def test_invalid_restart_mode_falls_back_to_simulated(qtbot):
    page = _build_page(qtbot)

    page.load_host_control_settings(
        "deployment-123",
        "definitely-not-valid",
    )

    assert page.restart_mode() == "simulated"


def test_host_control_api_key_is_password_masked(qtbot):
    page = _build_page(qtbot)

    assert (
        page.bot_hosting_api_key_input.echoMode()
        == page.bot_hosting_api_key_input.EchoMode.Password
    )


def test_save_host_control_button_calls_callback(qtbot):
    calls = []

    page = BotPage(
        "https://linkcue.apps.bot-hosting.cloud",
        8000,
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: calls.append("saved"),
        lambda: None,
        connection_mode="automatic",
    )
    qtbot.addWidget(page)

    page.save_host_control_button.click()

    assert calls == ["saved"]


def _build_pairing_page(qtbot):
    page = BotPage(
        "https://linkcue.apps.bot-hosting.cloud",
        8000,
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
        pair_manager_callback=lambda: None,
        connection_mode="automatic",
    )
    qtbot.addWidget(page)
    return page


def test_bot_tab_has_linkcue_security_pairing_group(qtbot):
    page = _build_pairing_page(qtbot)

    assert page.security_group.title() == "LinkCue Security"
    assert (
        page.security_group.objectName()
        == "linkCueSecurityGroup"
    )

    assert (
        page.control_password_input.objectName()
        == "controlNetworkPasswordInput"
    )
    assert (
        page.pair_manager_button.text()
        == "Pair This Manager"
    )


def test_control_network_password_is_masked(qtbot):
    page = _build_pairing_page(qtbot)

    assert (
        page.control_password_input.echoMode()
        == page.control_password_input.EchoMode.Password
    )


def test_control_network_password_accessor_strips_whitespace(qtbot):
    page = _build_pairing_page(qtbot)

    page.control_password_input.setText(
        "  shared-password  "
    )

    assert (
        page.control_network_password()
        == "shared-password"
    )


def test_pairing_status_can_show_saved_and_paired_state(qtbot):
    page = _build_pairing_page(qtbot)

    page.apply_pairing_state(
        paired=True,
        client_id="manager-example",
        password_saved=True,
    )

    assert "manager-example" in page.pairing_status_label.text()
    assert (
        page.control_password_input.text()
        == ""
    )
    assert (
        page.control_password_input.placeholderText()
        == "Control Network password saved securely"
    )
