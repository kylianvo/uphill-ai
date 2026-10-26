from uuid import uuid4


def test_preferences_validate_and_ignore_identity(client, auth_headers):
    path = "/api/notifications/preferences"
    headers = auth_headers["headers"]
    assert client.patch(path, headers=headers, json={"timezone": "Bad/Zone"}).status_code == 422
    assert client.patch(path, headers=headers, json={"user_id": 99}).status_code == 422
    assert client.patch(path, headers=headers, json={"quiet_start": "07:00"}).status_code == 422
    r = client.patch(path, headers=headers, json={"timezone": "Australia/Sydney", "workouts_enabled": True})
    assert r.status_code == 200
    assert r.json()["workouts_enabled"] is True


def test_registration_and_open_are_owned(client, auth_headers):
    path = "/api/notifications/installations/" + str(uuid4())
    body = {"token": "ab" * 32, "environment": "sandbox", "permission": "authorized"}
    assert client.put(path, json=body).status_code == 401
    assert client.put(path, json=body, headers=auth_headers["headers"]).status_code == 200
    assert (
        client.post("/api/notifications/" + str(uuid4()) + "/opened", headers=auth_headers["headers"]).status_code
        == 404
    )


def test_available_only_when_delivery_on_and_allowlisted(client, auth_headers, monkeypatch):
    from config import settings

    path, headers = "/api/notifications/preferences", auth_headers["headers"]
    assert client.get(path, headers=headers).json()["available"] is False
    monkeypatch.setattr(settings, "NOTIFICATION_WORKER_ENABLED", True)
    monkeypatch.setattr(settings, "NOTIFICATION_DELIVERY_ENABLED", True)
    monkeypatch.setattr(settings, "NOTIFICATION_ALLOWLIST", str(auth_headers["user_id"]))
    assert client.get(path, headers=headers).json()["available"] is True


def _event(user_id, kind):
    from datetime import UTC, datetime, timedelta

    from db import engine
    from services.notification_store import insert_event

    now = datetime.now(UTC)
    with engine.begin() as conn:
        return insert_event(
            conn,
            user_id,
            dict(event_key=f"{kind}:test", kind=kind, destination={}, due_at=now, expires_at=now + timedelta(hours=1)),
        )


def test_feedback_mutes_the_events_kind(client, auth_headers):
    headers = auth_headers["headers"]
    event = _event(auth_headers["user_id"], "week_brief")
    assert client.post(f"/api/notifications/{event}/feedback", headers=headers, json={"less": True}).status_code == 200
    assert client.get("/api/notifications/preferences", headers=headers).json()["muted_kinds"] == ["week_brief"]


def test_feedback_ignores_kinds_that_cannot_be_muted(client, auth_headers):
    headers = auth_headers["headers"]
    event = _event(auth_headers["user_id"], "workout")
    assert client.post(f"/api/notifications/{event}/feedback", headers=headers, json={"less": True}).status_code == 200
    assert client.get("/api/notifications/preferences", headers=headers).json()["muted_kinds"] == []


def test_feedback_is_owner_checked(client, auth_headers):
    path = f"/api/notifications/{uuid4()}/feedback"
    assert client.post(path, headers=auth_headers["headers"], json={"less": True}).status_code == 404


def test_patch_can_only_shrink_muted_kinds(client, auth_headers):
    path, headers = "/api/notifications/preferences", auth_headers["headers"]
    event = _event(auth_headers["user_id"], "week_brief")
    client.post(f"/api/notifications/{event}/feedback", headers=headers, json={"less": True})
    assert client.patch(path, headers=headers, json={"muted_kinds": ["week_brief", "knowledge"]}).status_code == 422
    assert client.patch(path, headers=headers, json={"muted_kinds": ["bogus"]}).status_code == 422
    r = client.patch(path, headers=headers, json={"muted_kinds": []})
    assert r.status_code == 200 and r.json()["muted_kinds"] == []


def test_old_build_time_fields_still_accepted(client, auth_headers):
    body = {"workout_time": "06:30", "coaching_time": "19:00", "quiet_start": "22:00", "quiet_end": "06:00"}
    assert client.patch("/api/notifications/preferences", headers=auth_headers["headers"], json=body).status_code == 200
