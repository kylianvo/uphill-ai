"""fitness_assessments history + weekly run volumes. Scratch DB only."""

from datetime import UTC, date, datetime

from sqlalchemy import text

import db
from db import engine


def _user(email="fs@test.io"):
    with engine.connect() as conn:
        uid = conn.execute(
            text("INSERT INTO users (email, name) VALUES (:e, 'FS') RETURNING id"), {"e": email}
        ).scalar_one()
        conn.commit()
    return uid


def _activity(uid, start, km, vert=0.0, kind="trail_run", ext="x"):
    with engine.connect() as conn:
        conn.execute(
            text("""
            INSERT INTO activities (user_id, source_provider, external_ids, activity_type,
                                    start_time, duration_seconds, distance_km, elevation_gain_m)
            VALUES (:u, 'coros', CAST(:ext AS jsonb), :k, :s, 3600, :km, :v)
        """),
            {"u": uid, "ext": f'{{"coros": "{ext}"}}', "k": kind, "s": start, "km": km, "v": vert},
        )
        conn.commit()


def test_threshold_source_defaults_to_unknown():
    uid = _user()
    assert db.get_user_by_id(uid)["threshold_source"] == "unknown"


def test_assessment_inserted_only_when_values_change():
    uid = _user()
    data = {"vo2max": 63.0, "running_level": 92.0, "threshold_pace": "3:57", "pred_marathon_sec": 10200.0}
    assert db.record_fitness_assessment(uid, "coros", data) is True
    assert db.record_fitness_assessment(uid, "coros", data) is False
    assert db.record_fitness_assessment(uid, "coros", {**data, "vo2max": 63.0000001}) is False
    assert db.record_fitness_assessment(uid, "coros", {**data, "vo2max": 64.0}) is True
    latest = db.get_latest_fitness_assessment(uid)
    assert latest["vo2max"] == 64.0
    assert latest["pred_marathon_sec"] == 10200.0
    assert latest["measured_at"].tzinfo is not None


def test_weekly_run_volumes_groups_by_monday_and_skips_non_runs():
    uid = _user()
    _activity(uid, datetime(2026, 9, 14, 6, tzinfo=UTC), 20.0, 800, ext="a")
    _activity(uid, datetime(2026, 9, 20, 6, tzinfo=UTC), 30.0, 1200, ext="b")
    _activity(uid, datetime(2026, 9, 21, 6, tzinfo=UTC), 10.0, 0, kind="indoor_run", ext="c")
    _activity(uid, datetime(2026, 9, 21, 7, tzinfo=UTC), 5.0, 0, kind="strength", ext="d")
    rows = db.get_weekly_run_volumes(uid, since=date(2026, 9, 1))
    assert rows == [
        {"week_start": date(2026, 9, 14), "km": 50.0, "vert_m": 2000.0},
        {"week_start": date(2026, 9, 21), "km": 10.0, "vert_m": 0.0},
    ]
    assert db.get_first_activity_at(uid, "coros") == datetime(2026, 9, 14, 6, tzinfo=UTC)


def test_plan_fitness_snapshot_round_trips_and_disconnect_clears_assessments():
    uid = _user()
    with engine.connect() as conn:
        pid = conn.execute(
            text("""INSERT INTO plans (user_id, race_name, race_date, goal_type, total_weeks)
                    VALUES (:u, 'R', '2026-12-01', 'race', 10) RETURNING id"""),
            {"u": uid},
        ).scalar_one()
        conn.commit()
    db.set_plan_fitness_snapshot(pid, {"tier": "sub_elite"})
    with engine.connect() as conn:
        stored = conn.execute(text("SELECT fitness_snapshot FROM plans WHERE id=:p"), {"p": pid}).scalar_one()
    assert stored == {"tier": "sub_elite"}

    db.record_fitness_assessment(uid, "coros", {"vo2max": 50.0})
    db.delete_provider_data(uid, "coros")
    assert db.get_latest_fitness_assessment(uid) is None
