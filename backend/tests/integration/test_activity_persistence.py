"""Persistence tests for activities and daily metrics. Needs a live Postgres."""

from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import text

import db
from services.providers.base import CanonicalActivity, CanonicalDailyMetric

START = datetime(2026, 8, 29, 5, 45, tzinfo=UTC)


def _activity(external_id="a1", provider="coros", start=START, distance=15.03, duration=5434.0):
    return CanonicalActivity(
        external_id=external_id,
        provider=provider,
        activity_type="trail_run",
        start_time=start,
        duration_seconds=duration,
        distance_km=distance,
        avg_hr=148,
        device_model="COROS APEX PRO",
    )


@pytest.fixture()
def user_id():
    with db.engine.connect() as conn:
        row = conn.execute(
            text("INSERT INTO users (email, name, provider) VALUES (:e,:n,'email') RETURNING id"),
            {"e": f"sync-{datetime.now().timestamp()}@test.local", "n": "Sync Test"},
        ).fetchone()
        conn.commit()
    return row[0]


def test_upsert_activity_inserts_once(user_id):
    first = db.upsert_activity(user_id, _activity())
    assert first is not None


def test_upsert_activity_is_idempotent_for_the_same_external_id(user_id):
    first = db.upsert_activity(user_id, _activity())
    second = db.upsert_activity(user_id, _activity())
    assert first == second


def test_activity_stores_device_model(user_id):
    activity_id = db.upsert_activity(user_id, _activity())
    with db.engine.connect() as conn:
        model = conn.execute(text("SELECT device_model FROM activities WHERE id = :i"), {"i": activity_id}).scalar()
    assert model == "COROS APEX PRO"


def test_near_identical_activity_from_another_provider_is_marked_duplicate(user_id):
    original = db.upsert_activity(user_id, _activity(external_id="c1", provider="coros"))
    mirror = db.upsert_activity(
        user_id,
        _activity(external_id="m1", provider="manual", start=START + timedelta(minutes=2)),
    )
    with db.engine.connect() as conn:
        duplicate_of = conn.execute(text("SELECT duplicate_of FROM activities WHERE id = :i"), {"i": mirror}).scalar()
    assert duplicate_of == original


def test_daily_metric_upsert_overwrites_the_same_day(user_id):
    db.upsert_daily_metric(user_id, CanonicalDailyMetric(date(2026, 9, 4), "coros", resting_hr=57))
    db.upsert_daily_metric(user_id, CanonicalDailyMetric(date(2026, 9, 4), "coros", resting_hr=59))
    with db.engine.connect() as conn:
        rows = conn.execute(text("SELECT resting_hr FROM daily_metrics WHERE user_id = :u"), {"u": user_id}).fetchall()
    assert [r[0] for r in rows] == [59]


def test_delete_provider_data_removes_activities_and_metrics(user_id):
    db.upsert_activity(user_id, _activity())
    db.upsert_daily_metric(user_id, CanonicalDailyMetric(date(2026, 9, 4), "coros", resting_hr=57))
    db.delete_provider_data(user_id, "coros")
    with db.engine.connect() as conn:
        activities = conn.execute(text("SELECT count(*) FROM activities WHERE user_id = :u"), {"u": user_id}).scalar()
        metrics = conn.execute(text("SELECT count(*) FROM daily_metrics WHERE user_id = :u"), {"u": user_id}).scalar()
    assert (activities, metrics) == (0, 0)
