import json
import httpx
import pytest

from app.bot_client import BotClient, BotClientError
from app.linkcue_identity import LinkCueIdentity


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


def test_twitch_auth_status():
    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/twitch/auth/status"

        return httpx.Response(
            200,
            json={
                "authorized": True,
                "user_id": "12345",
                "login": "linkcuebot",
            },
        )

    client = make_client(handler)

    assert client.twitch_auth_status() == {
        "authorized": True,
        "user_id": "12345",
        "login": "linkcuebot",
    }


def test_authorize_twitch():
    def handler(request):
        assert request.method == "POST"
        assert request.url.path == "/twitch/auth/authorize"

        return httpx.Response(
            200,
            json={
                "authorization_url": "https://example.test/twitch/oauth",
            },
        )

    client = make_client(handler)

    assert client.authorize_twitch() == {
        "authorization_url": "https://example.test/twitch/oauth",
    }


def test_connect_twitch():
    def handler(request):
        assert request.method == "POST"
        assert request.url.path == "/twitch/connect"

        return httpx.Response(
            200,
            json={
                "connected": True,
                "channels": [],
            },
        )

    client = make_client(handler)

    assert client.connect_twitch() == {
        "connected": True,
        "channels": [],
    }


def test_disconnect_twitch():
    def handler(request):
        assert request.method == "POST"
        assert request.url.path == "/twitch/disconnect"

        return httpx.Response(
            200,
            json={
                "connected": False,
                "channels": [],
            },
        )

    client = make_client(handler)

    assert client.disconnect_twitch() == {
        "connected": False,
        "channels": [],
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


def test_validation_error_does_not_expose_request_input():
    secret = "do-not-leak-this-secret"

    def handler(request):
        return httpx.Response(
            422,
            json={
                "detail": [
                    {
                        "type": "model_attributes_type",
                        "loc": ["body"],
                        "msg": "Input should be a valid dictionary or object",
                        "input": secret,
                    }
                ]
            },
        )

    client = make_client(handler)

    with pytest.raises(BotClientError) as exc_info:
        client.health()

    error = exc_info.value

    assert secret not in str(error)
    assert secret not in (error.detail or "")


def test_list_bans():
    seen = []

    def handler(request):
        seen.append(
            (
                request.method,
                request.url.path,
                request.url.params.get(
                    "include_inactive"
                ),
            )
        )

        return httpx.Response(
            200,
            json=[],
        )

    client = make_client(handler)

    assert client.creator_bans(
        include_inactive=True
    ) == []
    assert client.video_bans(
        include_inactive=True
    ) == []

    assert seen == [
        (
            "GET",
            "/bans/creators",
            "true",
        ),
        (
            "GET",
            "/bans/videos",
            "true",
        ),
    ]


def test_manage_creator_bans():
    requests = []

    def handler(request):
        body = (
            json.loads(request.content)
            if request.content
            else None
        )
        requests.append(
            (
                request.method,
                request.url.path,
                body,
            )
        )

        if request.method == "POST":
            return httpx.Response(
                201,
                json={"ban_id": 12},
            )

        if request.method == "PATCH":
            return httpx.Response(
                200,
                json={
                    "ban_id": 12,
                    "active": False,
                    "changed": True,
                },
            )

        return httpx.Response(
            200,
            json=[
                {
                    "action": "banned",
                    "actor": "manager-example",
                }
            ],
        )

    client = make_client(handler)

    assert client.add_creator_ban(
        platform="youtube",
        video_creator_id="UC_TEST",
        video_channel="Test Channel",
        reason="Repeated submissions",
    ) == {
        "ban_id": 12,
    }

    assert client.set_creator_ban_active(
        12,
        active=False,
        reason="Appeal accepted",
    ) == {
        "ban_id": 12,
        "active": False,
        "changed": True,
    }

    assert client.creator_ban_audit(12) == [
        {
            "action": "banned",
            "actor": "manager-example",
        }
    ]

    assert requests == [
        (
            "POST",
            "/bans/creators",
            {
                "platform": "youtube",
                "video_creator_id": "UC_TEST",
                "video_channel": "Test Channel",
                "reason": "Repeated submissions",
            },
        ),
        (
            "PATCH",
            "/bans/creators/12",
            {
                "active": False,
                "reason": "Appeal accepted",
            },
        ),
        (
            "GET",
            "/bans/creators/12/audit",
            None,
        ),
    ]


def test_manage_video_bans():
    requests = []

    def handler(request):
        body = (
            json.loads(request.content)
            if request.content
            else None
        )
        requests.append(
            (
                request.method,
                request.url.path,
                body,
            )
        )

        if request.method == "POST":
            return httpx.Response(
                201,
                json={"ban_id": 21},
            )

        if request.method == "PATCH":
            return httpx.Response(
                200,
                json={
                    "ban_id": 21,
                    "active": True,
                    "changed": True,
                },
            )

        return httpx.Response(
            200,
            json=[
                {
                    "action": "rebanned",
                    "actor": "manager-example",
                }
            ],
        )

    client = make_client(handler)

    assert client.add_video_ban(
        platform="youtube",
        video_platform_id="video123",
        title="Test Video",
        url="https://youtu.be/video123",
        reason="Blocked video",
    ) == {
        "ban_id": 21,
    }

    assert client.set_video_ban_active(
        21,
        active=True,
        reason="Ban restored",
    ) == {
        "ban_id": 21,
        "active": True,
        "changed": True,
    }

    assert client.video_ban_audit(21) == [
        {
            "action": "rebanned",
            "actor": "manager-example",
        }
    ]

    assert requests == [
        (
            "POST",
            "/bans/videos",
            {
                "platform": "youtube",
                "video_platform_id": "video123",
                "title": "Test Video",
                "url": "https://youtu.be/video123",
                "reason": "Blocked video",
            },
        ),
        (
            "PATCH",
            "/bans/videos/21",
            {
                "active": True,
                "reason": "Ban restored",
            },
        ),
        (
            "GET",
            "/bans/videos/21/audit",
            None,
        ),
    ]


def test_software_status():
    payload = {
        "bot": {
            "status": "online",
            "version": "0.1.0",
            "api_version": "0.1",
        },
        "managers": [
            {
                "display_name": "Steve",
                "version": "0.1.0",
                "client_id": "manager-example",
            }
        ],
        "players": [],
    }

    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/software/status"

        return httpx.Response(
            200,
            json=payload,
        )

    client = make_client(handler)

    assert client.software_status() == payload


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


def test_create_manager_pairing_request():
    def handler(request):
        assert request.method == "POST"
        assert request.url.path == "/auth/create-pairing"

        payload = json.loads(
            request.content.decode("utf-8")
        )

        assert payload == {
            "role": "manager",
            "control_password": "shared-password",
        }

        return httpx.Response(
            200,
            json={
                "code": "123456",
                "role": "manager",
                "expires_at": "2026-09-06T08:00:00+00:00",
            },
        )

    client = make_client(handler)

    result = client.create_manager_pairing(
        "shared-password"
    )

    assert result["code"] == "123456"
    assert result["role"] == "manager"


def test_pair_manager_client():
    def handler(request):
        assert request.method == "POST"
        assert request.url.path == "/auth/pair"

        payload = json.loads(
            request.content.decode("utf-8")
        )

        assert payload == {
            "code": "123456",
            "role": "manager",
            "control_password": "shared-password",
        }

        return httpx.Response(
            200,
            json={
                "client_id": "manager-example",
                "role": "manager",
                "secret": "ab" * 32,
            },
        )

    client = make_client(handler)

    result = client.pair_manager(
        "123456",
        "shared-password",
    )

    assert result == {
        "client_id": "manager-example",
        "role": "manager",
        "secret": "ab" * 32,
    }


def test_host_control_provisioning():
    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/provisioning/host-control"

        return httpx.Response(
            200,
            json={
                "bot_hosting_api_key": "host-control-secret",
            },
        )

    client = make_client(handler)

    result = client.host_control_provisioning()

    assert result == {
        "bot_hosting_api_key": "host-control-secret",
    }

def test_signed_json_request_keeps_content_type(monkeypatch):
    def handler(request):
        assert request.method == "POST"
        assert request.url.path == "/auth/create-pairing"
        assert (
            request.headers["Content-Type"]
            == "application/json"
        )

        payload = json.loads(
            request.content.decode("utf-8")
        )

        assert payload == {
            "role": "manager",
            "control_password": "shared-password",
        }

        return httpx.Response(
            200,
            json={
                "code": "123456",
                "role": "manager",
                "expires_at": "future",
            },
        )

    client = make_client(handler)

    identity = LinkCueIdentity(
        client_id="manager-existing",
        role="manager",
        secret="ab" * 32,
    )

    monkeypatch.setattr(
        client.identity_store,
        "load_identity",
        lambda: identity,
    )

    result = client.create_manager_pairing(
        "shared-password"
    )

    assert result["code"] == "123456"

def test_twitch_broadcaster_auth_status():
    def handler(request):
        assert request.method == "GET"
        assert (
            request.url.path
            == "/twitch/broadcaster/auth/status"
        )

        return httpx.Response(
            200,
            json={
                "authorized": True,
                "user_id": "987654",
                "login": "smokeeeg",
            },
        )

    client = make_client(handler)

    assert client.twitch_broadcaster_auth_status() == {
        "authorized": True,
        "user_id": "987654",
        "login": "smokeeeg",
    }


def test_authorize_twitch_broadcaster():
    def handler(request):
        assert request.method == "POST"
        assert (
            request.url.path
            == "/twitch/broadcaster/auth/authorize"
        )

        return httpx.Response(
            200,
            json={
                "authorization_url": (
                    "https://example.test/"
                    "twitch/broadcaster/oauth"
                ),
            },
        )

    client = make_client(handler)

    assert client.authorize_twitch_broadcaster() == {
        "authorization_url": (
            "https://example.test/twitch/broadcaster/oauth"
        ),
    }
