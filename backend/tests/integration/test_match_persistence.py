"""Persistence tests for match state. Needs a live Postgres."""

from datetime import UTC, datetime

import pytest
from sqlalchemy import text

import db
from services.providers.base import CanonicalActivity


@pytest.fixture()
def user_id():
    with db.engine.connect() as conn:
        row = conn.execute(
            text("INSERT INTO users (email, name, provider) VALUES (:e,'M','email') RETURNING id"),
            {"e": f"match-{datetime.now().timestamp()}@t.local"},
        ).fetchone()
        conn.commit()
    return row[0]


@pytest.fixture()
def activity_id(user_id):
    return db.upsert_activity(
        user_id,
        CanonicalActivity(
            external_id="m1",
            provider="coros",
            activity_type="outdoor_run",
            start_time=datetime(2026, 9, 2, 6, 0, tzinfo=UTC),
            duration_seconds=3600.0,
            distance_km=10.0,
        ),
    )


def test_save_match_records_state(activity_id):
    db.save_match(
        activity_id=activity_id,
        workout_id=None,
        confidence=0.91,
        method="auto",
        details={"reasons": ["duration 60 min vs 60 planned"]},
    )
    with db.engine.connect() as conn:
        row = conn.execute(
            text("SELECT match_confidence, match_method FROM activities WHERE id = :i"),
            {"i": activity_id},
        ).fetchone()
    assert row[0] == pytest.approx(0.91) and row[1] == "auto"


def test_manual_match_overwrites_an_automatic_one(activity_id):
    db.save_match(activity_id=activity_id, workout_id=None, confidence=0.6, method="auto", details={})
    db.set_manual_match(activity_id=activity_id, workout_id=None)
    with db.engine.connect() as conn:
        method = conn.execute(text("SELECT match_method FROM activities WHERE id = :i"), {"i": activity_id}).scalar()
    assert method == "manual"


def test_save_match_never_overwrites_a_manual_match(activity_id):
    """The second non-negotiable rule, proven against real Postgres: once an
    athlete has corrected a match by hand, an automatic run's save_match must
    be a no-op for that activity -- not merely "usually not called" (the
    runner-level unit tests already prove that), but actually rejected by the
    UPDATE's own WHERE clause even if something did call it."""
    db.set_manual_match(activity_id=activity_id, workout_id=None)
    db.save_match(activity_id=activity_id, workout_id=999, confidence=0.99, method="auto", details={"x": 1})
    with db.engine.connect() as conn:
        row = conn.execute(
            text("SELECT match_method, matched_workout_id, match_confidence FROM activities WHERE id = :i"),
            {"i": activity_id},
        ).fetchone()
    assert row[0] == "manual"
    assert row[1] is None
    assert row[2] is None


def test_clear_match_resets_all_match_columns(activity_id):
    db.save_match(activity_id=activity_id, workout_id=None, confidence=0.7, method="auto", details={"a": 1})
    db.clear_match(activity_id=activity_id)
    with db.engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT matched_workout_id, match_confidence, match_method, match_details "
                "FROM activities WHERE id = :i"
            ),
            {"i": activity_id},
        ).fetchone()
    assert row == (None, None, None, None)


def test_activity_belongs_to_user(user_id, activity_id):
    assert db.activity_belongs_to_user(activity_id, user_id) is True
    assert db.activity_belongs_to_user(activity_id, user_id + 999999) is False
