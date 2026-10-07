"""goal_context.gather accepts the iOS sheet's group exclusion keys."""

import pytest

from services import goal_context

TARGET = {"race_name": "Synthetic 50K", "distance_km": 50.0, "elevation_gain_m": 2500.0}
USER = {
    "id": 7,
    "gender": "male",
    "current_weekly_km": 70.0,
    "coros_vo2max": 55.0,
    "zone2_pace_min": "6:00",
    "zone2_pace_max": "6:40",
}
RESULT = {
    "id": 11,
    "race_name": "Synthetic Trail 30K",
    "race_date": "2025-05-01",
    "is_dnf": False,
    "finish_time_sec": 14400,
    "distance_km": 30.0,
    "elevation_gain_m": 1500.0,
    "discipline": "trail",
}


@pytest.fixture(autouse=True)
def stub(monkeypatch):
    monkeypatch.setattr(goal_context.race_history, "list_results", lambda uid, sel: [RESULT])
    monkeypatch.setattr(goal_context.race_history, "_dedupe", lambda rows: rows)
    monkeypatch.setattr(goal_context.db, "get_utmb_index", lambda uid: None)
    monkeypatch.setattr(goal_context.db, "get_weekly_training_trend", lambda uid: None)
    monkeypatch.setattr(goal_context.db, "get_latest_fitness_assessment", lambda uid: {"pred_marathon_sec": 10560.0})


def test_race_history_excludes_every_linked_result():
    ctx = goal_context.gather(user=USER, target=TARGET, race_date="2026-12-06", exclude={"race_history"})
    assert ctx.results == []
    assert [s["included"] for s in ctx.sources if s["key"].startswith("result:")] == [False]


def test_physiology_excludes_vo2max_prediction_and_easy_pace():
    ctx = goal_context.gather(user=USER, target=TARGET, race_date="2026-12-06", exclude={"physiology"})
    athlete = ctx.prompt["athlete"]
    assert "vo2max" not in athlete
    assert "marathon_prediction_sec" not in athlete
    assert "easy_pace_min_km" not in athlete
    assert ctx.easy_pace_min_km is None


def test_nothing_excluded_keeps_all_three():
    ctx = goal_context.gather(user=USER, target=TARGET, race_date="2026-12-06")
    assert len(ctx.results) == 1
    assert {"vo2max", "marathon_prediction_sec", "easy_pace_min_km"} <= ctx.prompt["athlete"].keys()
