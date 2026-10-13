"""Apple Health recovery metrics through the sync endpoint, on a live Postgres."""

from datetime import date, datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

import db
from config import settings
from routers import integrations
from services.providers.base import CanonicalDailyMetric

app = FastAPI()
app.include_router(integrations.router, prefix="/api")
client = TestClient(app)
SYNC = "/api/integrations/apple-health/sync"


@pytest.fixture()
def user_id(monkeypatch):
    with db.engine.connect() as conn:
        uid = conn.execute(
            text("INSERT INTO users (email, name, provider) VALUES (:e,:n,'email') RETURNING id"),
            {"e": f"health-{datetime.now().timestamp()}@test.local", "n": "Health Test"},
        ).scalar()
        conn.commit()

    async def no_match(*a, **k):
        return None

    monkeypatch.setattr(integrations.matching_runner, "match_user", no_match)
    monkeypatch.setattr(settings, "APPLE_HEALTH_ENABLED", True)
    monkeypatch.setattr(settings, "APPLE_HEALTH_RECOVERY_ENABLED", True)
    app.dependency_overrides[integrations.get_current_user] = lambda: {"id": uid}
    yield uid
    app.dependency_overrides.pop(integrations.get_current_user, None)


def _days(n, hrv=lambda i: 62.0, sleep=420):
    today = date.today()
    return [
        {
            "date": (today - timedelta(days=n - 1 - i)).isoformat(),
            "resting_hr": 52,
            "hrv_sdnn_ms": hrv(i) + (2 if i % 2 else -2),
            "sleep_minutes": sleep,
        }
        for i in range(n)
    ]


def _rows(uid):
    with db.engine.connect() as conn:
        return conn.execute(
            text(
                "SELECT metric_date, hrv_ms, hrv_baseline_ms, hrv_status, sleep_minutes, resting_hr "
                "FROM daily_metrics WHERE user_id = :u AND source_provider = 'apple_health' ORDER BY metric_date"
            ),
            {"u": uid},
        ).fetchall()


def test_thirty_days_store_rows_and_statuses_then_resync_overwrites(user_id):
    days = _days(30, hrv=lambda i: 49.0 if i >= 27 else 62.0)
    body = client.post(SYNC, json={"daily_metrics": days}).json()
    assert body["daily_metrics"]["accepted"] == 30

    rows = _rows(user_id)
    assert len(rows) == 30
    assert rows[0].hrv_status is None  # no history yet
    assert rows[-1].hrv_status == "low"  # last 3 days dipped
    assert rows[-1].sleep_minutes == 420
    assert rows[20].hrv_status == "normal"

    readiness = db.get_recent_readiness_summary(user_id, days=7)
    assert readiness["source_provider"] == "apple_health"
    assert readiness["readiness_flag"] == "fatigued"
    assert readiness["avg_sleep_minutes"] == 420

    # Re-send the last 3 days recovered: values are overwritten and the status follows.
    recovered = _days(3, hrv=lambda i: 63.0, sleep=450)
    client.post(SYNC, json={"daily_metrics": recovered})
    rows = _rows(user_id)
    assert len(rows) == 30
    assert rows[-1].sleep_minutes == 450
    assert rows[-1].hrv_status == "normal"


def test_coros_and_apple_rows_never_average(user_id):
    today = date.today()
    db.upsert_daily_metric(user_id, CanonicalDailyMetric(today - timedelta(days=1), "coros", hrv_ms=40.0))
    db.upsert_daily_metric(user_id, CanonicalDailyMetric(today, "apple_health", hrv_ms=90.0, sleep_minutes=400))
    readiness = db.get_recent_readiness_summary(user_id, days=7)
    assert readiness["source_provider"] == "apple_health"
    assert readiness["avg_hrv_ms"] == 90.0
    latest = db.get_latest_daily_metrics(user_id)
    assert latest["source_provider"] == "apple_health"
    assert latest["sleep_minutes"] == 400


def test_disconnect_removes_metric_rows(user_id):
    client.post(SYNC, json={"daily_metrics": _days(5)})
    assert len(_rows(user_id)) == 5
    client.delete("/api/integrations/apple-health")
    assert _rows(user_id) == []


def test_flag_off_stores_nothing(user_id, monkeypatch):
    monkeypatch.setattr(settings, "APPLE_HEALTH_RECOVERY_ENABLED", False)
    client.post(SYNC, json={"daily_metrics": _days(5)})
    assert _rows(user_id) == []
