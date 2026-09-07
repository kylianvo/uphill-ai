"""Persistence tests for match state. Needs a live Postgres."""

from datetime import UTC, date, datetime

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


def test_manual_match_overwrites_an_automatic_one(user_id, activity_id):
    db.save_match(activity_id=activity_id, workout_id=None, confidence=0.6, method="auto", details={})
    db.set_manual_match(activity_id=activity_id, workout_id=None, user_id=user_id)
    with db.engine.connect() as conn:
        method = conn.execute(text("SELECT match_method FROM activities WHERE id = :i"), {"i": activity_id}).scalar()
    assert method == "manual"


def test_save_match_never_overwrites_a_manual_match(user_id, activity_id):
    """The second non-negotiable rule, proven against real Postgres: once an
    athlete has corrected a match by hand, an automatic run's save_match must
    be a no-op for that activity -- not merely "usually not called" (the
    runner-level unit tests already prove that), but actually rejected by the
    UPDATE's own WHERE clause even if something did call it."""
    db.set_manual_match(activity_id=activity_id, workout_id=None, user_id=user_id)
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


# --- Cross-user IDOR fix: workout_id ownership -----------------------------
#
# db.set_manual_match previously trusted its caller for workout ownership --
# only the FK proved the workout row existed, not who it belonged to. An
# athlete could attach their own activity to another athlete's workout by
# guessing a small integer, and because match_method='manual' is permanent
# (rule 2), no automatic run would ever clear the wrong reference. Fixed with
# two layers: a route-level ownership check (db.workout_belongs_to_user) and
# a second guard baked directly into set_manual_match's own SQL, so the
# invariant holds even for a future caller that forgets the route check --
# the same principle already applied to the manual-match guard in save_match.


def _create_workout_for(owner_user_id: int) -> int:
    plan_id = db.create_plan(
        user_id=owner_user_id,
        race_name="Test Race",
        race_date="2027-05-01",
        goal_type="finish",
        target_time_hours=None,
        total_weeks=8,
    )
    with db.engine.connect() as conn:
        row = conn.execute(
            text("""
                INSERT INTO workouts (plan_id, week_number, day_of_week, phase, title, type,
                    duration_minutes, target_zone)
                VALUES (:pid, 1, 'Monday', 'Base', 'Easy Run', 'run', 45, 'zone2')
                RETURNING id
            """),
            {"pid": plan_id},
        ).fetchone()
        conn.commit()
    return row[0]


@pytest.fixture()
def other_user_id():
    with db.engine.connect() as conn:
        row = conn.execute(
            text("INSERT INTO users (email, name, provider) VALUES (:e,'Other','email') RETURNING id"),
            {"e": f"match-other-{datetime.now().timestamp()}@t.local"},
        ).fetchone()
        conn.commit()
    return row[0]


def test_workout_belongs_to_user(user_id, other_user_id):
    workout_id = _create_workout_for(user_id)
    assert db.workout_belongs_to_user(workout_id, user_id) is True
    assert db.workout_belongs_to_user(workout_id, other_user_id) is False


def test_set_manual_match_is_a_no_op_for_a_workout_owned_by_another_user(user_id, other_user_id, activity_id):
    foreign_workout_id = _create_workout_for(other_user_id)
    db.set_manual_match(activity_id=activity_id, workout_id=foreign_workout_id, user_id=user_id)
    with db.engine.connect() as conn:
        row = conn.execute(
            text("SELECT matched_workout_id, match_method FROM activities WHERE id = :i"),
            {"i": activity_id},
        ).fetchone()
    assert row[0] is None
    assert row[1] is None


def test_set_manual_match_clearing_with_none_still_works(user_id, activity_id):
    """Guards the regression risk in the CAST(:w AS INTEGER) IS NULL branch --
    workout_id=None is the legitimate "clear this match" case and must keep
    working even with the added ownership guard."""
    own_workout_id = _create_workout_for(user_id)
    db.set_manual_match(activity_id=activity_id, workout_id=own_workout_id, user_id=user_id)
    db.set_manual_match(activity_id=activity_id, workout_id=None, user_id=user_id)
    with db.engine.connect() as conn:
        row = conn.execute(
            text("SELECT matched_workout_id, match_method FROM activities WHERE id = :i"),
            {"i": activity_id},
        ).fetchone()
    assert row[0] is None
    assert row[1] == "manual"


def test_set_manual_match_succeeds_for_a_workout_the_same_user_owns(user_id, activity_id):
    own_workout_id = _create_workout_for(user_id)
    db.set_manual_match(activity_id=activity_id, workout_id=own_workout_id, user_id=user_id)
    with db.engine.connect() as conn:
        row = conn.execute(
            text("SELECT matched_workout_id, match_method FROM activities WHERE id = :i"),
            {"i": activity_id},
        ).fetchone()
    assert row[0] == own_workout_id
    assert row[1] == "manual"


def test_matching_override_route_rejects_a_foreign_workout_id(client, auth_headers):
    """End-to-end proof through the actual PATCH route: a caller cannot
    attach their own activity to another athlete's workout, and the failure
    looks identical (same status, same detail) to a plain 'activity not
    found' -- a different message would leak that the workout exists."""
    with db.engine.connect() as conn:
        row = conn.execute(
            text("INSERT INTO users (email, name, provider) VALUES (:e,'Victim','email') RETURNING id"),
            {"e": f"victim-{datetime.now().timestamp()}@t.local"},
        ).fetchone()
        conn.commit()
    victim_id = row[0]
    foreign_workout_id = _create_workout_for(victim_id)

    caller_id = auth_headers["user_id"]
    my_activity_id = db.upsert_activity(
        caller_id,
        CanonicalActivity(
            external_id="route-idor-1",
            provider="coros",
            activity_type="outdoor_run",
            start_time=datetime(2026, 9, 3, 6, 0, tzinfo=UTC),
            duration_seconds=3600.0,
            distance_km=10.0,
        ),
    )

    resp = client.patch(
        f"/api/integrations/matching/{my_activity_id}",
        params={"workout_id": foreign_workout_id},
        headers=auth_headers["headers"],
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Activity not found."

    with db.engine.connect() as conn:
        matched = conn.execute(
            text("SELECT matched_workout_id, match_method FROM activities WHERE id = :i"),
            {"i": my_activity_id},
        ).fetchone()
    assert matched[0] is None
    assert matched[1] is None


# --- GET /api/integrations/matching -----------------------------------------
#
# Previously only POST (run a match) and PATCH (correct one) existed -- there
# was no way to list what the matcher decided, so the review UI had nothing
# to render. This lists the caller's activities in a date window with their
# current match state, LEFT JOINed to workouts so an unmatched activity still
# appears (with workout_id/workout_title both None). Every value is raw
# (numbers, an ISO datetime), never a pre-formatted string -- formatting
# (including Vietnamese locale conventions) happens in the frontend, where
# `lang` is known.


def test_get_matches_for_review_returns_only_the_callers_activities(user_id, activity_id, other_user_id):
    db.upsert_activity(
        other_user_id,
        CanonicalActivity(
            external_id="other-1",
            provider="coros",
            activity_type="outdoor_run",
            start_time=datetime(2026, 9, 2, 7, 0, tzinfo=UTC),
            duration_seconds=1800.0,
            distance_km=5.0,
        ),
    )
    rows = db.get_matches_for_review(user_id, date(2026, 9, 1), date(2026, 9, 5))
    assert [r["activity_id"] for r in rows] == [activity_id]


def test_get_matches_for_review_left_joins_so_an_unmatched_activity_still_appears(user_id, activity_id):
    rows = db.get_matches_for_review(user_id, date(2026, 9, 1), date(2026, 9, 5))
    assert len(rows) == 1
    assert rows[0]["activity_id"] == activity_id
    assert rows[0]["workout_id"] is None
    assert rows[0]["workout_title"] is None


def test_get_matches_for_review_includes_the_matched_workouts_title(user_id, activity_id):
    workout_id = _create_workout_for(user_id)
    db.save_match(activity_id=activity_id, workout_id=workout_id, confidence=0.91, method="auto", details={})
    rows = db.get_matches_for_review(user_id, date(2026, 9, 1), date(2026, 9, 5))
    assert rows[0]["workout_id"] == workout_id
    assert rows[0]["workout_title"] == "Easy Run"


def test_get_matches_for_review_returns_raw_not_formatted_values(user_id):
    activity_id = db.upsert_activity(
        user_id,
        CanonicalActivity(
            external_id="raw-1",
            provider="coros",
            activity_type="outdoor_run",
            start_time=datetime(2026, 9, 2, 6, 0, tzinfo=UTC),
            duration_seconds=2530.0,
            distance_km=8.2,
            elevation_gain_m=145.0,
            avg_hr=151,
            device_model="COROS APEX 2 Pro",
        ),
    )
    rows = db.get_matches_for_review(user_id, date(2026, 9, 1), date(2026, 9, 5))
    row = next(r for r in rows if r["activity_id"] == activity_id)
    assert row["distance_km"] == pytest.approx(8.2)
    assert row["duration_seconds"] == pytest.approx(2530.0)
    assert row["avg_hr"] == 151
    assert row["elevation_gain_m"] == pytest.approx(145.0)
    assert row["device_model"] == "COROS APEX 2 Pro"
    assert row["source_provider"] == "coros"
    assert row["start_time"] is not None


def test_get_matches_for_review_respects_the_date_window(user_id):
    db.upsert_activity(
        user_id,
        CanonicalActivity(
            external_id="outside-window",
            provider="coros",
            activity_type="outdoor_run",
            start_time=datetime(2026, 8, 1, 6, 0, tzinfo=UTC),
            duration_seconds=1800.0,
            distance_km=5.0,
        ),
    )
    rows = db.get_matches_for_review(user_id, date(2026, 9, 1), date(2026, 9, 5))
    assert rows == []


def test_matching_get_route_returns_only_the_callers_activities(client, auth_headers, other_user_id):
    caller_id = auth_headers["user_id"]
    my_activity_id = db.upsert_activity(
        caller_id,
        CanonicalActivity(
            external_id="route-get-1",
            provider="coros",
            activity_type="outdoor_run",
            start_time=datetime.now(UTC),
            duration_seconds=1800.0,
            distance_km=5.0,
        ),
    )
    db.upsert_activity(
        other_user_id,
        CanonicalActivity(
            external_id="route-get-other",
            provider="coros",
            activity_type="outdoor_run",
            start_time=datetime.now(UTC),
            duration_seconds=1800.0,
            distance_km=5.0,
        ),
    )
    resp = client.get("/api/integrations/matching", params={"days": 30}, headers=auth_headers["headers"])
    assert resp.status_code == 200
    body = resp.json()
    activity_ids = [a["activity_id"] for a in body["activities"]]
    assert activity_ids == [my_activity_id]


def test_matching_get_route_left_join_includes_unmatched_activity(client, auth_headers):
    caller_id = auth_headers["user_id"]
    db.upsert_activity(
        caller_id,
        CanonicalActivity(
            external_id="route-get-unmatched",
            provider="coros",
            activity_type="outdoor_run",
            start_time=datetime.now(UTC),
            duration_seconds=1800.0,
            distance_km=5.0,
        ),
    )
    resp = client.get("/api/integrations/matching", params={"days": 30}, headers=auth_headers["headers"])
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["activities"]) == 1
    assert body["activities"][0]["workout_id"] is None
    assert body["activities"][0]["workout_title"] is None


@pytest.mark.parametrize("days", [0, 366, -1])
def test_matching_get_route_rejects_days_out_of_bounds(client, auth_headers, days):
    resp = client.get("/api/integrations/matching", params={"days": days}, headers=auth_headers["headers"])
    assert resp.status_code == 400
    assert resp.json()["detail"] == "days must be between 1 and 365."
