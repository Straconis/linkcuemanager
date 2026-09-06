import httpx
import pytest

from app.bot_hosting_restart import (
    BotHostingRestartError,
    BotHostingRestartService,
)


class FakeBotHostingClient:
    def __init__(self):
        self.calls = []

    def stop(self):
        self.calls.append(("stop",))
        return {"ok": True}

    def start(self):
        self.calls.append(("start",))
        return {"ok": True}

    def restart(self):
        self.calls.append(("restart",))
        return {"ok": True}

    def wait_for_state(
        self,
        state,
        *,
        timeout,
        poll_interval,
        sleep,
    ):
        self.calls.append(
            (
                "wait_for_state",
                state,
                timeout,
                poll_interval,
            )
        )
        return {
            "state": state,
        }


def healthy_transport():
    def handler(request):
        assert (
            str(request.url)
            == "https://linkcue.example/health"
        )

        return httpx.Response(
            200,
            json={
                "status": "ok",
                "service": "LinkCue Bot",
            },
        )

    return httpx.MockTransport(handler)


def test_simulated_restart_stops_then_starts_and_checks_health():
    client = FakeBotHostingClient()
    sleeps = []

    service = BotHostingRestartService(
        client,
        "https://linkcue.example",
        state_timeout=12.0,
        health_timeout=5.0,
        poll_interval=0.25,
        restart_delay=1.5,
        sleep=sleeps.append,
        health_transport=healthy_transport(),
    )

    result = service.restart("simulated")

    assert client.calls == [
        ("stop",),
        (
            "wait_for_state",
            "offline",
            12.0,
            0.25,
        ),
        ("start",),
        (
            "wait_for_state",
            "running",
            12.0,
            0.25,
        ),
    ]
    assert sleeps == [1.5]
    assert result["mode"] == "simulated"
    assert result["deployment"]["state"] == "running"
    assert result["health"]["status"] == "ok"


def test_direct_restart_uses_native_restart_and_checks_health():
    client = FakeBotHostingClient()

    service = BotHostingRestartService(
        client,
        "https://linkcue.example/",
        sleep=lambda seconds: None,
        health_transport=healthy_transport(),
    )

    result = service.restart("direct")

    assert client.calls == [
        ("restart",),
        (
            "wait_for_state",
            "running",
            30.0,
            1.0,
        ),
    ]
    assert result["mode"] == "direct"
    assert result["health"]["status"] == "ok"


def test_invalid_restart_mode_is_rejected():
    service = BotHostingRestartService(
        FakeBotHostingClient(),
        "https://linkcue.example",
    )

    with pytest.raises(
        ValueError,
        match="Unsupported restart mode",
    ):
        service.restart("banana")


def test_health_wait_retries_until_bot_is_healthy():
    calls = {"count": 0}
    sleeps = []

    def handler(request):
        calls["count"] += 1

        if calls["count"] == 1:
            return httpx.Response(
                503,
                json={"status": "starting"},
            )

        return httpx.Response(
            200,
            json={"status": "ok"},
        )

    service = BotHostingRestartService(
        FakeBotHostingClient(),
        "https://linkcue.example",
        poll_interval=0.1,
        sleep=sleeps.append,
        health_transport=httpx.MockTransport(
            handler
        ),
    )

    result = service.wait_for_health()

    assert result == {"status": "ok"}
    assert calls["count"] == 2
    assert sleeps == [0.1]


def test_health_wait_times_out_cleanly(monkeypatch):
    times = iter(
        [
            0.0,
            0.0,
            2.0,
        ]
    )

    monkeypatch.setattr(
        "app.bot_hosting_restart.time.monotonic",
        lambda: next(times),
    )

    def handler(request):
        return httpx.Response(
            503,
            json={"status": "starting"},
        )

    service = BotHostingRestartService(
        FakeBotHostingClient(),
        "https://linkcue.example",
        health_timeout=1.0,
        poll_interval=0.1,
        sleep=lambda seconds: None,
        health_transport=httpx.MockTransport(
            handler
        ),
    )

    with pytest.raises(
        BotHostingRestartError,
        match="Timed out waiting",
    ):
        service.wait_for_health()
