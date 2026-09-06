from app.credential_store import CredentialStore


CONTROL_NETWORK_PASSWORD_KEY = "control_network_password"


class ControlNetworkCredentialStore:
    def __init__(
        self,
        store: CredentialStore | None = None,
    ):
        self.store = store or CredentialStore()

    def save_password(
        self,
        password: str,
    ) -> None:
        value = password.strip()

        if not value:
            raise ValueError(
                "Control Network password cannot be empty."
            )

        self.store.save(
            CONTROL_NETWORK_PASSWORD_KEY,
            value,
        )

    def get_password(self) -> str | None:
        return self.store.get(
            CONTROL_NETWORK_PASSWORD_KEY
        )

    def clear_password(self) -> None:
        self.store.delete(
            CONTROL_NETWORK_PASSWORD_KEY
        )
