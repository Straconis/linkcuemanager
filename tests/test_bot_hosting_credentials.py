import pytest

from app.bot_hosting_credentials import (
    BOT_HOSTING_API_KEY,
    BotHostingCredentialStore,
)


class FakeCredentialStore:
    def __init__(self):
        self.values = {}

    def save(self, name, value):
        self.values[name] = value

    def get(self, name):
        return self.values.get(name)

    def delete(self, name):
        self.values.pop(name, None)


def test_save_api_key_uses_secure_credential_store():
    backend = FakeCredentialStore()
    store = BotHostingCredentialStore(backend)

    store.save_api_key("  secret-key  ")

    assert backend.values == {
        BOT_HOSTING_API_KEY: "secret-key"
    }


def test_get_api_key_reads_secure_credential_store():
    backend = FakeCredentialStore()
    backend.values[BOT_HOSTING_API_KEY] = "secret-key"

    store = BotHostingCredentialStore(backend)

    assert store.get_api_key() == "secret-key"


def test_clear_api_key_removes_secure_credential():
    backend = FakeCredentialStore()
    backend.values[BOT_HOSTING_API_KEY] = "secret-key"

    store = BotHostingCredentialStore(backend)

    store.clear_api_key()

    assert BOT_HOSTING_API_KEY not in backend.values


def test_blank_api_key_is_rejected():
    backend = FakeCredentialStore()
    store = BotHostingCredentialStore(backend)

    with pytest.raises(
        ValueError,
        match="cannot be empty",
    ):
        store.save_api_key("   ")

    assert backend.values == {}
