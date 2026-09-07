from app.pages.twitch_page import TwitchPage


def _build_page(
    qtbot,
    authorize_callback=lambda: None,
    connect_callback=lambda: None,
    disconnect_callback=lambda: None,
    join_callback=lambda: None,
    leave_callback=lambda: None,
    refresh_callback=lambda: None,
):
    page = TwitchPage(
        authorize_callback,
        connect_callback,
        disconnect_callback,
        join_callback,
        leave_callback,
        refresh_callback,
    )
    qtbot.addWidget(page)
    return page


def test_runtime_controls_are_available(qtbot):
    page = _build_page(qtbot)

    assert hasattr(page, "authorization_label")
    assert hasattr(page, "connection_label")
    assert hasattr(page, "authorize_button")
    assert hasattr(page, "connect_button")
    assert hasattr(page, "disconnect_button")
    assert hasattr(page, "configured_channel_label")
    assert hasattr(page, "join_button")
    assert hasattr(page, "leave_button")
    assert hasattr(page, "refresh_button")
    assert hasattr(page, "status_label")
    assert hasattr(page, "channel_list")


def test_configured_channel_display(qtbot):
    page = _build_page(qtbot)

    page.set_configured_channel("smokeeeg")

    assert page.configured_channel_label.text() == (
        "Configured Channel: smokeeeg"
    )


def test_configured_channel_display_handles_missing_channel(qtbot):
    page = _build_page(qtbot)

    page.set_configured_channel(None)

    assert page.configured_channel_label.text() == (
        "Configured Channel: Not configured"
    )


def test_selected_channel_returns_current_selection(qtbot):
    page = _build_page(qtbot)

    page.apply_status(
        {
            "channels": [
                "smokeeeg",
                "otherchannel",
            ]
        }
    )

    page.channel_list.setCurrentRow(1)

    assert page.selected_channel() == "otherchannel"


def test_selected_channel_returns_empty_when_none_selected(qtbot):
    page = _build_page(qtbot)

    assert page.selected_channel() == ""


def test_status_is_active_when_channels_exist(qtbot):
    page = _build_page(qtbot)

    page.apply_status(
        {
            "channels": [
                "smokeeeg",
                "otherchannel",
            ]
        }
    )

    assert page.status_label.text() == (
        "Active - 2 channel(s)"
    )


def test_status_is_inactive_when_no_channels_exist(qtbot):
    page = _build_page(qtbot)

    page.apply_status(
        {
            "channels": [],
        }
    )

    assert page.status_label.text() == "Inactive"


def test_connected_flag_can_control_runtime_status(qtbot):
    page = _build_page(qtbot)

    page.apply_status(
        {
            "connected": True,
            "channels": [],
        },
        use_connected_flag=True,
    )

    assert page.status_label.text() == (
        "Active - 0 channel(s)"
    )


def test_runtime_buttons_call_callbacks(qtbot):
    calls = []

    page = _build_page(
        qtbot,
        authorize_callback=lambda: calls.append("authorize"),
        connect_callback=lambda: calls.append("connect"),
        disconnect_callback=lambda: calls.append("disconnect"),
        join_callback=lambda: calls.append("join"),
        leave_callback=lambda: calls.append("leave"),
        refresh_callback=lambda: calls.append("refresh"),
    )

    page.authorize_button.click()
    page.connect_button.click()
    page.disconnect_button.click()
    page.join_button.click()
    page.leave_button.click()
    page.refresh_button.click()

    assert calls == [
        "authorize",
        "connect",
        "disconnect",
        "join",
        "leave",
        "refresh",
    ]


def test_authorization_status_shows_authorized_login(qtbot):
    page = _build_page(qtbot)

    page.apply_auth_status(
        {
            "authorized": True,
            "login": "linkcuebot",
        }
    )

    assert page.authorization_label.text() == (
        "Authorization: Authorized as linkcuebot"
    )


def test_authorization_status_shows_not_authorized(qtbot):
    page = _build_page(qtbot)

    page.apply_auth_status(
        {
            "authorized": False,
            "login": None,
        }
    )

    assert page.authorization_label.text() == (
        "Authorization: Not Authorized"
    )


def test_runtime_status_updates_connection_and_authorization(qtbot):
    page = _build_page(qtbot)

    page.apply_status(
        {
            "authorized": True,
            "login": "linkcuebot",
            "connected": True,
            "channels": ["smokeeeg"],
        },
        use_connected_flag=True,
    )

    assert page.authorization_label.text() == (
        "Authorization: Authorized as linkcuebot"
    )
    assert page.connection_label.text() == (
        "Connection: Connected"
    )
    assert page.status_label.text() == (
        "Active - 1 channel(s)"
    )


def test_runtime_status_shows_disconnected(qtbot):
    page = _build_page(qtbot)

    page.apply_status(
        {
            "authorized": True,
            "login": "linkcuebot",
            "connected": False,
            "channels": [],
        },
        use_connected_flag=True,
    )

    assert page.connection_label.text() == (
        "Connection: Disconnected"
    )
    assert page.status_label.text() == "Inactive"

def test_unavailable_status_clears_stale_runtime_state(qtbot):
    page = _build_page(qtbot)

    page.apply_status(
        {
            "authorized": True,
            "login": "linkcuebot",
            "connected": True,
            "channels": ["smokeeeg"],
        },
        use_connected_flag=True,
    )

    page.show_unavailable()

    assert page.authorization_label.text() == "Authorization: Unknown"
    assert page.connection_label.text() == "Connection: Unknown"
    assert page.status_label.text() == "Unavailable"
    assert page.channel_list.count() == 0

