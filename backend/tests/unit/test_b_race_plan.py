from datetime import date

import pytest

import db
from services import b_race, course_match, goal_service, race_matcher

PLAN = {"id": 5, "goal_type": "time", "race_date": "2026-12-13", "course_distance_km": 70,
        "course_elevation_gain_m": 4000, "start_date": "2026-09-28", "total_weeks": 12}  # fmt: skip
TODAY = date(2026, 10, 26)


@pytest.fixture(autouse=True)
def quiet(monkeypatch):
    monkeypatch.setattr(db, "longest_recent_run", lambda uid, since: (30.0, 200.0))
    monkeypatch.setattr(db, "get_plan_races", lambda pid, include_cancelled=False: [])
    monkeypatch.setattr(race_matcher, "race_distances", lambda name: [])
    monkeypatch.setattr(race_matcher, "match_race", lambda name, **k: None)
    monkeypatch.setattr(course_match, "resolve_course_match", lambda n, d, g: (d, g, None))


def test_facts_use_longest_run_of_last_six_weeks(monkeypatch):
    seen = {}
    monkeypatch.setattr(db, "longest_recent_run", lambda uid, since: seen.setdefault("since", since) and (24.0, 190.0))
    f = b_race.facts_for_plan(7, PLAN, today=TODAY)
    assert seen["since"] == date(2026, 9, 14)
    assert (f.a_date, f.a_distance_km, f.plan_monday, f.total_weeks) == (date(2026, 12, 13), 70, date(2026, 9, 28), 12)
    assert f.longest_recent_km == 24.0


def test_unmatched_race_without_distance_raises():
    with pytest.raises(ValueError, match="distance_required"):
        b_race.resolve_input({"race_name": "Unknown hill race", "race_date": "2026-11-01"})


def test_options_come_from_matched_course(monkeypatch):
    monkeypatch.setattr(
        race_matcher, "race_distances", lambda name: [{"distance_km": 42}, {"distance_km": 15}, {"distance_km": 25}]
    )
    monkeypatch.setattr(course_match, "resolve_course_match", lambda n, d, g: (d or 25, g or 1000, None))
    r = b_race.resolve_input({"race_name": "Ta Xua Trail", "race_date": "2026-11-01"})
    assert r["options_km"] == [15, 25, 42] and r["distance_km"] == 25 and r["elevation_gain_m"] == 1000


def test_prediction_is_none_when_goal_service_fails(monkeypatch):
    def boom(**kw):
        raise RuntimeError("no anchors")

    monkeypatch.setattr(goal_service, "run", boom)
    out = b_race.evaluate({"id": 7}, PLAN, {"race_name": "X", "race_date": "2026-11-01", "distance_km": 25},
                          predict=True, today=TODAY)  # fmt: skip
    assert out["predicted"] is None and out["verdict"]["level"] in b_race.LEVELS


def test_prediction_never_attaches_to_the_plan(monkeypatch):
    seen = {}
    monkeypatch.setattr(goal_service, "run", lambda **kw: seen.update(kw) or {"goals": {"a": 185, "b": 195, "c": 205}})
    out = b_race.evaluate({"id": 7}, PLAN, {"race_name": "X", "race_date": "2026-11-01", "distance_km": 25},
                          predict=True, today=TODAY)  # fmt: skip
    assert seen["plan"] is None and seen["trigger"] == "b_race"
    assert out["predicted"] == {"low_sec": 185 * 60, "high_sec": 205 * 60}


def test_live_assess_skips_prediction(monkeypatch):
    monkeypatch.setattr(goal_service, "run", lambda **kw: pytest.fail("no prediction while assessing"))
    out = b_race.evaluate(
        {"id": 7}, PLAN, {"race_name": "X", "race_date": "2026-11-01", "distance_km": 25}, today=TODAY
    )
    assert out["predicted"] is None


def test_other_planned_races_feed_stacking_but_not_the_race_itself(monkeypatch):
    rows = [
        {"id": 1, "race_date": date(2026, 10, 25), "distance_km": 25, "elevation_gain_m": 1000, "effort": "race"},
        {"id": 2, "race_date": date(2026, 11, 8), "distance_km": 25, "elevation_gain_m": 1000, "effort": "race"},
    ]
    monkeypatch.setattr(db, "get_plan_races", lambda pid, include_cancelled=False: rows)
    f = b_race.facts_for_plan(7, PLAN, exclude_race_id=2, today=TODAY)
    assert [o.race_date for o in f.other_races] == [date(2026, 10, 25)]


def test_is_race_plan():
    assert b_race.is_race_plan(PLAN) and not b_race.is_race_plan({**PLAN, "goal_type": "start_running"})
