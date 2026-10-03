"""goal_context.gather surfaces the COROS marathon prediction as a toggleable source."""

from datetime import UTC, datetime

import pytest

from services import goal_context

TARGET = {"race_name": "Synthetic 50K", "distance_km": 50.0, "elevation_gain_m": 2500.0}
USER = {"id": 7, "gender": "male", "current_weekly_km": 70.0}


@pytest.fixture
def stub(monkeypatch):
    state = {"assessment": {"pred_marathon_sec": 10560.0, "measured_at": datetime(2026, 8, 27, tzinfo=UTC)}}
    monkeypatch.setattr(goal_context.race_history, "list_results", lambda uid, sel: [])
    monkeypatch.setattr(goal_context.db, "get_utmb_index", lambda uid: None)
    monkeypatch.setattr(goal_context.db, "get_weekly_training_trend", lambda uid: None)
    monkeypatch.setattr(goal_context.db, "get_latest_fitness_assessment", lambda uid: state["assessment"])
    return state


def test_marathon_prediction_reaches_the_prompt(stub):
    ctx = goal_context.gather(user=USER, target=TARGET, race_date="2026-12-06")
    assert ctx.prompt["athlete"]["marathon_prediction_sec"] == 10560.0
    assert any(s["key"] == "predictor" and "2:56" in s["label"] for s in ctx.sources)


def test_the_predictor_can_be_excluded(stub):
    ctx = goal_context.gather(user=USER, target=TARGET, race_date="2026-12-06", exclude={"predictor"})
    assert "marathon_prediction_sec" not in ctx.prompt["athlete"]


def test_no_assessment_is_reported_missing(stub):
    stub["assessment"] = None
    ctx = goal_context.gather(user=USER, target=TARGET, race_date="2026-12-06")
    assert "marathon_prediction_sec" not in ctx.prompt["athlete"]
    assert "predictor" in ctx.missing
