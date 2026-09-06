import pytest

from app.control_network_credentials import (
    CONTROL_NETWORK_PASSWORD_KEY,
    ControlNetworkCredentialStore,
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


def test_save_password_uses_secure_credential_store():
    backend = FakeCredentialStore()
    store = ControlNetworkCredentialStore(backend)

    store.save_password("  shared-password  ")

    assert backend.values == {
        CONTROL_NETWORK_PASSWORD_KEY: "shared-password"
    }


def test_get_password_reads_secure_credential_store():
    backend = FakeCredentialStore()
    backend.values[
        CONTROL_NETWORK_PASSWORD_KEY
    ] = "shared-password"

    store = ControlNetworkCredentialStore(backend)

    assert store.get_password() == "shared-password"


def test_clear_password_removes_secure_credential():
    backend = FakeCredentialStore()
    backend.values[
        CONTROL_NETWORK_PASSWORD_KEY
    ] = "shared-password"

    store = ControlNetworkCredentialStore(backend)

    store.clear_password()

    assert CONTROL_NETWORK_PASSWORD_KEY not in backend.values


def test_blank_password_is_rejected():
    backend = FakeCredentialStore()
    store = ControlNetworkCredentialStore(backend)

    with pytest.raises(
        ValueError,
        match="cannot be empty",
    ):
        store.save_password("   ")

    assert backend.values == {}
