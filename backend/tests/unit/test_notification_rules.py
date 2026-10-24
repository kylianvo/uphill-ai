from datetime import UTC, date, datetime, time, timedelta

import pytest

from services.notification_rules import candidates, delivery_window, is_done, local_due


def context():
    return dict(
        user={"id": 1},
        preferences=dict(
            timezone="Australia/Sydney",
            workouts_enabled=True,
            coaching_enabled=True,
            workout_time="07:00",
            coaching_time="18:00",
            quiet_start="21:00",
            quiet_end="07:00",
        ),
        plan=dict(goal_type="finish", id=5, start_date="2026-10-12", race_date="2026-12-20", plan_status="active"),
        workouts=[
            dict(
                id=1,
                week_number=1,
                day_of_week="Friday",
                duration_minutes=45,
                type="Easy",
                title="Easy run",
                target_zone="Z2",
                approved_at="yes",
                is_completed=0,
            )
        ],
        history=[],
        cards=[],
        opens=[],
        requests=[],
        checklist=[],
        connections=[],
    )


def test_manual_incomplete_overrides_match():
    assert not is_done({"is_completed": 0, "matched_activity_id": 7})
    assert is_done({"is_completed": None, "matched_activity_id": 7})


@pytest.mark.parametrize(
    "day,wall,expected",
    [
        (date(2026, 10, 4), time(2, 30), "2026-10-03T16:00:00+00:00"),
        (date(2026, 4, 5), time(2, 30), "2026-04-04T15:30:00+00:00"),
    ],
)
def test_dst(day, wall, expected):
    assert local_due(day, wall, "Australia/Sydney").isoformat() == expected


def test_workout_uses_current_state():
    c = context()
    now = datetime(2026, 10, 15, 20, 0, tzinfo=UTC)
    assert candidates(c, now)[0]["destination"] == {"kind": "workout", "plan_id": 5, "workout_id": 1}
    c["workouts"][0]["is_completed"] = 1
    assert not candidates(c, now)
    c["workouts"][0]["is_completed"] = 0
    c["workouts"][0]["approved_at"] = None
    assert not candidates(c, now)


def test_no_late_replay_or_missing_timezone():
    c = context()
    assert not candidates(c, datetime(2026, 10, 15, 21, 1, tzinfo=UTC))
    c["preferences"]["timezone"] = None
    assert not candidates(c, datetime(2026, 10, 15, 20, 0, tzinfo=UTC))


def test_quiet_hours_do_not_cross_expiry():
    p = context()["preferences"]
    due = datetime(2026, 10, 16, 11, tzinfo=UTC)
    assert delivery_window(due, p, due + timedelta(hours=1)) is None


def test_null_type_and_phase_do_not_crash():
    c = context()
    c["workouts"][0].update(type=None, phase=None)
    assert candidates(c, datetime(2026, 10, 15, 20, 0, tzinfo=UTC))
