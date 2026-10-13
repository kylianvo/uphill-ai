"""POST /apple-health/sync, DELETE /apple-health and GET /status -- no DB.
Every db call the router makes is replaced by an in-memory fake."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from config import settings
from routers import integrations

app = FastAPI()
app.include_router(integrations.router, prefix="/api")
client = TestClient(app)

SYNC = "/api/integrations/apple-health/sync"


def _row(external_id="HK-1", **over):
    row = {
        "external_id": external_id,
        "activity_type": "outdoor_run",
        "start_time": "2026-10-12T06:00:00+07:00",
        "end_time": "2026-10-12T07:02:00+07:00",
        "duration_seconds": 3720,
        "distance_km": 10.4,
        "elevation_gain_m": 412,
        "avg_hr": 148,
        "max_hr": 171,
        "calories": 690,
        "source_name": "Apple Watch",
    }
    row.update(over)
    return row


@pytest.fixture
def fake(monkeypatch):
    state = {"connection": None, "stored": {}, "deleted": [], "synced": 0, "matched": [], "provider_deleted": []}

    def upsert(uid, activity):
        state["stored"].setdefault(activity.external_id, activity)
        return list(state["stored"]).index(activity.external_id) + 1

    def save_connection(
        uid, provider, access_token_enc, refresh_token_enc, token_expires_at, scopes, provider_user_id=None
    ):
        state["connection"] = {"provider": provider, "status": "active", "last_sync_at": None, "scopes": scopes}
        return 1

    def mark_synced(uid, provider):
        state["synced"] += 1
        state["connection"]["last_sync_at"] = datetime(2026, 10, 14, tzinfo=UTC)

    async def match_user(uid, since, until, plan_id=None, tz_offset_minutes=None):
        state["matched"].append((since, until, plan_id, tz_offset_minutes))
        return {"matched": 1, "suggested": 0, "unmatched": 0, "skipped_manual": 0}

    monkeypatch.setattr(
        integrations.db, "get_connection", lambda uid, p: state["connection"] if p == "apple_health" else None
    )
    monkeypatch.setattr(integrations.db, "save_connection", save_connection)
    monkeypatch.setattr(integrations.db, "upsert_activity", upsert)
    monkeypatch.setattr(
        integrations.db,
        "delete_activities_by_external_ids",
        lambda uid, p, ids: state["deleted"].extend(ids) or len(ids),
    )
    monkeypatch.setattr(integrations.db, "mark_connection_synced", mark_synced)
    monkeypatch.setattr(integrations.db, "delete_provider_data", lambda uid, p: state["provider_deleted"].append(p))
    monkeypatch.setattr(integrations.db, "get_user_by_id", lambda uid: {"id": uid})
    monkeypatch.setattr(integrations.matching_runner, "match_user", match_user)
    monkeypatch.setattr(settings, "APPLE_HEALTH_ENABLED", True)
    app.dependency_overrides[integrations.get_current_user] = lambda: {"id": 7}
    yield state
    app.dependency_overrides.pop(integrations.get_current_user, None)


def test_first_sync_creates_the_connection_and_stores_rows(fake):
    resp = client.post(SYNC, json={"workouts": [_row()], "deleted_ids": []})
    assert resp.status_code == 200
    body = resp.json()
    assert body["accepted"] == 1 and body["rejected"] == [] and body["deleted"] == 0
    assert fake["connection"]["provider"] == "apple_health"
    activity = fake["stored"]["HK-1"]
    assert activity.provider == "apple_health"
    assert activity.device_model == "Apple Watch"
    assert activity.avg_pace_sec_per_km == pytest.approx(3720 / 10.4)
    assert fake["synced"] == 1
    assert body["matching"]["matched"] == 1


def test_resending_the_same_batch_is_idempotent(fake):
    client.post(SYNC, json={"workouts": [_row()]})
    client.post(SYNC, json={"workouts": [_row()]})
    assert list(fake["stored"]) == ["HK-1"]


def test_empty_sync_still_marks_the_connection_synced(fake):
    resp = client.post(SYNC, json={"workouts": [], "deleted_ids": []})
    assert resp.status_code == 200
    assert fake["synced"] == 1


def test_deleted_ids_are_forwarded(fake):
    resp = client.post(SYNC, json={"workouts": [], "deleted_ids": ["HK-9", "HK-8"]})
    assert resp.json()["deleted"] == 2
    assert fake["deleted"] == ["HK-9", "HK-8"]


def test_implausible_rows_are_rejected_not_fatal(fake):
    future = (datetime.now(UTC) + timedelta(days=3)).isoformat()
    rows = [
        _row("ok"),
        _row("backwards", end_time="2026-10-12T05:00:00+07:00"),
        _row("naive", start_time="2026-10-12T06:00:00", end_time="2026-10-12T07:02:00"),
        _row("spike", max_hr=300),
        _row("too-fast", distance_km=40.0),
        _row("future", start_time=future, end_time=future),
        _row("cycling", activity_type="cycling"),
        _row("long", duration_seconds=49 * 3600),
    ]
    body = client.post(SYNC, json={"workouts": rows}).json()
    assert body["accepted"] == 1
    assert {r["external_id"] for r in body["rejected"]} == {
        "backwards",
        "naive",
        "spike",
        "too-fast",
        "future",
        "cycling",
        "long",
    }
    assert list(fake["stored"]) == ["ok"]


def test_strength_without_distance_is_accepted(fake):
    row = _row("gym", activity_type="strength", distance_km=None, elevation_gain_m=None)
    body = client.post(SYNC, json={"workouts": [row]}).json()
    assert body["accepted"] == 1
    assert fake["stored"]["gym"].avg_pace_sec_per_km is None


def test_batch_over_500_is_a_422(fake):
    rows = [_row(f"HK-{i}") for i in range(501)]
    assert client.post(SYNC, json={"workouts": rows}).status_code == 422


def test_matching_failure_does_not_fail_the_sync(fake, monkeypatch):
    async def boom(*a, **k):
        raise RuntimeError("matcher down")

    monkeypatch.setattr(integrations.matching_runner, "match_user", boom)
    resp = client.post(SYNC, json={"workouts": [_row()]})
    assert resp.status_code == 200
    assert resp.json()["matching"] is None


def test_disabled_flag_returns_404(fake, monkeypatch):
    monkeypatch.setattr(settings, "APPLE_HEALTH_ENABLED", False)
    assert client.post(SYNC, json={"workouts": []}).status_code == 404


def test_disconnect_deletes_provider_data(fake):
    resp = client.delete("/api/integrations/apple-health")
    assert resp.status_code == 200
    assert fake["provider_deleted"] == ["apple_health"]


def test_status_reports_apple_health(fake):
    client.post(SYNC, json={"workouts": []})
    body = client.get("/api/integrations/status").json()
    assert body["apple_health"]["enabled"] is True
    assert body["apple_health"]["connected"] is True
    assert body["apple_health"]["last_sync_at"] is not None
