from unittest.mock import AsyncMock, patch

from services.coros_push import PushError


def test_push_requires_auth(client):
    assert client.post("/api/integrations/coros/push", json={}).status_code == 401
    assert client.get("/api/integrations/coros/push-status").status_code == 401


def test_push_passes_user_today_and_lang(client, auth_headers):
    fake = AsyncMock(return_value={"status": "sent", "summary": {"workouts_sent": 3}, "last_pushed_at": "x"})
    with patch("routers.integrations.coros_push.push_plan", fake):
        resp = client.post(
            "/api/integrations/coros/push",
            headers=auth_headers["headers"],
            json={"client_today": "2099-01-01", "lang": "vi"},
        )
    assert resp.status_code == 200 and resp.json()["status"] == "sent"
    user_id, today, lang = fake.call_args.args
    assert user_id == auth_headers["user_id"] and lang == "vi"
    assert str(today) != "2099-01-01"  # out of the +-1 day tolerance -> server date


def test_push_error_maps_to_status_and_code(client, auth_headers):
    fake = AsyncMock(side_effect=PushError("PUSH_limit", 429, {"limit": 10}))
    with patch("routers.integrations.coros_push.push_plan", fake):
        resp = client.post("/api/integrations/coros/push", headers=auth_headers["headers"], json={})
    assert resp.status_code == 429
    assert resp.json() == {"detail": {"code": "PUSH_limit", "params": {"limit": 10}}}


def test_push_rejects_unknown_lang(client, auth_headers):
    resp = client.post("/api/integrations/coros/push", headers=auth_headers["headers"], json={"lang": "fr"})
    assert resp.status_code == 422


def test_push_status_not_connected(client, auth_headers):
    resp = client.get("/api/integrations/coros/push-status", headers=auth_headers["headers"])
    assert resp.status_code == 200 and resp.json() == {"connected": False}
