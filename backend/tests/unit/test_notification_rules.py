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


# --- v2 timing -----------------------------------------------------------------------------------
from services.notification_rules import slot_time, usual_start  # noqa: E402

SYD = "Australia/Sydney"


def runs(*local_times, day=date(2026, 10, 13)):
    """Activities on consecutive weekdays (Tue 13 Oct onward, AEDT = UTC+11) at the given local times."""
    out = []
    for i, hhmm in enumerate(local_times):
        h, m = map(int, hhmm.split(":"))
        start = datetime.combine(day + timedelta(days=i), time(h, m)) - timedelta(hours=11)
        out.append(
            dict(
                id=i,
                start_time=start.replace(tzinfo=UTC),
                duration_seconds=3600,
                distance_km=10,
                elevation_gain_m=0,
                matched_workout_id=None,
            )
        )
    return out


def test_usual_start_needs_four_and_splits_weekend():
    weekdays = runs("06:00", "06:10", "06:20", "18:00")  # Tue-Fri
    assert usual_start(weekdays, SYD, weekend=False, now=datetime(2026, 10, 20, tzinfo=UTC)) == time(6, 15)
    weekend = runs("07:00", "07:00", day=date(2026, 10, 17))  # Sat, Sun
    assert usual_start(weekend, SYD, weekend=True, now=datetime(2026, 10, 20, tzinfo=UTC)) is None


def test_usual_start_ignores_activities_older_than_28_days():
    old = runs("06:00", "06:00", "06:00", "06:00", day=date(2026, 8, 4))
    assert usual_start(old, SYD, weekend=False, now=datetime(2026, 10, 20, tzinfo=UTC)) is None


def test_workout_slot_is_75_min_before_usual_start():
    c = context()
    c["activities"] = runs("08:00", "08:00", "08:00", "08:00")
    assert slot_time(c, "workout", date(2026, 10, 16)) == time(6, 45)


def test_workout_slot_falls_back_to_0700_without_history():
    c = context()
    c["activities"] = []
    assert slot_time(c, "workout", date(2026, 10, 16)) == time(7, 0)
    assert candidates(c, datetime(2026, 10, 15, 20, 0, tzinfo=UTC))[0]["kind"] == "workout"


def test_early_runner_clamps_then_quiet_hours_push_to_0700():
    c = context()
    c["activities"] = runs("05:30", "05:30", "05:30", "05:30")
    assert slot_time(c, "workout", date(2026, 10, 16)) == time(6, 0)
    due = candidates(c, datetime(2026, 10, 15, 20, 0, tzinfo=UTC))[0]["due_at"]
    assert due == datetime(2026, 10, 15, 20, 0, tzinfo=UTC)  # 07:00 Sydney


def test_week_brief_slot_is_0730_and_coaching_is_1800():
    c = context()
    assert slot_time(c, "week_brief", date(2026, 10, 19)) == time(7, 30)
    for kind in ("planning", "unlogged", "checklist", "knowledge", "taper", "race"):
        assert slot_time(c, kind, date(2026, 10, 19)) == time(18, 0)


def test_stored_quiet_hours_are_ignored():
    p = {**context()["preferences"], "quiet_start": "23:00", "quiet_end": "05:00"}
    due = datetime(2026, 10, 16, 11, tzinfo=UTC)  # 22:00 Sydney
    window = delivery_window(due, p, due + timedelta(days=1))
    assert window[0] == datetime(2026, 10, 16, 20, tzinfo=UTC)  # 07:00 next day


# --- v2 budget -----------------------------------------------------------------------------------
from services.notification_rules import backed_off  # noqa: E402

NOW = datetime(2026, 10, 15, 20, 0, tzinfo=UTC)  # Fri 07:00 Sydney, workout day


def sent(kind, days_ago, opened=False):
    at = NOW - timedelta(days=days_ago)
    return dict(id=f"{kind}{days_ago}", kind=kind, status="accepted", claimed_at=at, opened_at=at if opened else None)


def test_muted_kind_is_never_a_candidate():
    c = context()
    c["preferences"]["muted_kinds"] = ["workout"]  # not mutable via API, but the filter itself is kind-agnostic
    assert not candidates(c, NOW)


def test_three_unopened_week_briefs_back_off_for_14_days():
    history = [sent("week_brief", d) for d in (21, 14, 7)]
    assert backed_off(history, "week_brief", NOW)
    assert not backed_off(history, "week_brief", NOW + timedelta(days=8))  # 15 days after the last


def test_unopened_workout_reminders_never_back_off():
    assert not backed_off([sent("workout", d) for d in (3, 2, 1)], "workout", NOW)


def test_one_opened_in_the_last_three_resets_back_off():
    history = [sent("knowledge", 9), sent("knowledge", 6, opened=True), sent("knowledge", 3)]
    assert not backed_off(history, "knowledge", NOW)


def test_rules_with_no_activities_and_no_history():
    c = context()
    c["activities"], c["history"] = [], []
    assert [x["kind"] for x in candidates(c, NOW)] == ["workout"]
