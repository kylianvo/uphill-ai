from services import goal_service

SHOWN = {"goals": {"a": 480, "b": 540, "c": 600}}


def test_target_on_a_or_c_is_on_track_with_its_tier():
    assert goal_service.status(SHOWN, 8.0) == {"state": "on_track", "suggested_mins": None, "tier": "a"}
    assert goal_service.status(SHOWN, 9.0)["tier"] == "b"
    assert goal_service.status(SHOWN, 10.0)["tier"] == "c"


def test_target_between_tiers_still_drifts_against_b():
    assert goal_service.status(SHOWN, 8.5) == {"state": "behind", "suggested_mins": 540}
    assert goal_service.status(SHOWN, 11.0)["state"] == "ahead"


def test_a_feasibility_uses_the_a_time_as_target(monkeypatch):
    seen = {}

    def fake(plan, assessment=None):
        seen.update(plan)
        return {"verdict": "stretch"}

    monkeypatch.setattr(goal_service, "feasibility_for", fake)
    plan = {"goal_type": "finish", "target_time_hours": None}
    assert goal_service.a_feasibility_for(plan, SHOWN) == {"verdict": "stretch"}
    assert seen["goal_type"] == "time" and seen["target_time_hours"] == 8.0
    assert goal_service.a_feasibility_for(plan, None) is None


def test_targets_hold_the_long_run_to_the_tier_cap():
    plan = {
        "course_distance_km": 70,
        "course_elevation_gain_m": 4000,
        "goal_type": "time",
        "target_time_hours": 11.0,
        "athlete_tier": "intermediate",
        "days_per_week": 5,
    }
    t = goal_service.targets_for(plan, None)
    assert t["long_run_min"] > 0 and t["peak_week_km"] > 0
    assert goal_service.targets_for({"course_distance_km": None}, None) is None


def _with_latest(monkeypatch):
    monkeypatch.setattr(goal_service.db, "get_latest_goal_assessment", lambda plan_id: {"id": 1})
    monkeypatch.setattr(goal_service, "_present", lambda row: dict(SHOWN))
    monkeypatch.setattr(goal_service, "with_plan_support", lambda shown, plan: shown)


def test_an_a_target_trains_at_b_until_the_gate_opens(monkeypatch):
    _with_latest(monkeypatch)
    plan = {"id": 7, "target_time_hours": 8.0}
    assert goal_service.training_target_hours(plan, gate_open=False) == 9.0
    assert goal_service.training_target_hours(plan, gate_open=True) == 8.0


def test_b_and_c_targets_are_never_changed(monkeypatch):
    _with_latest(monkeypatch)
    assert goal_service.training_target_hours({"id": 7, "target_time_hours": 9.0}, gate_open=False) == 9.0
    assert goal_service.training_target_hours({"id": 7, "target_time_hours": 10.0}, gate_open=False) == 10.0
    assert goal_service.training_target_hours({"id": 7, "target_time_hours": None}, gate_open=False) is None
