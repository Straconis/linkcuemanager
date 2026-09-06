import time
from collections.abc import Callable

import httpx

from app.bot_hosting_client import (
    BotHostingClient,
    BotHostingClientError,
)


class BotHostingRestartError(RuntimeError):
    pass


class BotHostingRestartService:
    def __init__(
        self,
        client: BotHostingClient,
        health_url: str,
        *,
        state_timeout: float = 30.0,
        health_timeout: float = 30.0,
        poll_interval: float = 1.0,
        restart_delay: float = 1.0,
        sleep: Callable[[float], None] = time.sleep,
        health_transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.client = client
        self.health_url = (
            health_url.rstrip("/") + "/health"
        )
        self.state_timeout = state_timeout
        self.health_timeout = health_timeout
        self.poll_interval = poll_interval
        self.restart_delay = restart_delay
        self.sleep = sleep
        self.health_transport = health_transport

    def restart(
        self,
        mode: str,
    ) -> dict:
        normalized_mode = mode.strip().lower()

        if normalized_mode == "simulated":
            return self._simulated_restart()

        if normalized_mode == "direct":
            return self._direct_restart()

        raise ValueError(
            f"Unsupported restart mode: {mode}"
        )

    def _simulated_restart(self) -> dict:
        try:
            self.client.stop()

            self.client.wait_for_state(
                "offline",
                timeout=self.state_timeout,
                poll_interval=self.poll_interval,
                sleep=self.sleep,
            )

            self.sleep(self.restart_delay)

            self.client.start()

            deployment = self.client.wait_for_state(
                "running",
                timeout=self.state_timeout,
                poll_interval=self.poll_interval,
                sleep=self.sleep,
            )

            health = self.wait_for_health()

        except BotHostingClientError as exc:
            raise BotHostingRestartError(
                str(exc)
            ) from exc

        return {
            "mode": "simulated",
            "deployment": deployment,
            "health": health,
        }

    def _direct_restart(self) -> dict:
        try:
            self.client.restart()

            deployment = self.client.wait_for_state(
                "running",
                timeout=self.state_timeout,
                poll_interval=self.poll_interval,
                sleep=self.sleep,
            )

            health = self.wait_for_health()

        except BotHostingClientError as exc:
            raise BotHostingRestartError(
                str(exc)
            ) from exc

        return {
            "mode": "direct",
            "deployment": deployment,
            "health": health,
        }

    def wait_for_health(self) -> dict:
        deadline = time.monotonic() + self.health_timeout
        last_error = "Bot health endpoint unavailable."

        while True:
            try:
                with httpx.Client(
                    timeout=5.0,
                    transport=self.health_transport,
                ) as client:
                    response = client.get(
                        self.health_url
                    )

                response.raise_for_status()
                result = response.json()

                if (
                    isinstance(result, dict)
                    and result.get("status") == "ok"
                ):
                    return result

                last_error = (
                    "Bot health endpoint returned "
                    "an unexpected response."
                )

            except (
                httpx.HTTPError,
                ValueError,
            ) as exc:
                last_error = str(exc)

            if time.monotonic() >= deadline:
                raise BotHostingRestartError(
                    "Timed out waiting for LinkCue Bot "
                    f"health check: {last_error}"
                )

            self.sleep(self.poll_interval)
