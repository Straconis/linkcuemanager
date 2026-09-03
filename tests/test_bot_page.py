from app.pages.bot_page import BotPage


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
        'href="https://linkcue.apps.bot-hosting.cloud/live"'
        in page.live_queue_link.text()
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
        'href="https://linkcue.apps.bot-hosting.cloud/live"'
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
        'href="https://linkcue.apps.bot-hosting.cloud/live"'
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
        'href="https://linkcue.apps.bot-hosting.cloud:9000/live"'
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
        connection_mode="manual",
    )
    qtbot.addWidget(page)

    assert page.bot_url_input.text() == "de1.bot-hosting.cloud"
    assert page.public_web_url_input.text() == ""
