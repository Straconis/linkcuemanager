import httpx
import pytest

from app.bot_hosting_client import (
    BotHostingClient,
    BotHostingClientError,
)


DEPLOYMENT_ID = "deployment-123"
API_KEY = "test-api-key"


def test_deployment_reads_expected_endpoint():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == (
            f"/api/v1/deployments/{DEPLOYMENT_ID}"
        )
        assert request.headers["Authorization"] == (
            f"Bearer {API_KEY}"
        )

        return httpx.Response(
            200,
            json={
                "id": DEPLOYMENT_ID,
                "state": "running",
            },
        )

    client = BotHostingClient(
        API_KEY,
        DEPLOYMENT_ID,
        transport=httpx.MockTransport(handler),
    )

    result = client.deployment()

    assert result["state"] == "running"


@pytest.mark.parametrize(
    ("method_name", "expected_action"),
    [
        ("start", "start"),
        ("stop", "stop"),
        ("restart", "restart"),
    ],
)
def test_power_methods_send_expected_action(
    method_name,
    expected_action,
):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == (
            f"/api/v1/deployments/{DEPLOYMENT_ID}/power"
        )
        assert request.headers["Authorization"] == (
            f"Bearer {API_KEY}"
        )

        payload = request.read().decode("utf-8")

        assert f'"action":"{expected_action}"' in payload

        return httpx.Response(
            200,
            json={
                "ok": True,
                "action": expected_action,
            },
        )

    client = BotHostingClient(
        API_KEY,
        DEPLOYMENT_ID,
        transport=httpx.MockTransport(handler),
    )

    result = getattr(
        client,
        method_name,
    )()

    assert result == {
        "ok": True,
        "action": expected_action,
    }


def test_invalid_power_action_is_rejected():
    client = BotHostingClient(
        API_KEY,
        DEPLOYMENT_ID,
    )

    with pytest.raises(
        ValueError,
        match="Unsupported Bot-Hosting power action",
    ):
        client.power("explode")


def test_http_error_becomes_bot_hosting_client_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            504,
            json={
                "error": "Gateway Timeout",
            },
        )

    client = BotHostingClient(
        API_KEY,
        DEPLOYMENT_ID,
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(
        BotHostingClientError,
        match="Gateway Timeout",
    ):
        client.restart()


def test_wait_for_state_returns_when_expected_state_is_seen():
    states = iter(
        [
            "stopping",
            "offline",
        ]
    )

    client = BotHostingClient(
        API_KEY,
        DEPLOYMENT_ID,
    )

    client.deployment = lambda: {
        "state": next(states)
    }

    result = client.wait_for_state(
        "offline",
        timeout=5.0,
        poll_interval=0.0,
        sleep=lambda _: None,
    )

    assert result["state"] == "offline"


def test_wait_for_state_times_out():
    client = BotHostingClient(
        API_KEY,
        DEPLOYMENT_ID,
    )

    client.deployment = lambda: {
        "state": "stopping"
    }

    with pytest.raises(
        BotHostingClientError,
        match="Timed out waiting",
    ):
        client.wait_for_state(
            "offline",
            timeout=0.0,
            poll_interval=0.0,
            sleep=lambda _: None,
        )
