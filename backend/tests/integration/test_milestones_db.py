"""plan_milestones persistence. Needs a live scratch Postgres (tests truncate)."""

from datetime import UTC, date, datetime

import pytest
from sqlalchemy import text

import db
from services.providers.base import CanonicalActivity

NOW = datetime(2026, 10, 20, 7, 0, tzinfo=UTC)


@pytest.fixture()
def plan_id():
    with db.engine.connect() as conn:
        uid = conn.execute(
            text("INSERT INTO users (email, name, provider) VALUES (:e,'M','email') RETURNING id"),
            {"e": f"ms-{datetime.now().timestamp()}@test.local"},
        ).scalar()
        conn.commit()
    return db.create_plan(
        uid,
        "First 5K",
        "2026-12-20",
        "start_running",
        None,
        12,
        start_date="2026-10-05",
        milestone_target="5k",
        has_target_event=False,
    )


def test_create_plan_persists_target_and_event_flag(plan_id):
    with db.engine.connect() as conn:
        row = conn.execute(
            text("SELECT milestone_target, has_target_event FROM plans WHERE id=:p"), {"p": plan_id}
        ).fetchone()
    assert (row[0], row[1]) == ("5k", False)


def test_insert_milestone_if_absent_is_idempotent(plan_id):
    assert db.insert_milestone_if_absent(plan_id, "jog_5", "auto", NOW) is True
    assert db.insert_milestone_if_absent(plan_id, "jog_5", "auto", NOW) is False
    assert len(db.get_plan_milestone_rows(plan_id)) == 1


def test_revoke_then_insert_if_absent_keeps_revoked(plan_id):
    db.insert_milestone_if_absent(plan_id, "jog_10", "auto", NOW)
    db.revoke_milestone(plan_id, "jog_10")
    assert db.insert_milestone_if_absent(plan_id, "jog_10", "auto", NOW) is False
    (row,) = db.get_plan_milestone_rows(plan_id)
    assert row["source"] == "revoked" and row["achieved_at"] is None


def test_set_manual_replaces_revoked(plan_id):
    db.revoke_milestone(plan_id, "jog_10")
    db.set_milestone_manual(plan_id, "jog_10")
    (row,) = db.get_plan_milestone_rows(plan_id)
    assert row["source"] == "manual" and row["achieved_at"] is not None


def test_set_plan_milestone_target(plan_id):
    db.set_plan_milestone_target(plan_id, "10k", 22, clear_event=True)
    with db.engine.connect() as conn:
        row = conn.execute(
            text("SELECT milestone_target, total_weeks, has_target_event FROM plans WHERE id=:p"), {"p": plan_id}
        ).fetchone()
    assert tuple(row) == ("10k", 22, False)


def test_get_run_activities_since_filters_type_and_date(plan_id):
    with db.engine.connect() as conn:
        uid = conn.execute(text("SELECT user_id FROM plans WHERE id=:p"), {"p": plan_id}).scalar()

    def act(ext, typ, start):
        return CanonicalActivity(
            external_id=ext,
            provider="coros",
            activity_type=typ,
            start_time=start,
            duration_seconds=1800.0,
            distance_km=5.2,
        )

    db.upsert_activity(uid, act("r1", "outdoor_run", datetime(2026, 10, 10, 6, tzinfo=UTC)))
    db.upsert_activity(uid, act("s1", "strength", datetime(2026, 10, 10, 7, tzinfo=UTC)))
    db.upsert_activity(uid, act("r0", "outdoor_run", datetime(2026, 10, 4, 6, tzinfo=UTC)))
    got = db.get_run_activities_since(uid, date(2026, 10, 5))
    assert [a["distance_km"] for a in got] == [pytest.approx(5.2)] and len(got) == 1


def test_get_completed_run_workouts(plan_id):
    with db.engine.connect() as conn:
        wid = conn.execute(
            text(
                "INSERT INTO workouts (plan_id, week_number, day_of_week, phase, title, type, duration_minutes, target_zone, is_completed) "
                "VALUES (:p,1,'Monday','Base','Easy','Easy Run',20,'Zone 2',1) RETURNING id"
            ),
            {"p": plan_id},
        ).scalar()
        conn.commit()
    (w,) = db.get_completed_run_workouts(plan_id)
    assert w["id"] == wid and w["duration_minutes"] == 20
