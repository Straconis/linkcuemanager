from app.credential_store import CredentialStore


BOT_HOSTING_API_KEY = "bot_hosting_api_key"


class BotHostingCredentialStore:
    def __init__(
        self,
        store: CredentialStore | None = None,
    ):
        self.store = store or CredentialStore()

    def save_api_key(
        self,
        api_key: str,
    ) -> None:
        value = api_key.strip()

        if not value:
            raise ValueError(
                "Bot-Hosting API key cannot be empty."
            )

        self.store.save(
            BOT_HOSTING_API_KEY,
            value,
        )

    def get_api_key(self) -> str | None:
        return self.store.get(
            BOT_HOSTING_API_KEY
        )

    def clear_api_key(self) -> None:
        self.store.delete(
            BOT_HOSTING_API_KEY
        )
