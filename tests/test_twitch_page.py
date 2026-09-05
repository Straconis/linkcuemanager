from app.pages.twitch_page import TwitchPage


def _build_page(
    qtbot,
    join_callback=lambda: None,
    leave_callback=lambda: None,
    refresh_callback=lambda: None,
):
    page = TwitchPage(
        join_callback,
        leave_callback,
        refresh_callback,
    )
    qtbot.addWidget(page)
    return page


def test_runtime_controls_are_available(qtbot):
    page = _build_page(qtbot)

    assert hasattr(page, "channel_input")
    assert hasattr(page, "join_button")
    assert hasattr(page, "leave_button")
    assert hasattr(page, "refresh_button")
    assert hasattr(page, "status_label")
    assert hasattr(page, "channel_list")


def test_runtime_channel_input_round_trip(qtbot):
    page = _build_page(qtbot)

    page.set_channel("SmokeEEG")

    assert page.entered_channel() == "SmokeEEG"


def test_clear_channel_input(qtbot):
    page = _build_page(qtbot)

    page.set_channel("smokeeeg")
    page.clear_channel_input()

    assert page.entered_channel() == ""


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
        join_callback=lambda: calls.append("join"),
        leave_callback=lambda: calls.append("leave"),
        refresh_callback=lambda: calls.append("refresh"),
    )

    page.join_button.click()
    page.leave_button.click()
    page.refresh_button.click()

    assert calls == [
        "join",
        "leave",
        "refresh",
    ]
