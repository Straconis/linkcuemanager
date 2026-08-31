import httpx
import pytest

from app.bot_client import BotClient, BotClientError


def make_client(handler):
    transport = httpx.MockTransport(handler)

    return BotClient(
        "http://test-bot",
        transport=transport,
    )


def test_health():
    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/health"

        return httpx.Response(
            200,
            json={
                "status": "ok",
                "app": "LinkCue Bot",
                "version": "0.1.0",
            },
        )

    client = make_client(handler)

    assert client.health() == {
        "status": "ok",
        "app": "LinkCue Bot",
        "version": "0.1.0",
    }


def test_queue():
    def handler(request):
        assert request.url.path == "/queue"

        return httpx.Response(
            200,
            json=[
                {
                    "id": 1,
                    "url": "https://youtu.be/example",
                    "status": "queued",
                }
            ],
        )

    client = make_client(handler)

    assert client.queue() == [
        {
            "id": 1,
            "url": "https://youtu.be/example",
            "status": "queued",
        }
    ]


def test_queue_rejects_non_list_response():
    def handler(request):
        return httpx.Response(
            200,
            json={"unexpected": True},
        )

    client = make_client(handler)

    with pytest.raises(
        BotClientError,
        match="invalid queue response",
    ):
        client.queue()


def test_twitch_status():
    def handler(request):
        assert request.url.path == "/twitch/status"

        return httpx.Response(
            200,
            json={
                "connected": True,
                "channels": ["teststreamer"],
            },
        )

    client = make_client(handler)

    assert client.twitch_status() == {
        "connected": True,
        "channels": ["teststreamer"],
    }


def test_join_twitch_channel():
    def handler(request):
        assert request.method == "POST"
        assert (
            request.url.path
            == "/twitch/channels/teststreamer/join"
        )

        return httpx.Response(
            200,
            json={
                "status": "joined",
                "channel": "teststreamer",
                "channels": ["teststreamer"],
            },
        )

    client = make_client(handler)

    result = client.join_twitch_channel("teststreamer")

    assert result["status"] == "joined"


def test_leave_twitch_channel():
    def handler(request):
        assert request.method == "POST"
        assert (
            request.url.path
            == "/twitch/channels/teststreamer/leave"
        )

        return httpx.Response(
            200,
            json={
                "status": "left",
                "channel": "teststreamer",
                "channels": [],
            },
        )

    client = make_client(handler)

    result = client.leave_twitch_channel("teststreamer")

    assert result["status"] == "left"


def test_channel_name_is_url_encoded():
    def handler(request):
        assert (
            request.url.raw_path
            == b"/twitch/channels/test%20streamer/join"
        )

        return httpx.Response(
            200,
            json={"status": "joined"},
        )

    client = make_client(handler)

    client.join_twitch_channel("test streamer")


def test_http_error_becomes_bot_client_error():
    def handler(request):
        return httpx.Response(
            500,
            json={"detail": "server exploded"},
        )

    client = make_client(handler)

    with pytest.raises(BotClientError):
        client.health()
