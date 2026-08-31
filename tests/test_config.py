from app.config import APP_NAME, APP_VERSION, DEFAULT_BOT_URL


def test_application_identity():
    assert APP_NAME == "LinkCue Manager"
    assert APP_VERSION == "0.1.0"


def test_default_bot_url():
    assert DEFAULT_BOT_URL == "http://127.0.0.1:8000"
