from urllib.parse import quote

import httpx


class BotClientError(RuntimeError):
    pass


class BotClient:
    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 5.0,
        transport: httpx.BaseTransport | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.transport = transport

    def _client(self) -> httpx.Client:
        return httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            transport=self.transport,
        )

    def _request(
        self,
        method: str,
        path: str,
    ) -> dict | list:
        try:
            with self._client() as client:
                response = client.request(method, path)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as exc:
            raise BotClientError(str(exc)) from exc

    def health(self) -> dict:
        return self._request("GET", "/health")

    def queue(self) -> list[dict]:
        result = self._request("GET", "/queue")

        if not isinstance(result, list):
            raise BotClientError("Bot returned an invalid queue response")

        return result

    def twitch_status(self) -> dict:
        return self._request("GET", "/twitch/status")

    def join_twitch_channel(self, channel: str) -> dict:
        encoded = quote(channel, safe="")
        return self._request(
            "POST",
            f"/twitch/channels/{encoded}/join",
        )

    def leave_twitch_channel(self, channel: str) -> dict:
        encoded = quote(channel, safe="")
        return self._request(
            "POST",
            f"/twitch/channels/{encoded}/leave",
        )
