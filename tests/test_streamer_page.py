from app.pages.streamer_page import StreamerPage


def _build_page(
    qtbot,
    authorize_callback=lambda: None,
    generate_callback=lambda: None,
    copy_callback=lambda: None,
):
    page = StreamerPage(
        lambda: None,
        authorize_callback,
        generate_callback,
        copy_callback,
    )
    qtbot.addWidget(page)
    return page


def test_streamer_twitch_settings_controls_are_available(qtbot):
    page = _build_page(qtbot)

    assert hasattr(page, "streamer_name_input")
    assert hasattr(page, "channel_url_input")
    assert hasattr(page, "configured_channel_input")
    assert hasattr(
        page,
        "populate_streamer_name_from_url_toggle",
    )
    assert hasattr(page, "populate_channel_from_url_toggle")
    assert hasattr(page, "save_settings_button")


def test_authorize_linkcue_bot_account_button(qtbot):
    authorizations = []

    page = _build_page(
        qtbot,
        authorize_callback=(
            lambda: authorizations.append(True)
        ),
    )

    assert (
        page.authorize_twitch_button.text()
        == "Authorize LinkCue Bot Account"
    )

    page.authorize_twitch_button.click()

    assert authorizations == [True]


def test_streamer_twitch_auto_population_defaults_on(qtbot):
    page = _build_page(qtbot)

    assert (
        page.populate_streamer_name_from_url_enabled()
        is True
    )
    assert page.populate_channel_from_url_enabled() is True
    assert page.streamer_name_input.isReadOnly() is True
    assert page.configured_channel_input.isReadOnly() is True


def test_streamer_twitch_url_populates_name_and_channel_when_enabled(
    qtbot,
):
    page = _build_page(qtbot)

    page.channel_url_input.setText(
        "https://twitch.tv/SmokeEEG"
    )

    assert page.streamer_name() == "smokeeeg"
    assert page.configured_channel() == "smokeeeg"


def test_streamer_twitch_url_without_scheme_populates_channel(
    qtbot,
):
    page = _build_page(qtbot)

    page.channel_url_input.setText(
        "twitch.tv/SmokeEEG/"
    )

    assert page.configured_channel() == "smokeeeg"


def test_disabling_name_auto_population_makes_name_editable(
    qtbot,
):
    page = _build_page(qtbot)

    page.populate_streamer_name_from_url_toggle.setChecked(False)

    assert (
        page.populate_streamer_name_from_url_enabled()
        is False
    )
    assert page.streamer_name_input.isReadOnly() is False

    page.streamer_name_input.setText("Boomer")

    assert page.streamer_name() == "Boomer"


def test_manual_name_is_not_overwritten_when_name_auto_population_off(
    qtbot,
):
    page = _build_page(qtbot)

    page.populate_streamer_name_from_url_toggle.setChecked(False)
    page.streamer_name_input.setText("Boomer")

    page.channel_url_input.setText(
        "https://twitch.tv/smokeeeg"
    )

    assert page.streamer_name() == "Boomer"
    assert page.configured_channel() == "smokeeeg"


def test_disabling_auto_population_makes_channel_editable(
    qtbot,
):
    page = _build_page(qtbot)

    page.populate_channel_from_url_toggle.setChecked(False)

    assert page.populate_channel_from_url_enabled() is False
    assert page.configured_channel_input.isReadOnly() is False

    page.configured_channel_input.setText(
        "specialchannel"
    )

    assert page.configured_channel() == "specialchannel"


def test_manual_channel_is_not_overwritten_when_auto_population_off(
    qtbot,
):
    page = _build_page(qtbot)

    page.populate_channel_from_url_toggle.setChecked(False)
    page.configured_channel_input.setText(
        "specialchannel"
    )

    page.channel_url_input.setText(
        "https://twitch.tv/smokeeeg"
    )

    assert page.configured_channel() == "specialchannel"


def test_loading_auto_settings_derives_name_and_channel_from_url(
    qtbot,
):
    page = _build_page(qtbot)

    page.load_settings(
        "Boomer",
        "https://twitch.tv/SmokeEEG",
        "differentchannel",
        True,
        True,
    )

    assert page.streamer_name() == "smokeeeg"
    assert (
        page.channel_url()
        == "https://twitch.tv/SmokeEEG"
    )
    assert page.configured_channel() == "smokeeeg"
    assert page.streamer_name_input.isReadOnly() is True
    assert page.configured_channel_input.isReadOnly() is True


def test_loading_manual_settings_preserves_name_and_channel(
    qtbot,
):
    page = _build_page(qtbot)

    page.load_settings(
        "Boomer",
        "https://twitch.tv/smokeeeg",
        "specialchannel",
        False,
        False,
    )

    assert page.streamer_name() == "Boomer"
    assert page.configured_channel() == "specialchannel"
    assert page.streamer_name_input.isReadOnly() is False
    assert page.configured_channel_input.isReadOnly() is False


def test_loading_independent_auto_modes(qtbot):
    page = _build_page(qtbot)

    page.load_settings(
        "Boomer",
        "https://twitch.tv/smokeeeg",
        "specialchannel",
        True,
        False,
    )

    assert page.streamer_name() == "smokeeeg"
    assert page.configured_channel() == "specialchannel"
    assert page.streamer_name_input.isReadOnly() is True
    assert page.configured_channel_input.isReadOnly() is False

    page.load_settings(
        "Boomer",
        "https://twitch.tv/smokeeeg",
        "specialchannel",
        False,
        True,
    )

    assert page.streamer_name() == "Boomer"
    assert page.configured_channel() == "smokeeeg"
    assert page.streamer_name_input.isReadOnly() is False
    assert page.configured_channel_input.isReadOnly() is True


def test_loading_auto_name_without_url_preserves_saved_name(
    qtbot,
):
    page = _build_page(qtbot)

    page.load_settings(
        "Boomer",
        None,
        None,
        True,
        True,
    )

    assert page.streamer_name() == "Boomer"
    assert (
        page.populate_streamer_name_from_url_enabled()
        is True
    )
    assert page.streamer_name_input.isReadOnly() is True

def test_streamer_authorization_link_controls(qtbot):
    generated = []
    copied = []

    page = _build_page(
        qtbot,
        generate_callback=lambda: generated.append(True),
        copy_callback=lambda: copied.append(True),
    )

    assert (
        page.generate_streamer_auth_link_button.text()
        == "Generate Streamer Authorization Link"
    )
    assert page.copy_streamer_auth_link_button.text() == "Copy Link"
    assert page.streamer_auth_link_input.isReadOnly() is True
    assert page.copy_streamer_auth_link_button.isEnabled() is False

    page.generate_streamer_auth_link_button.click()

    assert generated == [True]

    page.set_streamer_authorization_link(
        "https://example.test/authorize"
    )

    assert page.streamer_authorization_link() == (
        "https://example.test/authorize"
    )
    assert page.copy_streamer_auth_link_button.isEnabled() is True

    page.copy_streamer_auth_link_button.click()

    assert copied == [True]


def test_streamer_authorization_status(qtbot):
    page = _build_page(qtbot)

    page.set_streamer_authorization_status(
        authorized=False,
        login=None,
    )

    assert (
        page.streamer_auth_status_label.text()
        == "Streamer channel: Not authorized"
    )

    page.set_streamer_authorization_status(
        authorized=True,
        login="smokeeeg",
    )

    assert (
        page.streamer_auth_status_label.text()
        == "Streamer channel: Authorized as smokeeeg"
    )
