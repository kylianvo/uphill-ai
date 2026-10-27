from datetime import date

import db
from services import b_race, coach_nudge
from services.coach_tools import plan_tools

MON = date(2026, 9, 28)
RACE = {"id": 9, "race_name": "Ta Xua 25K", "race_date": date(2026, 11, 1), "distance_km": 25, "elevation_gain_m": 1000,
        "effort": "race", "kept_against": None, "status": "planned", "verdict": {"level": "good"}}  # fmt: skip
PLAN = {"id": 5, "user_id": 7, "goal_type": "time", "race_name": "VMM 70K", "race_date": "2026-12-13",
        "course_distance_km": 70, "course_elevation_gain_m": 4000, "start_date": "2026-09-28", "total_weeks": 12}  # fmt: skip


def test_brief_fact_only_in_race_and_recovery_weeks():
    fact = b_race.brief_fact([RACE], 5, MON)
    assert fact.startswith("B-race this week: Ta Xua 25K on Sunday") and "taper Thu–Sat" in fact
    assert b_race.brief_fact([RACE], 6, MON).startswith("B-race recovery: Zone 1 only until Friday")
    assert b_race.brief_fact([RACE], 4, MON) is None and b_race.brief_fact([RACE], 7, MON) is None


def test_coach_context_lists_planned_races_only(monkeypatch):
    rows = [RACE, {**RACE, "id": 10, "status": "done", "race_name": "Old race"}]
    monkeypatch.setattr(db, "get_plan_races", lambda pid, include_cancelled=False: rows)
    block = b_race.coach_context_block(PLAN)
    assert [r["race_name"] for r in block] == ["Ta Xua 25K"] and block[0]["level"] == "good"
    assert b_race.coach_context_block({**PLAN, "goal_type": "start_running"}) == []


def w(week, day, minutes=50, type_="Easy"):
    return {"week_number": week, "day_of_week": day, "type": type_, "duration_minutes": minutes, "title": type_,
            "phase": "Build", "is_completed": 0}  # fmt: skip


def test_nudge_facts_carry_the_b_race_of_this_week():
    ws = [w(5, d) for d in ("Tuesday", "Thursday")] + [
        {**w(5, "Sunday", 195, "Race"), "title": "Ta Xua 25K", "plan_race_id": 9}
    ]
    f = coach_nudge.facts_for(PLAN, ws, date(2026, 10, 27), readiness_flag=None, feasibility_verdict=None,
                              plan_supported=True, b_races=[RACE])  # fmt: skip
    assert f["b_race_this_week"] == {"race_name": "Ta Xua 25K", "day": "Sunday", "distance_km": 25, "effort": "race"}
    f2 = coach_nudge.facts_for(PLAN, ws, date(2026, 10, 27), readiness_flag=None, feasibility_verdict=None,
                               plan_supported=True)  # fmt: skip
    assert f2["b_race_this_week"] is None


def test_chat_tool_refuses_non_race_plans(monkeypatch):
    monkeypatch.setattr(db, "get_active_plan", lambda uid: {**PLAN, "goal_type": "start_running"})
    r = plan_tools.assess_b_race_impl(7, race_name="Ta Xua", race_date="2026-11-01", distance_km=25)
    assert r.status == "error" and r.error == "not_a_race_plan"


def test_chat_tool_returns_verdict_and_points_to_the_plan_screen(monkeypatch):
    monkeypatch.setattr(db, "get_active_plan", lambda uid: PLAN)
    monkeypatch.setattr(db, "get_user_by_id", lambda uid: {"id": 7})
    monkeypatch.setattr(b_race, "evaluate", lambda user, plan, data, **k: {"verdict": {"level": "good"}, "race": data})
    monkeypatch.setattr(b_race, "current_date", lambda: date(2026, 10, 26))
    r = plan_tools.assess_b_race_impl(7, race_name="Ta Xua", race_date="2026-11-01", distance_km=25)
    assert r.status == "success" and r.card_data["verdict"]["level"] == "good"
    assert "Add race" in r.card_data["how_to_add"]
