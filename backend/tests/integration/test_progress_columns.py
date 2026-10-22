"""Progress-tab columns on daily_metrics and activities, on a live Postgres."""

from datetime import UTC, date, datetime, time, timedelta

import pytest
from sqlalchemy import text

import db
from services.providers.base import CanonicalActivity, CanonicalDailyMetric


@pytest.fixture()
def user_id():
    with db.engine.connect() as conn:
        uid = conn.execute(
            text("INSERT INTO users (email, name, provider) VALUES (:e,:n,'email') RETURNING id"),
            {"e": f"progress-{datetime.now().timestamp()}@test.local", "n": "Progress Test"},
        ).scalar()
        conn.commit()
    return uid


def test_daily_metric_round_trips_sleep_window_and_hrv_range(user_id):
    day = date(2026, 10, 22)
    db.upsert_daily_metric(
        user_id,
        CanonicalDailyMetric(
            day,
            "coros",
            sleep_minutes=418,
            sleep_start=time(0, 48),
            sleep_end=time(7, 51),
            hrv_ms=60.0,
            hrv_range_low=51.0,
            hrv_range_high=75.0,
        ),
    )
    # A later partial row (resting HR only) must not wipe the sleep window or range.
    db.upsert_daily_metric(user_id, CanonicalDailyMetric(day, "coros", resting_hr=51))
    with db.engine.connect() as conn:
        row = (
            conn.execute(
                text("SELECT * FROM daily_metrics WHERE user_id = :u AND metric_date = :d"), {"u": user_id, "d": day}
            )
            .mappings()
            .one()
        )
    assert (row["sleep_start"], row["sleep_end"]) == (time(0, 48), time(7, 51))
    assert (row["hrv_range_low"], row["hrv_range_high"]) == (51.0, 75.0)
    assert row["resting_hr"] == 51


def _activity(ext, minutes, start):
    return CanonicalActivity(
        external_id=ext, provider="coros", activity_type="trail_run", start_time=start, duration_seconds=minutes * 60
    )


def test_drift_helpers_select_unchecked_long_runs_and_mark_them(user_id):
    now = datetime.now(UTC)
    long_id = db.upsert_activity(user_id, _activity("long", 150, now - timedelta(days=3)))
    db.upsert_activity(user_id, _activity("short", 45, now - timedelta(days=2)))
    db.upsert_activity(user_id, _activity("old", 150, now - timedelta(days=120)))

    rows = db.get_activities_needing_drift(user_id, "coros", now - timedelta(days=90))
    assert [r["external_id"] for r in rows] == ["long"]
    assert {"id", "external_id", "activity_type", "workout_type"} <= set(rows[0])

    db.set_activity_hr_drift(long_id, 1.6)
    assert db.get_activities_needing_drift(user_id, "coros", now - timedelta(days=90)) == []
    pace_rows = db.get_activities_for_pace(user_id, now - timedelta(days=10), now)
    assert [r["hr_drift_pct"] for r in pace_rows if r["duration_seconds"] == 9000] == [1.6]


def test_build_health_against_real_rows(user_id):
    from services import progress_cards

    today = date.today()
    for i in range(10):
        db.upsert_daily_metric(
            user_id, CanonicalDailyMetric(today - timedelta(days=i), "coros", resting_hr=52, sleep_minutes=420)
        )
    body = progress_cards.build({"id": user_id}, "health", today=today)
    assert [c["key"] for c in body["cards"]] == ["coach_read", "sleep", "resting_hr"]
    assert body["cards"][1]["source"] == "coros" and body["connected"] is False
