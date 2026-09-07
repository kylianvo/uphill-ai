"""Unit tests for the matching runner -- db is monkeypatched, no DB or network."""

from datetime import UTC, date, datetime, timedelta

import pytest

from services.matching import runner

BASE = datetime(2026, 9, 2, 6, 0, tzinfo=UTC)


def activity(id_, offset_s=0, duration_s=3600.0, km=10.0, method=None):
    return {
        "id": id_,
        "start_time": BASE + timedelta(seconds=offset_s),
        "duration_seconds": duration_s,
        "distance_km": km,
        "elevation_gain_m": 100.0,
        "avg_hr": 150,
        "activity_type": "outdoor_run",
        "match_method": method,
    }


def workout(id_, day="2026-09-02"):
    return {
        "id": id_,
        "type": "EASY",
        "duration_minutes": 60.0,
        "distance_km": 10.0,
        "elevation_gain_m": 100.0,
        "target_hr_range": "140-155",
        "target_pace": None,
        "interval_reps": None,
        "workout_date": date.fromisoformat(day),
    }


@pytest.mark.asyncio
async def test_writes_match_state_for_a_confident_pair(monkeypatch):
    saved = []
    monkeypatch.setattr(runner.db, "get_activities_for_matching", lambda *a, **k: [activity(1)])
    monkeypatch.setattr(runner.db, "get_dated_workouts_for_matching", lambda *a, **k: [workout(10)])
    monkeypatch.setattr(runner.db, "save_match", lambda **kw: saved.append(kw))
    monkeypatch.setattr(runner.settings, "MATCHING_SHADOW_MODE", True)

    result = await runner.match_user(7, date(2026, 9, 1), date(2026, 9, 3))
    assert result["matched"] == 1
    assert saved[0]["workout_id"] == 10
    assert saved[0]["method"] == "auto"


@pytest.mark.asyncio
async def test_bundle_attributes_workout_id_to_primary_fragment_only(monkeypatch):
    # In a multi-activity bundle (e.g. 2.5 min warm-up + 60 min main run),
    # UNIQUE(matched_workout_id) constraint in PostgreSQL dictates only the primary
    # activity receives workout_id, while the secondary fragment gets workout_id=None.
    saved = []
    frag1 = activity(1, offset_s=0, duration_s=150.0, km=0.5)
    frag2 = activity(2, offset_s=300, duration_s=3600.0, km=9.5)
    monkeypatch.setattr(runner.db, "get_activities_for_matching", lambda *a, **k: [frag1, frag2])
    monkeypatch.setattr(runner.db, "get_dated_workouts_for_matching", lambda *a, **k: [workout(10)])
    monkeypatch.setattr(runner.db, "save_match", lambda **kw: saved.append(kw))
    monkeypatch.setattr(runner.settings, "MATCHING_SHADOW_MODE", True)

    result = await runner.match_user(7, date(2026, 9, 1), date(2026, 9, 3))
    assert result["matched"] == 1
    assert len(saved) == 2

    saved_by_id = {s["activity_id"]: s for s in saved}
    assert saved_by_id[2]["workout_id"] == 10
    assert saved_by_id[2]["method"] == "auto"

    assert saved_by_id[1]["workout_id"] is None
    assert saved_by_id[1]["details"]["bundle_primary_activity_id"] == 2


@pytest.mark.asyncio
async def test_shadow_mode_never_marks_a_workout_complete(monkeypatch):
    completed = []
    monkeypatch.setattr(runner.db, "get_activities_for_matching", lambda *a, **k: [activity(1)])
    monkeypatch.setattr(runner.db, "get_dated_workouts_for_matching", lambda *a, **k: [workout(10)])
    monkeypatch.setattr(runner.db, "save_match", lambda **kw: None)
    monkeypatch.setattr(runner.db, "update_workout_log", lambda *a, **k: completed.append(a))
    monkeypatch.setattr(runner.settings, "MATCHING_SHADOW_MODE", True)

    await runner.match_user(7, date(2026, 9, 1), date(2026, 9, 3))
    assert completed == []


@pytest.mark.asyncio
async def test_live_mode_marks_only_auto_band_matches_complete(monkeypatch):
    completed = []
    monkeypatch.setattr(runner.db, "get_activities_for_matching", lambda *a, **k: [activity(1)])
    monkeypatch.setattr(runner.db, "get_dated_workouts_for_matching", lambda *a, **k: [workout(10)])
    monkeypatch.setattr(runner.db, "save_match", lambda **kw: None)
    monkeypatch.setattr(runner.db, "update_workout_log", lambda workout_id, **kw: completed.append(workout_id))
    monkeypatch.setattr(runner.settings, "MATCHING_SHADOW_MODE", False)

    await runner.match_user(7, date(2026, 9, 1), date(2026, 9, 3))
    assert completed == [10]


@pytest.mark.asyncio
async def test_a_manual_match_is_never_touched_by_an_automatic_run(monkeypatch):
    saved = []
    monkeypatch.setattr(runner.db, "get_activities_for_matching", lambda *a, **k: [activity(1, method="manual")])
    monkeypatch.setattr(runner.db, "get_dated_workouts_for_matching", lambda *a, **k: [workout(10)])
    monkeypatch.setattr(runner.db, "save_match", lambda **kw: saved.append(kw))
    monkeypatch.setattr(runner.settings, "MATCHING_SHADOW_MODE", True)

    result = await runner.match_user(7, date(2026, 9, 1), date(2026, 9, 3))
    assert saved == []
    assert result["skipped_manual"] == 1


@pytest.mark.asyncio
async def test_activities_with_no_workouts_that_day_are_reported_not_dropped(monkeypatch):
    monkeypatch.setattr(runner.db, "get_activities_for_matching", lambda *a, **k: [activity(1)])
    monkeypatch.setattr(runner.db, "get_dated_workouts_for_matching", lambda *a, **k: [])
    monkeypatch.setattr(runner.db, "save_match", lambda **kw: None)
    monkeypatch.setattr(runner.settings, "MATCHING_SHADOW_MODE", True)

    result = await runner.match_user(7, date(2026, 9, 1), date(2026, 9, 3))
    assert result["unmatched"] == 1


# --- Malformed-plan handling ---------------------------------------------
#
# workout_calendar.plan_start_monday computes total_weeks from week_number
# lazily -- via a generator inside max() -- only on the legacy fallback path
# (no plans.start_date, no explicit race workout). That branch is essentially
# never exercised by the existing ICS export (current plans always carry
# start_date), so a corrupted week_number sitting in an old legacy plan has
# never had a chance to raise before. The matching runner calls
# plan_start_monday/workout_date directly, for every plan an athlete has ever
# had, so it is the first caller that can actually hit that data.
#
# Decision: a malformed schedule must not take down the whole run for an
# athlete who has one bad legacy plan among several healthy ones. The runner
# catches ValueError/TypeError/KeyError around each plan's start-Monday
# anchor computation (skipping that whole plan's workouts -- there is no
# valid anchor to place any of them against) and, separately, around each
# individual workout's date offset (skipping just that one row). Activities
# on the affected days still come through as "unmatched" (reported, not
# dropped) rather than raising out of match_user.


def _malformed_legacy_workout(id_, week_number="not-a-number"):
    # No "start_date" and no RACE-typed workout -> plan_start_monday falls
    # back to the lazy total_weeks computation, which calls int(week_number).
    return {
        "id": id_,
        "type": "EASY",
        "duration_minutes": 60.0,
        "distance_km": 10.0,
        "elevation_gain_m": 100.0,
        "target_hr_range": "140-155",
        "target_pace": None,
        "interval_reps": None,
        "week_number": week_number,
        "day_of_week": "Wednesday",
        "is_completed": 0,
        "start_date": None,
        "race_date": "2026-12-01",
    }


def _healthy_workout(id_, week_number, day_of_week, start_date, race_date="2026-12-01"):
    return {
        "id": id_,
        "type": "EASY",
        "duration_minutes": 60.0,
        "distance_km": 10.0,
        "elevation_gain_m": 100.0,
        "target_hr_range": "140-155",
        "target_pace": None,
        "interval_reps": None,
        "week_number": week_number,
        "day_of_week": day_of_week,
        "is_completed": 0,
        "start_date": start_date,
        "race_date": race_date,
    }


def test_workouts_by_date_skips_a_plan_whose_week_number_is_unparseable():
    workouts = [_malformed_legacy_workout(99)]
    by_date = runner._workouts_by_date(workouts)
    assert by_date == {}


def test_workouts_by_date_keeps_healthy_plans_when_a_sibling_plan_is_malformed():
    healthy = _healthy_workout(1, week_number=1, day_of_week="Wednesday", start_date="2026-09-01")
    malformed = _malformed_legacy_workout(99)
    by_date = runner._workouts_by_date([healthy, malformed])
    assert date(2026, 9, 2) in by_date
    assert by_date[date(2026, 9, 2)][0]["id"] == 1


@pytest.mark.asyncio
async def test_match_user_does_not_crash_on_a_malformed_plan_and_reports_unmatched(monkeypatch):
    monkeypatch.setattr(runner.db, "get_activities_for_matching", lambda *a, **k: [activity(1)])
    monkeypatch.setattr(runner.db, "get_dated_workouts_for_matching", lambda *a, **k: [_malformed_legacy_workout(99)])
    monkeypatch.setattr(runner.db, "save_match", lambda **kw: None)
    monkeypatch.setattr(runner.settings, "MATCHING_SHADOW_MODE", True)

    result = await runner.match_user(7, date(2026, 9, 1), date(2026, 9, 3))
    assert result["unmatched"] == 1


@pytest.mark.asyncio
async def test_match_user_scopes_workouts_by_plan_id(monkeypatch):
    calls = []

    def fake_get_workouts(user_id, plan_id=None):
        calls.append({"user_id": user_id, "plan_id": plan_id})
        return [workout(10)]

    monkeypatch.setattr(runner.db, "get_activities_for_matching", lambda *a, **k: [activity(1)])
    monkeypatch.setattr(runner.db, "get_dated_workouts_for_matching", fake_get_workouts)
    monkeypatch.setattr(runner.db, "save_match", lambda **kw: None)
    monkeypatch.setattr(runner.settings, "MATCHING_SHADOW_MODE", True)

    await runner.match_user(7, date(2026, 9, 1), date(2026, 9, 3), plan_id=42)
    assert len(calls) == 1
    assert calls[0]["plan_id"] == 42
