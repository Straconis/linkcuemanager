import json
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
        assert request.url.path == "/api/queue"

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


def test_history_uses_api_history_endpoint():
    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/api/history"

        return httpx.Response(
            200,
            json=[
                {
                    "id": 7,
                    "url": "https://youtu.be/history-example",
                    "status": "played",
                }
            ],
        )

    client = make_client(handler)

    assert client.history() == [
        {
            "id": 7,
            "url": "https://youtu.be/history-example",
            "status": "played",
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


def test_player_status():
    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/player/status"

        return httpx.Response(
            200,
            json={
                "active": True,
                "last_heartbeat": "2026-08-31T21:00:00+00:00",
                "timeout_seconds": 15,
            },
        )

    client = make_client(handler)

    assert client.player_status() == {
        "active": True,
        "last_heartbeat": "2026-08-31T21:00:00+00:00",
        "timeout_seconds": 15,
    }


def test_player_state():
    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/player/state"

        return httpx.Response(
            200,
            json={
                "state": "idle",
                "item": None,
            },
        )

    client = make_client(handler)

    assert client.player_state() == {
        "state": "idle",
        "item": None,
    }


def test_add_queue_item():
    def handler(request):
        assert request.method == "POST"
        assert request.url.path == "/queue"

        payload = __import__("json").loads(
            request.content.decode("utf-8")
        )

        assert payload == {
            "url": "https://youtu.be/example",
            "title": None,
            "video_channel": None,
            "twitch_channel": None,
            "submitted_by": "Steve",
            "submission_source": "manager",
        }

        return httpx.Response(
            201,
            json={"id": 42},
        )

    client = make_client(handler)

    result = client.add_queue_item(
        "https://youtu.be/example",
        submitted_by="Steve",
    )

    assert result == {"id": 42}


def test_move_queue_item():
    def handler(request):
        assert request.method == "POST"
        assert request.url.path == "/queue/42/move"

        payload = __import__("json").loads(
            request.content.decode("utf-8")
        )

        assert payload == {
            "position": 1,
        }

        return httpx.Response(
            200,
            json={
                "status": "moved",
                "id": 42,
                "position": 1,
            },
        )

    client = make_client(handler)

    result = client.move_queue_item(
        42,
        1,
    )

    assert result["status"] == "moved"
    assert result["position"] == 1


def test_remove_queue_item():
    def handler(request):
        assert request.method == "DELETE"
        assert request.url.path == "/queue/42"

        return httpx.Response(
            200,
            json={
                "status": "deleted",
                "id": 42,
            },
        )

    client = make_client(handler)

    result = client.remove_queue_item(42)

    assert result == {
        "status": "deleted",
        "id": 42,
    }

def test_json_request_sets_application_json_content_type():
    import json

    captured = {}

    def handler(request):
        captured["content_type"] = request.headers.get(
            "Content-Type"
        )
        captured["body"] = request.content

        return httpx.Response(
            200,
            json={
                "bot_url": "http://de1.bot-hosting.cloud",
                "bot_port": 25479,
                "restart_required": True,
            },
        )

    client = BotClient(
        "http://example.test",
        transport=httpx.MockTransport(handler),
    )

    client.identity_store.load_identity = lambda: None

    client.set_bot_connection(
        "http://de1.bot-hosting.cloud",
        25479,
    )

    assert captured["content_type"] == "application/json"

    assert json.loads(captured["body"]) == {
        "bot_url": "http://de1.bot-hosting.cloud",
        "bot_port": 25479,
    }


def test_restart_bot_posts_to_maintenance_restart():
    captured = {}

    def handler(request: httpx.Request):
        captured["method"] = request.method
        captured["path"] = request.url.path

        return httpx.Response(
            200,
            json={"status": "restart_requested"},
        )

    client = BotClient(
        "http://example.test",
        transport=httpx.MockTransport(handler),
    )
    client.identity_store.load_identity = lambda: None

    result = client.restart_bot()

    assert captured == {
        "method": "POST",
        "path": "/maintenance/restart",
    }
    assert result == {
        "status": "restart_requested"
    }


def test_twitch_setting():
    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/settings/twitch"

        return httpx.Response(
            200,
            json={
                "channel_url": "https://twitch.tv/smokeeeg",
                "channel": "smokeeeg",
                "populate_channel_from_url": True,
            },
        )

    client = make_client(handler)

    assert client.twitch_setting() == {
        "channel_url": "https://twitch.tv/smokeeeg",
        "channel": "smokeeeg",
        "populate_channel_from_url": True,
    }


def test_set_twitch_setting():
    def handler(request):
        assert request.method == "PUT"
        assert request.url.path == "/settings/twitch"

        assert json.loads(request.content) == {
            "channel_url": "https://twitch.tv/smokeeeg",
            "channel": "specialchannel",
            "populate_channel_from_url": False,
        }

        return httpx.Response(
            200,
            json={
                "channel_url": "https://twitch.tv/smokeeeg",
                "channel": "specialchannel",
                "populate_channel_from_url": False,
            },
        )

    client = make_client(handler)

    result = client.set_twitch_setting(
        "https://twitch.tv/smokeeeg",
        "specialchannel",
        False,
    )

    assert result == {
        "channel_url": "https://twitch.tv/smokeeeg",
        "channel": "specialchannel",
        "populate_channel_from_url": False,
    }
