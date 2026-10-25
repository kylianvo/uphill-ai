"""Garmin connect, webhook and push ingest -- no DB, no live Garmin. Payloads are synthetic."""

import asyncio
import base64
from datetime import UTC, datetime

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from config import settings
from routers import integrations
from services import garmin_ingest, garmin_oauth
from services.coros_oauth import TokenSet
from services.providers import garmin

app = FastAPI()
app.include_router(integrations.router, prefix="/api")
app.dependency_overrides[integrations.get_current_user] = lambda: {"id": 42}
client = TestClient(app, follow_redirects=False)


@pytest.fixture(autouse=True)
def _garmin_on(monkeypatch):
    monkeypatch.setattr(settings, "GARMIN_ENABLED", True)
    monkeypatch.setattr(settings, "GARMIN_CLIENT_ID", "client-1")
    monkeypatch.setattr(settings, "GARMIN_CLIENT_SECRET", "secret-1")
    monkeypatch.setattr(settings, "GARMIN_WEBHOOK_TOKEN", "hook-token")
    monkeypatch.setattr(settings, "TOKEN_ENCRYPTION_KEY", "k" * 44)
    integrations._PENDING_AUTH.clear()
    client.cookies.clear()


RUN = {
    "userId": "g-1",
    "activityId": 5001,
    "activityType": "TRAIL_RUNNING",
    "startTimeInSeconds": 1_760_000_000,
    "startTimeOffsetInSeconds": 25_200,
    "durationInSeconds": 3600,
    "distanceInMeters": 10_000.0,
    "totalElevationGainInMeters": 650.0,
    "averageHeartRateInBeatsPerMinute": 142,
    "maxHeartRateInBeatsPerMinute": 171.0,
    "deviceName": "fenix 8",
}


# --- mapping -------------------------------------------------------------


def test_trail_run_maps_to_canonical_activity():
    a = garmin.to_activity(RUN)
    assert (a.external_id, a.provider, a.activity_type) == ("5001", "garmin", "trail_run")
    assert a.start_time == datetime.fromtimestamp(1_760_000_000, UTC)
    assert a.distance_km == 10.0 and a.avg_pace_sec_per_km == 360.0
    assert a.max_hr == 171 and a.device_model == "fenix 8"
    assert garmin.offset_minutes(RUN) == 420


def test_activity_details_read_the_nested_summary():
    details = {"userId": "g-1", "activityId": 5001, "summary": {k: v for k, v in RUN.items() if k != "activityId"}}
    assert garmin.to_activity(details) == garmin.to_activity(RUN)


def test_untracked_types_and_incomplete_items_are_skipped():
    assert garmin.to_activity({**RUN, "activityType": "TENNIS"}) is None
    assert garmin.to_activity({**RUN, "durationInSeconds": 0}) is None
    manual = garmin.to_activity({**RUN, "activityType": "STRENGTH_TRAINING", "deviceName": "unknown"})
    assert manual.activity_type == "strength" and manual.device_model is None and manual.avg_pace_sec_per_km is None


# --- OAuth ---------------------------------------------------------------


def test_token_exchange_uses_basic_auth_and_keeps_the_rotated_refresh_token():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers["authorization"]
        seen["body"] = request.content.decode()
        return httpx.Response(200, json={"access_token": "a", "refresh_token": "r2", "expires_in": 86400})

    tokens = asyncio.run(garmin_oauth.refresh("r1", transport=httpx.MockTransport(handler)))
    assert seen["auth"] == "Basic " + base64.b64encode(b"client-1:secret-1").decode()
    assert "grant_type=refresh_token" in seen["body"] and "refresh_token=r1" in seen["body"]
    assert tokens.refresh_token == "r2"


def test_connect_requires_ai_consent():
    assert client.get("/api/integrations/garmin/connect").status_code == 400
    resp = client.get("/api/integrations/garmin/connect", params={"ai_consent": "true"})
    assert resp.status_code == 200
    assert resp.json()["authorize_url"].startswith(garmin_oauth.AUTHORIZE_URL)
    assert "garmin_oauth_state" in resp.cookies


def test_connect_is_hidden_while_disabled(monkeypatch):
    monkeypatch.setattr(settings, "GARMIN_ENABLED", False)
    assert client.get("/api/integrations/garmin/connect", params={"ai_consent": "true"}).status_code == 404


def _exchange_stubs(monkeypatch, linked_to: int | None = None):
    async def exchange(code, verifier):
        return TokenSet("a", "r", None)

    async def user_id(token):
        return "g-1"

    async def permissions(token):
        return ["WORKOUT_IMPORT", "ACTIVITY_EXPORT"]

    saved, excluded = [], []
    monkeypatch.setattr(garmin_oauth, "exchange_code", exchange)
    monkeypatch.setattr(garmin_oauth, "fetch_user_id", user_id)
    monkeypatch.setattr(garmin_oauth, "fetch_permissions", permissions)
    monkeypatch.setattr(integrations.token_crypto, "encrypt_token", lambda t: f"enc:{t}")
    monkeypatch.setattr(
        integrations.db,
        "get_connection_by_provider_user",
        lambda p, pu: {"user_id": linked_to} if linked_to is not None else None,
    )
    monkeypatch.setattr(integrations.db, "save_connection", lambda **kw: saved.append(kw))
    monkeypatch.setattr(integrations.db, "mark_ai_eval_excluded", excluded.append)
    return saved, excluded


def test_exchange_saves_the_garmin_user_and_excludes_the_athlete_from_ai_evaluation(monkeypatch):
    saved, excluded = _exchange_stubs(monkeypatch)
    assert asyncio.run(integrations._garmin_exchange_and_save("code", "verifier", 42))
    assert saved[0]["provider_user_id"] == "g-1" and saved[0]["scopes"] == "ACTIVITY_EXPORT WORKOUT_IMPORT"
    assert excluded == [42]


def test_a_garmin_account_already_linked_to_another_athlete_is_refused(monkeypatch):
    saved, excluded = _exchange_stubs(monkeypatch, linked_to=7)
    assert not asyncio.run(integrations._garmin_exchange_and_save("code", "verifier", 42))
    assert saved == [] and excluded == []


def test_disconnect_deletes_data_even_when_garmin_deregistration_fails(monkeypatch):
    deleted = []

    async def token(connection):
        raise garmin_oauth.GarminAuthError("expired")

    monkeypatch.setattr(integrations.db, "get_connection", lambda u, p: {"user_id": u})
    monkeypatch.setattr(garmin_oauth, "access_token", token)
    monkeypatch.setattr(integrations.db, "delete_provider_data", lambda u, p: deleted.append((u, p)))
    assert client.delete("/api/integrations/garmin").json() == {"status": "disconnected"}
    assert deleted == [(42, "garmin")]


# --- webhook -------------------------------------------------------------

HOOK = "/api/integrations/garmin/webhook/hook-token"


def test_webhook_rejects_a_wrong_token_or_client_id(monkeypatch):
    processed = []
    monkeypatch.setattr(garmin_ingest, "process", lambda body: processed.append(body))
    assert (
        client.post(
            "/api/integrations/garmin/webhook/nope", json={}, headers={"garmin-client-id": "client-1"}
        ).status_code
        == 404
    )
    assert client.post(HOOK, json={}, headers={"garmin-client-id": "other"}).status_code == 404
    assert processed == []


def test_webhook_acknowledges_and_processes_in_the_background(monkeypatch):
    processed = []

    async def process(body):
        processed.append(body)

    monkeypatch.setattr(garmin_ingest, "process", process)
    resp = client.post(HOOK, json={"activities": [RUN]}, headers={"garmin-client-id": "client-1"})
    assert resp.status_code == 200
    assert processed == [{"activities": [RUN]}]


# --- ingest --------------------------------------------------------------


def _ingest_stubs(monkeypatch):
    calls = {"upsert": [], "match": [], "delete": [], "scopes": []}
    connections = {"g-1": {"user_id": 42}}

    async def match_user(user_id, since, until, plan_id=None, tz_offset_minutes=None):
        calls["match"].append((user_id, tz_offset_minutes))

    monkeypatch.setattr(garmin_ingest.db, "get_connection_by_provider_user", lambda p, pu: connections.get(pu))
    monkeypatch.setattr(garmin_ingest.db, "get_connection", lambda u, p: {"user_id": u})
    monkeypatch.setattr(garmin_ingest.db, "upsert_activity", lambda u, a: calls["upsert"].append((u, a.external_id)))
    monkeypatch.setattr(garmin_ingest.db, "mark_connection_synced", lambda u, p: None)
    monkeypatch.setattr(garmin_ingest.db, "delete_provider_data", lambda u, p: calls["delete"].append((u, p)))
    monkeypatch.setattr(garmin_ingest.db, "set_connection_scopes", lambda u, p, s: calls["scopes"].append((u, s)))
    monkeypatch.setattr(garmin_ingest.matching_runner, "match_user", match_user)
    return calls


def test_ingest_stores_known_users_activities_then_matches(monkeypatch):
    calls = _ingest_stubs(monkeypatch)
    body = {"activities": [RUN, {**RUN, "userId": "stranger", "activityId": 9}, {**RUN, "activityType": "GOLF"}]}
    asyncio.run(garmin_ingest.process(body))
    assert calls["upsert"] == [(42, "5001")]
    assert calls["match"] == [(42, 420)]


def test_ingest_deregistration_deletes_and_permission_change_updates_scopes(monkeypatch):
    calls = _ingest_stubs(monkeypatch)
    _registration(monkeypatch, live=False)
    asyncio.run(
        garmin_ingest.process(
            {
                "deregistrations": [{"userId": "g-1"}, {"userId": "stranger"}],
                "userPermissionsChange": [{"userId": "g-1", "permissions": ["HEALTH_EXPORT", "ACTIVITY_EXPORT"]}],
                "sleeps": [{"userId": "g-1"}],
            }
        )
    )
    assert calls["delete"] == [(42, "garmin")]
    assert calls["scopes"] == [(42, "ACTIVITY_EXPORT HEALTH_EXPORT")]


def _registration(monkeypatch, live: bool):
    async def token(connection):
        return "a"

    async def user_id(token):
        if not live:
            raise garmin_oauth.GarminAuthError("403", 403)
        return "g-1"

    monkeypatch.setattr(garmin_oauth, "access_token", token)
    monkeypatch.setattr(garmin_oauth, "fetch_user_id", user_id)


def test_a_deregistration_garmin_still_answers_for_is_ignored(monkeypatch):
    calls = _ingest_stubs(monkeypatch)
    _registration(monkeypatch, live=True)
    asyncio.run(garmin_ingest.process({"deregistrations": [{"userId": "g-1"}]}))
    assert calls["delete"] == []


def test_webhook_token_is_redacted_from_access_logs():
    import logging

    record = logging.LogRecord(
        "uvicorn.access",
        logging.INFO,
        "",
        0,
        '%s - "%s %s HTTP/%s" %d',
        ("1.2.3.4:5", "POST", "/api/integrations/garmin/webhook/hook-token", "1.1", 200),
        None,
    )
    integrations._RedactGarminWebhookToken().filter(record)
    assert "hook-token" not in record.getMessage() and "/garmin/webhook/[redacted]" in record.getMessage()


def test_a_deregistration_is_not_acted_on_when_garmin_cannot_be_reached(monkeypatch):
    calls = _ingest_stubs(monkeypatch)

    async def token(connection):
        return "a"

    async def user_id(token):
        raise garmin_oauth.GarminAuthError("503", 503)

    monkeypatch.setattr(garmin_oauth, "access_token", token)
    monkeypatch.setattr(garmin_oauth, "fetch_user_id", user_id)
    asyncio.run(garmin_ingest.process({"deregistrations": [{"userId": "g-1"}]}))
    assert calls["delete"] == []


def test_concurrent_token_refreshes_for_one_athlete_refresh_once(monkeypatch):
    from datetime import timedelta

    stored = {
        "user_id": 42,
        "access_token_enc": "old",
        "refresh_token_enc": "r1",
        "token_expires_at": datetime.now(UTC) - timedelta(minutes=1),
    }
    refreshes = []

    async def refresh(token, transport=None):
        refreshes.append(token)
        await asyncio.sleep(0)
        return TokenSet("new", "r2", datetime.now(UTC) + timedelta(days=1))

    def save_connection(**kw):
        stored.update(
            access_token_enc=kw["access_token_enc"],
            refresh_token_enc=kw["refresh_token_enc"],
            token_expires_at=kw["token_expires_at"],
        )

    monkeypatch.setattr(garmin_oauth, "refresh", refresh)
    monkeypatch.setattr(garmin_oauth.db, "get_connection", lambda u, p: dict(stored))
    monkeypatch.setattr(garmin_oauth.db, "save_connection", save_connection)
    monkeypatch.setattr(garmin_oauth.token_crypto, "encrypt_token", lambda t: t)
    monkeypatch.setattr(garmin_oauth.token_crypto, "decrypt_token", lambda t: t)

    async def both():
        return await asyncio.gather(garmin_oauth.access_token(dict(stored)), garmin_oauth.access_token(dict(stored)))

    assert asyncio.run(both()) == ["new", "new"]
    assert refreshes == ["r1"]


# --- recovery (Phase 2) --------------------------------------------------


def test_recovery_summaries_map_to_their_own_fields():
    from datetime import date, time

    rhr = garmin.to_daily_metric("dailies", {"calendarDate": "2026-10-24", "restingHeartRateInBeatsPerMinute": 48})
    hrv = garmin.to_daily_metric("hrv", {"calendarDate": "2026-10-24", "lastNightAvg": 62})
    sleep = garmin.to_daily_metric(
        "sleeps",
        {
            "calendarDate": "2026-10-24",
            "startTimeInSeconds": 1_761_235_200,  # 2026-10-23 16:00 UTC
            "startTimeOffsetInSeconds": 25_200,  # UTC+7: 23:00 local
            "durationInSeconds": 7 * 3600,
            "awakeDurationInSeconds": 1800,
            "validation": "AUTO_FINAL",
        },
    )
    assert (rhr.metric_date, rhr.resting_hr, rhr.hrv_ms) == (date(2026, 10, 24), 48, None)
    assert hrv.hrv_ms == 62.0 and hrv.resting_hr is None
    assert sleep.sleep_minutes == 420 and sleep.sleep_start == time(23, 0) and sleep.sleep_end == time(6, 30)


def test_unmeasured_or_implausible_recovery_is_skipped():
    day = {"calendarDate": "2026-10-24"}
    assert garmin.to_daily_metric("dailies", {**day, "restingHeartRateInBeatsPerMinute": 0}) is None
    assert garmin.to_daily_metric("hrv", {**day, "lastNightAvg": 900}) is None
    off_wrist = {**day, "startTimeInSeconds": 1, "durationInSeconds": 25_000, "validation": "OFF_WRIST"}
    assert garmin.to_daily_metric("sleeps", off_wrist) is None
    assert garmin.to_daily_metric("sleeps", {**off_wrist, "validation": "MANUAL"}) is None
    assert garmin.to_daily_metric("dailies", {"calendarDate": "n/a", "restingHeartRateInBeatsPerMinute": 50}) is None


def test_ingest_stores_recovery_and_derives_hrv_status_from_the_baseline(monkeypatch):
    _ingest_stubs(monkeypatch)
    stored, refreshed = [], []
    monkeypatch.setattr(
        garmin_ingest.db, "upsert_daily_metric", lambda u, m: stored.append((u, m.resting_hr, m.hrv_ms))
    )
    monkeypatch.setattr(garmin_ingest.recovery_baseline, "refresh", lambda u, d, p: refreshed.append((u, sorted(d), p)))
    asyncio.run(
        garmin_ingest.process(
            {
                "dailies": [{"userId": "g-1", "calendarDate": "2026-10-24", "restingHeartRateInBeatsPerMinute": 48}],
                "hrv": [
                    {"userId": "g-1", "calendarDate": "2026-10-24", "lastNightAvg": 62},
                    {"userId": "stranger", "calendarDate": "2026-10-24", "lastNightAvg": 70},
                ],
            }
        )
    )
    assert stored == [(42, 48, None), (42, None, 62.0)]
    from datetime import date

    assert refreshed == [(42, [date(2026, 10, 24)], "garmin")]
