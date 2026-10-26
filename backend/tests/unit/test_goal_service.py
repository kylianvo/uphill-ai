def test_vert_targets_for_the_plan_view_match_the_generators(monkeypatch):
    """The week rows show the same R-C8 targets the generator built the weeks to, from the plan's stored snapshot."""
    from config import settings
    from services import goal_service

    monkeypatch.setattr(settings, "PLAN_DEMANDS_ENABLED", True)
    plan = {
        "id": 131,
        "course_distance_km": 104.2,
        "course_elevation_gain_m": 5533,
        "goal_type": "time",
        "target_time_hours": 15.75,
        "total_weeks": 13,
        "mountain_days": '["Saturday"]',
        "training_mountain": "nui_dinh",
        "fitness_snapshot": {"weekly_vert_m": 589},
    }
    targets = goal_service.vert_targets_for(plan)
    assert targets["9"] == round(0.40 * 5533, -1) and "4" not in targets and int(targets["1"]) >= 589
    assert goal_service.vert_targets_for({**plan, "training_mountain": "chau_thoi"}) == {}  # too gentle, no stairs
    assert goal_service.vert_targets_for({**plan, "course_elevation_gain_m": 300}) == {}  # flat course
