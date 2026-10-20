import datetime as dt
from copy import deepcopy

import pytest
from pydantic import ValidationError

import main
from services import week_rebuild
from services.coros_workouts import TARGET_DISTANCE, TARGET_TIME, build_course, validate_course

ATHLETE = {
    "threshold_pace": "3:55",
    "aet_hr": 134,
    "ant_hr": 163,
    "max_hr": 185,
    "resting_hr": 60,
    "zone2_pace_min": "6:30",
    "zone2_pace_max": "5:45",
}
PLAN = {"id": 1, "user_id": 7, "total_weeks": 12, "start_date": "2026-10-12"}
TODAY = dt.date(2026, 10, 12)


def workout(**fields):
    return {
        "id": 11,
        "plan_id": 1,
        "week_number": 1,
        "day_of_week": "Saturday",
        "phase": "Build",
        "type": "Long Run",
        "title": "Long Run",
        "duration_minutes": 130,
        "distance_km": 20,
        "elevation_gain_m": 850,
        "target_zone": "Zone 2",
        "source": "ai_generated",
        **fields,
    }


def test_coach_km_and_climb_derive_time_and_keep_exact_values(monkeypatch):
    row = workout()
    monkeypatch.setattr(main, "get_plan_by_id", lambda pid: PLAN)
    monkeypatch.setattr(main, "get_workout_by_id", lambda wid: row)
    monkeypatch.setattr(main, "get_user_by_id", lambda uid: ATHLETE)
    monkeypatch.setattr(
        main, "coach_update_workout", lambda wid, uid, fields: {**row, **fields, "source": "coach_edited"}
    )
    request = main.CoachWorkoutUpdateRequest(distance_km=26, elevation_gain_m=1500, duration_minutes=30)
    updated = main.edit_athlete_workout(7, 1, 11, request, {"id": 8})
    assert updated["distance_km"] == 26 and updated["elevation_gain_m"] == 1500
    assert abs(updated["duration_minutes"] - 210) < 5
    assert updated["target_pace"] == "8:18 - 7:37 /km"
    assert updated["source"] == "coach_edited"


@pytest.mark.parametrize("source", ["coach_edited", "coach_created"])
def test_applied_rebuild_keeps_coach_session(monkeypatch, source):
    coach = workout(source=source, distance_km=26, elevation_gain_m=1500, duration_minutes=206.8)
    rows = [coach, workout(id=12, day_of_week="Tuesday")]
    original = deepcopy(coach)
    rng = week_rebuild.rebuild_range(PLAN, rows, 1, TODAY)
    assert rng.kept_ids == (11,)
    proposal = {
        "plan_id": 1,
        "operations": {"week": 1, "from_day": rng.from_day, "replaceable_ids": [12]},
        "fingerprints": week_rebuild.week_fingerprints(rows, 1),
        "draft": {"workouts": [workout(id=13, day_of_week="Tuesday")]},
    }
    monkeypatch.setattr(week_rebuild.calendar_ops, "check_agent_access", lambda uid, pid: PLAN)
    monkeypatch.setattr(week_rebuild.db, "get_plan_workouts_for_placement", lambda *args, **kw: rows)

    def replace(conn, pid, ids, draft):
        rows[:] = [w for w in rows if w["id"] not in ids] + draft

    monkeypatch.setattr(week_rebuild.db, "replace_week_workouts", replace)
    week_rebuild.apply_rebuild(7, proposal, TODAY, object())
    assert next(w for w in rows if w["id"] == 11) == original


@pytest.mark.parametrize(
    "source, target",
    [("coach_edited", TARGET_DISTANCE), ("coach_created", TARGET_DISTANCE), ("ai_generated", TARGET_TIME)],
)
def test_coros_coach_trail_uses_distance_generated_keeps_time(source, target):
    course = build_course(workout(source=source, distance_km=26, elevation_gain_m=1500, duration_minutes=206.8), "en")
    assert course["sections"][0]["targetType"] == target
    if target == TARGET_DISTANCE:
        assert len(course["sections"]) == 1
        assert course["sections"][0]["targetValue"] == 26000
    assert validate_course(course) == []


def test_adapt_request_accepts_mountain_preferences_in_shared_rebuild():
    request = main.AdaptWeekRequest(plan_id=1, week_number=1, training_mountain="nui_dinh", mountain_min_minutes=210)
    shared = week_rebuild.RebuildRequest(
        **request.model_dump(exclude={"plan_id", "max_continuous_jog_min", "client_today"})
    )
    assert shared.training_mountain == "nui_dinh" and shared.mountain_min_minutes == 210


def test_coach_negative_climb_rejected():
    with pytest.raises(ValidationError, match="elevation_gain_m"):
        main.CoachWorkoutUpdateRequest(distance_km=26, elevation_gain_m=-1)


def test_normal_coach_editor_preserves_trail_metrics_for_title_edit(monkeypatch):
    row = workout(distance_km=16.1, elevation_gain_m=966, mountain_climb_rate=60, target_pace="8:26 - 7:44 /km")
    monkeypatch.setattr(main, "get_plan_by_id", lambda pid: PLAN)
    monkeypatch.setattr(main, "get_workout_by_id", lambda wid: row)
    monkeypatch.setattr(main, "get_user_by_id", lambda uid: ATHLETE)
    monkeypatch.setattr(main, "coach_update_workout", lambda wid, uid, fields: {**row, **fields})
    request = main.CoachWorkoutUpdateRequest(
        title="Renamed trail run", type="Long Run", duration_minutes=130, target_zone="Zone 2"
    )
    updated = main.edit_athlete_workout(7, 1, 11, request, {"id": 8})
    for key in ["duration_minutes", "distance_km", "elevation_gain_m", "target_pace"]:
        assert updated[key] == row[key]


@pytest.mark.parametrize("rate", [60, None])
def test_normal_coach_edit_recalculates_trail_from_duration_and_zone(monkeypatch, rate):
    from services.plan_generator import PlanGenerator
    from services.trail_pace import trail_session

    row = workout(distance_km=16.1, elevation_gain_m=966, mountain_climb_rate=rate)
    monkeypatch.setattr(main, "get_plan_by_id", lambda pid: PLAN)
    monkeypatch.setattr(main, "get_workout_by_id", lambda wid: row)
    monkeypatch.setattr(main, "get_user_by_id", lambda uid: ATHLETE)
    monkeypatch.setattr(main, "coach_update_workout", lambda wid, uid, fields: {**row, **fields})
    request = main.CoachWorkoutUpdateRequest(duration_minutes=180, target_zone="Zone 1", distance_km=16.1)
    updated = main.edit_athlete_workout(7, 1, 11, request, {"id": 8})
    zones = PlanGenerator.resolve_pace_zones(ATHLETE, None)
    flat, _ = PlanGenerator.pace_and_distance_for_zone("Zone 1", 1, zones)
    pace, km, gain = trail_session(flat, 180, 60)
    assert updated["duration_minutes"] == 180
    assert (updated["target_pace"], updated["distance_km"], updated["elevation_gain_m"]) == (pace, km, gain)
    assert updated["mountain_climb_rate"] == pytest.approx(60)


def test_coach_edit_on_climbing_row_without_distance_does_not_crash(monkeypatch):
    # A row with D+ but no distance (and no stored climb rate) used to divide by zero.
    row = workout(distance_km=0, mountain_climb_rate=None)
    monkeypatch.setattr(main, "get_plan_by_id", lambda pid: PLAN)
    monkeypatch.setattr(main, "get_workout_by_id", lambda wid: row)
    monkeypatch.setattr(main, "get_user_by_id", lambda uid: ATHLETE)
    monkeypatch.setattr(main, "coach_update_workout", lambda wid, uid, fields: {**row, **fields})
    updated = main.edit_athlete_workout(7, 1, 11, main.CoachWorkoutUpdateRequest(duration_minutes=150), {"id": 8})
    assert updated["duration_minutes"] == 150
