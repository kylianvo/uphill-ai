import asyncio
from datetime import UTC, date, datetime

import pytest
from fastapi.testclient import TestClient

import main
from services import b_race, b_race_words, goal_service, race_history

client = TestClient(main.app)
RACE = {"id": 3, "plan_id": 5, "race_name": "Ta Xua Trail", "race_date": date(2026, 11, 1), "distance_km": 25,
        "elevation_gain_m": 1000, "effort": "race", "status": "planned", "kept_against": None,
        "predicted": {"low_sec": 11100, "high_sec": 12300}, "debrief": None, "result_seconds": None}  # fmt: skip
PLAN = {"id": 5, "user_id": 7, "goal_type": "time", "race_name": "VMM 70K", "race_date": "2026-12-13",
        "target_time_hours": 11.0, "course_distance_km": 70, "course_elevation_gain_m": 4000,
        "start_date": "2026-09-28", "total_weeks": 12}  # fmt: skip


def act(aid, day, km, secs=11460):
    return {
        "id": aid,
        "start_time": datetime(2026, 11, day, 6, tzinfo=UTC),
        "distance_km": km,
        "duration_seconds": secs,
    }


def test_shakeout_on_race_day_not_linked():
    assert b_race.match_result(RACE, [act(1, 1, 5.0, 1800)]) is None


def test_closest_distance_wins():
    got = b_race.match_result(RACE, [act(1, 1, 22.0), act(2, 1, 25.6), act(3, 3, 25.0)])
    assert got["id"] == 2  # 3 Nov is two days later: not the race


@pytest.fixture
def st(monkeypatch):
    st = {"race": dict(RACE), "history": [], "updates": []}
    monkeypatch.setattr(main.db, "get_plan_race", lambda pid, rid: st["race"] if rid == 3 else None)
    monkeypatch.setattr(main.db, "update_plan_race", lambda rid, f: st["updates"].append(f) or st["race"].update(f))
    monkeypatch.setattr(race_history, "create_manual", lambda uid, d: st["history"].append(d) or {"id": 77, **d})
    monkeypatch.setattr(
        goal_service, "run_for_plan", lambda user, plan, trigger, **k: {"goals": {"a": 600, "b": 640, "c": 700}}
    )
    monkeypatch.setattr(main, "get_recent_plans", lambda uid, limit=3: [{"id": 5}])
    monkeypatch.setattr(main.db, "get_plan_by_id", lambda pid: dict(PLAN))
    main.app.dependency_overrides[main.get_current_user] = lambda: {"id": 7}
    yield st
    main.app.dependency_overrides.pop(main.get_current_user, None)


def test_manual_result_marks_done_and_writes_race_history(st):
    r = client.post("/api/plans/5/races/3/result", json={"finish_time_sec": 11460})
    assert r.status_code == 200 and st["race"]["status"] == "done" and st["race"]["result_seconds"] == 11460
    h = st["history"][0]
    assert (h["race_name"], h["distance_km"], h["finish_time_sec"], h["discipline"]) == (
        "Ta Xua Trail",
        25,
        11460,
        "trail",
    )
    client.post("/api/plans/5/races/3/result", json={"finish_time_sec": 11400})  # a correction
    assert len(st["history"]) == 1 and st["race"]["result_seconds"] == 11400


def test_refresh_links_the_synced_race(monkeypatch, st):
    monkeypatch.setattr(main.db, "get_active_plan", lambda uid: dict(PLAN))
    monkeypatch.setattr(main.db, "get_plan_races", lambda pid, include_cancelled=False: [st["race"]])
    monkeypatch.setattr(main.db, "get_run_activities_since", lambda uid, since: [act(9, 1, 25.3)])
    monkeypatch.setattr(b_race, "current_date", lambda: date(2026, 11, 2))
    b_race.safe_refresh_results(7)
    assert st["race"]["activity_id"] == 9 and st["race"]["status"] == "done" and len(st["history"]) == 1


def test_debrief_text_grounded_and_fallback_en_vi():
    facts = b_race.debrief_facts(
        {**RACE, "result_seconds": 11460}, {"fuel": "plan", "pacing": "fast_start", "gear": "ok"}
    )
    assert facts["vs_prediction"] == "inside" and facts["result_time"] == "3:11:00"
    for lang in ("en", "vi"):
        text = b_race_words.fallback_debrief(facts, lang)
        assert "3:11:00" in text and b_race_words.grounded_debrief(text, facts)
    out = asyncio.run(b_race_words.debrief_text(facts, "en", api_key=None))
    assert out["source"] == "rules"


def test_kept_risky_adds_two_recovery_days():
    plain = b_race.debrief_facts({**RACE, "result_seconds": 11460}, {})
    risky = b_race.debrief_facts({**RACE, "result_seconds": 11460, "kept_against": "risky"}, {})
    assert risky["recovery_days"] == plain["recovery_days"] + 2


def test_target_change_is_only_suggested(st):
    st["race"]["result_seconds"] = 11460
    r = client.post("/api/plans/5/races/3/debrief", json={"fuel": "plan", "pacing": "even", "gear": "ok"})
    body = r.json()
    assert r.status_code == 200 and body["goal"]["suggested_target_hours"] == 10.67  # 640 min vs the 11:00 target
    assert body["debrief"]["answers"]["fuel"] == "plan" and body["debrief"]["text"]
    assert not any("target_time_hours" in u for u in st["updates"])  # the plan's target is untouched
