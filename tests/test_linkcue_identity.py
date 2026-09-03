from app.linkcue_identity import (
    IdentityStore,
    LinkCueIdentity,
)
from app.request_signer import create_signed_headers


def test_identity_round_trip(monkeypatch):
    import app.linkcue_identity as module

    storage = {}

    monkeypatch.setattr(
        module.CredentialStore,
        "save",
        lambda self, key, value:
            storage.update({key: value}),
    )

    monkeypatch.setattr(
        module.CredentialStore,
        "get",
        lambda self, key:
            storage.get(key),
    )

    identity_store = IdentityStore()

    identity_store.save_identity(
        LinkCueIdentity(
            client_id="manager-test",
            role="manager",
            secret="00" * 32,
        )
    )

    identity = identity_store.load_identity()

    assert identity.client_id == "manager-test"
    assert identity.role == "manager"


def test_signed_headers_create():
    identity = LinkCueIdentity(
        client_id="manager-test",
        role="manager",
        secret="00" * 32,
    )

    headers = create_signed_headers(
        identity,
        method="POST",
        path="/test",
    )

    assert "X-LinkCue-Client" in headers
    assert "X-LinkCue-Signature" in headers
