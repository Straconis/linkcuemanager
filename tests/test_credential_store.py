from app.credential_store import CredentialStore


def test_detects_backend():
    store = CredentialStore()

    assert store.backend_name() in {
        "windows",
        "linux",
        "unsupported",
    }


def test_save_and_get(monkeypatch):
    import app.credential_store as module

    storage = {}

    monkeypatch.setattr(
        module.keyring,
        "set_password",
        lambda service, name, value:
            storage.update({name: value}),
    )

    monkeypatch.setattr(
        module.keyring,
        "get_password",
        lambda service, name:
            storage.get(name),
    )

    store = CredentialStore()

    store.save(
        "test-secret",
        "abc123",
    )

    assert store.get(
        "test-secret"
    ) == "abc123"


def test_delete(monkeypatch):
    import app.credential_store as module

    storage = {
        "test-secret": "abc123"
    }

    monkeypatch.setattr(
        module.keyring,
        "delete_password",
        lambda service, name:
            storage.pop(name, None),
    )

    monkeypatch.setattr(
        module.keyring,
        "get_password",
        lambda service, name:
            storage.get(name),
    )

    store = CredentialStore()

    store.delete(
        "test-secret"
    )

    assert store.get(
        "test-secret"
    ) is None
