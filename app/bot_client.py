from urllib.parse import quote
import json

import httpx

from app.linkcue_identity import IdentityStore
from app.request_signer import create_signed_headers


class BotClientError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        detail: str | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail


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
        self.identity_store = IdentityStore()

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
        *,
        json_body: dict | None = None,
    ) -> dict | list:
        try:
            with self._client() as client:
                body = b""

                if json_body is not None:
                    body = json.dumps(
                        json_body,
                        separators=(",", ":"),
                    ).encode("utf-8")

                headers = {}

                if json_body is not None:
                    headers["Content-Type"] = "application/json"

                identity = self.identity_store.load_identity()

                if identity:
                    headers.update(
                        create_signed_headers(
                            identity,
                            method=method,
                            path=path,
                            body=body,
                        )
                    )

                response = client.request(
                    method,
                    path,
                    content=body if body else None,
                    headers=headers,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            detail = None

            try:
                body = exc.response.json()
                if isinstance(body, dict):
                    raw_detail = body.get("detail")

                    if isinstance(raw_detail, str):
                        detail = raw_detail

                    elif isinstance(raw_detail, list):
                        messages = []

                        for item in raw_detail:
                            if not isinstance(item, dict):
                                continue

                            message = item.get("msg")
                            if isinstance(message, str):
                                message = message.strip()
                                if message:
                                    messages.append(message)

                        if messages:
                            detail = "; ".join(messages)
            except (ValueError, TypeError):
                pass

            message = detail or str(exc)

            raise BotClientError(
                message,
                status_code=exc.response.status_code,
                detail=detail,
            ) from exc

        except httpx.HTTPError as exc:
            raise BotClientError(str(exc)) from exc

    def health(self) -> dict:
        return self._request("GET", "/health")

    def restart_bot(self) -> dict:
        result = self._request(
            "POST",
            "/maintenance/restart",
        )

        if not isinstance(result, dict):
            raise BotClientError(
                "Bot returned an invalid restart response"
            )

        return result

    def queue(self) -> list[dict]:
        result = self._request("GET", "/api/queue")

        if not isinstance(result, list):
            raise BotClientError(
                "Bot returned an invalid queue response"
            )

        return result

    def history(self) -> list[dict]:
        result = self._request("GET", "/api/history")

        if not isinstance(result, list):
            raise BotClientError(
                "Bot returned an invalid history response"
            )

        return result

    def add_queue_item(
        self,
        url: str,
        *,
        title: str | None = None,
        video_channel: str | None = None,
        twitch_channel: str | None = None,
        submitted_by: str | None = None,
    ) -> dict:
        return self._request(
            "POST",
            "/queue",
            json_body={
                "url": url,
                "title": title,
                "video_channel": video_channel,
                "twitch_channel": twitch_channel,
                "submitted_by": submitted_by,
                "submission_source": "manager",
            },
        )

    def move_queue_item(
        self,
        item_id: int,
        position: int,
    ) -> dict:
        return self._request(
            "POST",
            f"/queue/{item_id}/move",
            json_body={
                "position": position,
            },
        )

    def clear_queue(self) -> dict:
        return self._request(
            "DELETE",
            "/queue",
        )

    def remove_queue_item(
        self,
        item_id: int,
    ) -> dict:
        return self._request(
            "DELETE",
            f"/queue/{item_id}",
        )

    def refresh_queue_metadata(self) -> dict:
        result = self._request(
            "POST",
            "/queue/refresh-metadata",
        )

        if not isinstance(result, dict):
            raise BotClientError(
                "Bot returned an invalid metadata refresh response"
            )

        return result

    def bot_connection_setting(self) -> dict:
        result = self._request(
            "GET",
            "/settings/bot-connection",
        )

        if not isinstance(result, dict):
            raise BotClientError(
                "Bot returned an invalid connection setting"
            )

        return result

    def set_bot_connection(
        self,
        bot_url: str,
        bot_port: int,
    ) -> dict:
        result = self._request(
            "PUT",
            "/settings/bot-connection",
            json_body={
                "bot_url": bot_url,
                "bot_port": bot_port,
            },
        )

        if not isinstance(result, dict):
            raise BotClientError(
                "Bot returned an invalid connection setting"
            )

        return result

    def logging_setting(self) -> dict:
        result = self._request(
            "GET",
            "/settings/logging",
        )

        if not isinstance(result, dict):
            raise BotClientError(
                "Bot returned an invalid logging setting"
            )

        return result

    def set_logging_setting(
        self,
        enabled: bool,
        timezone_name: str,
    ) -> dict:
        result = self._request(
            "PUT",
            "/settings/logging",
            json_body={
                "enabled": enabled,
                "timezone": timezone_name,
            },
        )

        if not isinstance(result, dict):
            raise BotClientError(
                "Bot returned an invalid logging setting"
            )

        return result

    def public_web_setting(self) -> dict:
        result = self._request(
            "GET",
            "/settings/public-web",
        )

        if not isinstance(result, dict):
            raise BotClientError(
                "Bot returned an invalid public web setting"
            )

        return result

    def set_public_web_enabled(
        self,
        enabled: bool,
        port: int | None = None,
        public_url: str | None = None,
        connection_mode: str | None = None,
    ) -> dict:
        json_body = {
            "enabled": enabled,
        }

        if port is not None:
            json_body["port"] = port

        if public_url is not None:
            json_body["public_url"] = public_url

        if connection_mode is not None:
            json_body["connection_mode"] = connection_mode

        result = self._request(
            "PUT",
            "/settings/public-web",
            json_body=json_body,
        )

        if not isinstance(result, dict):
            raise BotClientError(
                "Bot returned an invalid public web setting"
            )

        return result

    def player_status(self) -> dict:
        return self._request("GET", "/player/status")

    def player_state(self) -> dict:
        return self._request("GET", "/player/state")

    def twitch_setting(self) -> dict:
        result = self._request(
            "GET",
            "/settings/twitch",
        )

        if not isinstance(result, dict):
            raise BotClientError(
                "Bot returned an invalid Twitch setting"
            )

        return result

    def set_twitch_setting(
        self,
        channel_url: str,
        channel: str,
        populate_channel_from_url: bool,
    ) -> dict:
        result = self._request(
            "PUT",
            "/settings/twitch",
            json_body={
                "channel_url": channel_url,
                "channel": channel,
                "populate_channel_from_url": (
                    populate_channel_from_url
                ),
            },
        )

        if not isinstance(result, dict):
            raise BotClientError(
                "Bot returned an invalid Twitch setting"
            )

        return result

    def create_manager_pairing(
        self,
        control_password: str,
    ) -> dict:
        result = self._request(
            "POST",
            "/auth/create-pairing",
            json_body={
                "role": "manager",
                "control_password": control_password,
            },
        )

        if not isinstance(result, dict):
            raise BotClientError(
                "Bot returned an invalid pairing response"
            )

        return result

    def pair_manager(
        self,
        code: str,
        control_password: str,
    ) -> dict:
        result = self._request(
            "POST",
            "/auth/pair",
            json_body={
                "code": code,
                "role": "manager",
                "control_password": control_password,
            },
        )

        if not isinstance(result, dict):
            raise BotClientError(
                "Bot returned an invalid client identity response"
            )

        return result

    def host_control_provisioning(self) -> dict:
        result = self._request(
            "GET",
            "/provisioning/host-control",
        )

        if not isinstance(result, dict):
            raise BotClientError(
                "Bot returned an invalid host control provisioning response"
            )

        return result

    def twitch_auth_status(self) -> dict:
        return self._request(
            "GET",
            "/twitch/auth/status",
        )

    def authorize_twitch(self) -> dict:
        return self._request(
            "POST",
            "/twitch/auth/authorize",
        )

    def twitch_status(self) -> dict:
        return self._request("GET", "/twitch/status")

    def connect_twitch(self) -> dict:
        return self._request(
            "POST",
            "/twitch/connect",
        )

    def disconnect_twitch(self) -> dict:
        return self._request(
            "POST",
            "/twitch/disconnect",
        )

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
