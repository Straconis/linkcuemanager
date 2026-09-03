import platform

import keyring


SERVICE_NAME = "LinkCue"


class CredentialStore:
    """
    Cross-platform secure credential storage.

    Windows:
        Credential Manager

    Linux:
        Secret Service/KWallet backend
        when available

    """

    def __init__(self):
        self.backend = self._detect_backend()

    def _detect_backend(self) -> str:
        system = platform.system()

        if system == "Windows":
            return "windows"

        if system == "Linux":
            return "linux"

        return "unsupported"

    def backend_name(self) -> str:
        return self.backend

    def save(
        self,
        name: str,
        value: str,
    ) -> None:
        keyring.set_password(
            SERVICE_NAME,
            name,
            value,
        )

    def get(
        self,
        name: str,
    ) -> str | None:
        return keyring.get_password(
            SERVICE_NAME,
            name,
        )

    def delete(
        self,
        name: str,
    ) -> None:
        keyring.delete_password(
            SERVICE_NAME,
            name,
        )
