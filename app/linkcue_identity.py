from dataclasses import dataclass

from app.credential_store import CredentialStore


CLIENT_ID_KEY = "client_id"
ROLE_KEY = "role"
SECRET_KEY = "secret"


@dataclass(frozen=True)
class LinkCueIdentity:
    client_id: str
    role: str
    secret: str


class IdentityStore:
    def __init__(self):
        self.store = CredentialStore()

    def save_identity(
        self,
        identity: LinkCueIdentity,
    ) -> None:
        self.store.save(
            CLIENT_ID_KEY,
            identity.client_id,
        )

        self.store.save(
            ROLE_KEY,
            identity.role,
        )

        self.store.save(
            SECRET_KEY,
            identity.secret,
        )

    def load_identity(
        self,
    ) -> LinkCueIdentity | None:
        client_id = self.store.get(
            CLIENT_ID_KEY
        )

        role = self.store.get(
            ROLE_KEY
        )

        secret = self.store.get(
            SECRET_KEY
        )

        if not all(
            [
                client_id,
                role,
                secret,
            ]
        ):
            return None

        return LinkCueIdentity(
            client_id=client_id,
            role=role,
            secret=secret,
        )

    def clear_identity(self) -> None:
        self.store.delete(
            CLIENT_ID_KEY
        )

        self.store.delete(
            ROLE_KEY
        )

        self.store.delete(
            SECRET_KEY
        )
