import time
from typing import Callable

import httpx


BOT_HOSTING_API_BASE_URL = "https://bot-hosting.net/api/v1"


class BotHostingClientError(RuntimeError):
    pass


class BotHostingClient:
    def __init__(
        self,
        api_key: str,
        deployment_id: str,
        *,
        timeout: float = 15.0,
        transport: httpx.BaseTransport | None = None,
    ):
        self.api_key = api_key.strip()
        self.deployment_id = deployment_id.strip()
        self.timeout = timeout
        self.transport = transport

    def _client(self) -> httpx.Client:
        return httpx.Client(
            base_url=BOT_HOSTING_API_BASE_URL,
            timeout=self.timeout,
            transport=self.transport,
            headers={
                "Authorization": f"Bearer {self.api_key}",
            },
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
    ) -> dict:
        try:
            with self._client() as client:
                response = client.request(
                    method,
                    path,
                    json=json,
                )

            response.raise_for_status()

            result = response.json()

            if not isinstance(result, dict):
                raise BotHostingClientError(
                    "Bot-Hosting returned an invalid response"
                )

            return result

        except httpx.HTTPStatusError as exc:
            detail = None

            try:
                payload = exc.response.json()

                if isinstance(payload, dict):
                    detail = (
                        payload.get("detail")
                        or payload.get("message")
                        or payload.get("error")
                    )
            except ValueError:
                detail = None

            message = (
                str(detail)
                if detail
                else (
                    f"Bot-Hosting returned HTTP "
                    f"{exc.response.status_code}"
                )
            )

            raise BotHostingClientError(message) from exc

        except httpx.HTTPError as exc:
            raise BotHostingClientError(str(exc)) from exc

    def deployment(self) -> dict:
        return self._request(
            "GET",
            f"/deployments/{self.deployment_id}",
        )

    def power(self, action: str) -> dict:
        normalized_action = action.strip().lower()

        if normalized_action not in {
            "start",
            "stop",
            "restart",
        }:
            raise ValueError(
                f"Unsupported Bot-Hosting power action: {action}"
            )

        return self._request(
            "POST",
            f"/deployments/{self.deployment_id}/power",
            json={
                "action": normalized_action,
            },
        )

    def start(self) -> dict:
        return self.power("start")

    def stop(self) -> dict:
        return self.power("stop")

    def restart(self) -> dict:
        return self.power("restart")

    def wait_for_state(
        self,
        expected_state: str,
        *,
        timeout: float = 30.0,
        poll_interval: float = 1.0,
        sleep: Callable[[float], None] = time.sleep,
    ) -> dict:
        deadline = time.monotonic() + timeout
        normalized_expected = expected_state.strip().lower()

        while True:
            deployment = self.deployment()
            state = str(
                deployment.get("state", "")
            ).strip().lower()

            if state == normalized_expected:
                return deployment

            if time.monotonic() >= deadline:
                raise BotHostingClientError(
                    "Timed out waiting for Bot-Hosting deployment "
                    f"to reach state '{normalized_expected}'. "
                    f"Last state was '{state or 'unknown'}'."
                )

            sleep(poll_interval)
