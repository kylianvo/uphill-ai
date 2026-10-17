from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import main
from services.plan_generator import PlanGenerator
from services.training_venues import Venues

PROFILE = {"threshold_pace": "3:55", "aet_hr": 134, "ant_hr": 163, "max_hr": 185, "resting_hr": 60}
FLAT = "4:54 - 4:30 /km"


def zones():
    return {**PlanGenerator.resolve_pace_zones(PROFILE, "finish"), "zone1_hr": "107-121 bpm", "zone2_hr": "121-134 bpm"}


def workout():
    return {
        "id": 11,
        "plan_id": 1,
        "day_of_week": "Saturday",
        "type": "Long Run",
        "duration_minutes": 180,
        "target_zone": "Zone 2",
        "distance_km": 22.3,
        "elevation_gain_m": 1338,
        "mountain_mode": "chill",
        "mountain_climb_rate": 60,
        "title": "Long Run",
    }


def test_indoor_treadmill_uses_flat_zone2_once():
    wo = PlanGenerator.apply_mountain_mode(
        workout(), "indoor", Venues(training_mountain="nui_dinh", use_treadmill=True), zones(), FLAT
    )
    assert wo["duration_minutes"] == 120
    assert float(wo["treadmill_incline"]) == 6
    speed = float(wo["treadmill_speed"])
    assert wo["distance_km"] == speed * 2
    assert wo["elevation_gain_m"] == wo["distance_km"] * 6 * 10
    assert speed == main.TrainingRules.calculate_treadmill_settings(4.7, 6)["speed_kph"]


def test_indoor_stairs_has_no_pace():
    wo = PlanGenerator.apply_mountain_mode(workout(), "indoor", Venues(stair_access=True), zones(), FLAT)
    assert wo["duration_minutes"] == 120
    assert "stair" in wo["title"].lower()
    assert not wo["target_pace"]
    assert wo["elevation_gain_m"] == 0


def test_indoor_without_equipment_falls_back_to_skip():
    wo = PlanGenerator.apply_mountain_mode(workout(), "indoor", Venues(), zones(), FLAT)
    assert wo["mountain_mode"] == "skip"
    assert wo["duration_minutes"] == 60
    assert wo["target_pace"] == FLAT


def test_skip_then_mountain_restores_ai_only_climb_rate():
    original = {**workout(), "mountain_climb_rate": 34}
    wo = PlanGenerator.apply_mountain_mode(original, "skip", Venues(), zones(), FLAT)
    assert wo["elevation_gain_m"] == 0
    assert wo["mountain_climb_rate"] == 34
    wo = PlanGenerator.apply_mountain_mode(wo, "mountain", Venues(), zones(), FLAT)
    assert wo["elevation_gain_m"] == round(wo["distance_km"] * 34)


@pytest.fixture
def state(monkeypatch):
    state = {"user": {"id": 7}, "rows": {11: workout(), 12: {"id": 12, "duration_minutes": 40}}}
    plan = {"id": 1, "user_id": 7, "training_mountain": "nui_dinh", "mountain_days": ["Saturday"]}
    monkeypatch.setattr(main, "get_workout_by_id", lambda wid: deepcopy(state["rows"].get(wid)))
    monkeypatch.setattr(main, "get_plan_by_id", lambda pid: plan)
    monkeypatch.setattr(main, "get_user_by_id", lambda uid: PROFILE)
    monkeypatch.setattr(main, "has_active_coach_link", lambda cid, aid: (cid, aid) == (8, 7))

    def update(wid, fields):
        state["rows"][wid].update(fields)

    monkeypatch.setattr(main, "update_workout_mountain_mode", update, raising=False)
    main.app.dependency_overrides[main.get_current_user] = lambda: state["user"]
    yield state
    main.app.dependency_overrides.pop(main.get_current_user, None)


def test_owner_switch_changes_only_selected_workout(state):
    response = TestClient(main.app).patch("/api/workouts/11/mountain-mode", json={"mode": "skip"})
    assert response.status_code == 200
    assert state["rows"][11]["mountain_mode"] == "skip"
    assert state["rows"][12] == {"id": 12, "duration_minutes": 40}


@pytest.mark.parametrize("user, expected", [({"id": 8, "is_coach": True}, 200), ({"id": 9}, 403)])
def test_mode_switch_requires_owner_or_linked_coach(state, user, expected):
    state["user"] = user
    response = TestClient(main.app).patch("/api/workouts/11/mountain-mode", json={"mode": "skip"})
    assert response.status_code == expected
    if expected == 403:
        assert state["rows"][11]["mountain_mode"] == "chill"


def test_invalid_mode_rejected(state):
    assert TestClient(main.app).patch("/api/workouts/11/mountain-mode", json={"mode": "unknown"}).status_code == 422


def test_negative_mountain_minimum_rejected_at_api_boundary():
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="mountain_min_minutes"):
        main.PlanGenerateRequest(goal_type="finish", current_weekly_km=30, mountain_min_minutes=-5)


def test_mountain_mode_preserves_prescribed_zone1_effort():
    pace = f"{zones()['zone1_pace']} /km"
    wo = PlanGenerator.apply_mountain_mode(
        {**workout(), "target_zone": "Zone 1"}, "mountain", Venues(training_mountain="nui_dinh"), zones(), pace
    )
    assert wo["target_zone"] == "Zone 1"
    assert wo["target_hr_range"] == "107-121 bpm"


def test_stairs_then_mountain_restores_original_title():
    original = {**workout(), "title": "Weekend mountain session"}
    wo = PlanGenerator.apply_mountain_mode(original, "indoor", Venues(stair_access=True), zones(), FLAT)
    wo = PlanGenerator.apply_mountain_mode(wo, "mountain", Venues(), zones(), FLAT)
    assert wo["title"] == "Weekend mountain session"
