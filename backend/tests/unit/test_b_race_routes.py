from datetime import date

import pytest
from fastapi.testclient import TestClient

import main
from services import course_match, goal_service, race_matcher

client = TestClient(main.app)
PLAN = {"id": 5, "user_id": 7, "goal_type": "time", "race_name": "VMM 70K", "race_date": "2026-12-13",
        "course_distance_km": 70, "course_elevation_gain_m": 4000, "start_date": "2026-09-28", "total_weeks": 12}  # fmt: skip
BODY = {"race_name": "Ta Xua Trail", "race_date": "2026-11-01", "distance_km": 25, "elevation_gain_m": 1000}


@pytest.fixture
def api(monkeypatch):
    st = {"plan": dict(PLAN), "rows": [], "updates": []}
    monkeypatch.setattr(main, "get_recent_plans", lambda uid, limit=3: [{"id": 5}] if uid == 7 else [])
    monkeypatch.setattr(main.db, "get_plan_by_id", lambda pid: st["plan"] if pid == 5 else None)
    monkeypatch.setattr(main.db, "longest_recent_run", lambda uid, since: (34.0, 200.0))
    monkeypatch.setattr(
        main.db,
        "get_plan_races",
        lambda pid, include_cancelled=False: [r for r in st["rows"] if include_cancelled or r["status"] != "cancelled"],
    )
    monkeypatch.setattr(
        main.db, "get_plan_race", lambda pid, rid: next((r for r in st["rows"] if r["id"] == rid), None)
    )

    def insert(pid, fields):
        row = {"id": len(st["rows"]) + 1, "plan_id": pid, "status": "planned", "effort": "race", "options_km": [],
               "kept_against": None, **fields}  # fmt: skip
        st["rows"].append(row)
        return row["id"]

    def update(rid, fields):
        st["updates"].append((rid, fields))
        next(r for r in st["rows"] if r["id"] == rid).update(fields)

    monkeypatch.setattr(main.db, "insert_plan_race", insert)
    monkeypatch.setattr(main.db, "update_plan_race", update)
    monkeypatch.setattr(main.db, "delete_race_workouts", lambda rid: 0)
    monkeypatch.setattr(main, "get_plan_workouts", lambda pid: [])
    monkeypatch.setattr(race_matcher, "race_distances", lambda name: [])
    monkeypatch.setattr(race_matcher, "match_race", lambda name, **k: None)
    monkeypatch.setattr(course_match, "resolve_course_match", lambda n, d, g: (d, g, None))
    monkeypatch.setattr(goal_service, "run", lambda **kw: {"goals": {"a": 185, "b": 195, "c": 205}})
    monkeypatch.setattr(main.b_race, "current_date", lambda: date(2026, 10, 26))
    main.app.dependency_overrides[main.get_current_user] = lambda: {"id": 7}
    yield st
    main.app.dependency_overrides.pop(main.get_current_user, None)


def test_other_users_plan_is_404(api):
    main.app.dependency_overrides[main.get_current_user] = lambda: {"id": 8}
    assert client.get("/api/plans/5/races").status_code == 404


def test_assess_returns_level_and_suggestion(api):
    r = client.post("/api/plans/5/races/assess", json={**BODY, "distance_km": 42, "elevation_gain_m": 2400})
    assert r.status_code == 200
    v = r.json()["verdict"]
    assert v["level"] == "risky" and v["suggestion"]["effort"] == "training" and r.json()["predicted"] is None


def test_non_race_plan_400(api):
    api["plan"]["goal_type"] = "start_running"
    assert client.post("/api/plans/5/races/assess", json=BODY).json()["detail"] == "not_a_race_plan"


def test_date_after_a_race_400(api):
    r = client.post("/api/plans/5/races", json={**BODY, "race_date": "2026-12-20"})
    assert r.status_code == 400 and r.json()["detail"] == "date_out_of_range"


def test_race_without_distance_422(api):
    r = client.post("/api/plans/5/races/assess", json={"race_name": "Unknown", "race_date": "2026-11-01"})
    assert r.status_code == 422 and r.json()["detail"] == "distance_required"


def test_create_stores_verdict_and_prediction(api):
    r = client.post("/api/plans/5/races", json=BODY)
    race = r.json()["race"]
    assert r.status_code == 200 and r.json()["rebuild_job_ids"] == []
    assert race["verdict"]["level"] == "good" and race["predicted"] == {"low_sec": 11100, "high_sec": 12300}
    assert (race["week"], race["day"]) == (5, "Sunday")


def test_fourth_race_409(api):
    for d in ("2026-10-31", "2026-11-07", "2026-11-14"):
        client.post("/api/plans/5/races", json={**BODY, "race_date": d, "distance_km": 10, "elevation_gain_m": 0})
    assert client.post("/api/plans/5/races", json=BODY).status_code == 409


def test_not_recommended_saved_as_training(api):
    race = client.post("/api/plans/5/races", json={**BODY, "race_date": "2026-12-03"}).json()["race"]
    assert race["effort"] == "training" and race["kept_against"] == "not_recommended"


def test_list_reassesses_after_a_date_moves(api):
    client.post("/api/plans/5/races", json=BODY)
    api["plan"]["race_date"] = "2026-11-10"  # the A-race moved: the B-race is now 9 days before it
    assert client.get("/api/plans/5/races").json()["races"][0]["verdict"]["level"] == "not_recommended"


def test_patch_reassesses_and_delete_cancels(api):
    rid = client.post("/api/plans/5/races", json=BODY).json()["race"]["id"]
    r = client.patch(f"/api/plans/5/races/{rid}", json={"effort": "training"})
    assert r.json()["race"]["effort"] == "training"
    assert client.delete(f"/api/plans/5/races/{rid}").json()["race"]["status"] == "cancelled"
    assert client.get("/api/plans/5/races").json()["races"] == []


def test_active_plan_lists_b_races(api, monkeypatch):
    monkeypatch.setattr(main, "get_active_plan", lambda uid: api["plan"])
    monkeypatch.setattr(main, "get_plan_workouts", lambda pid: [])
    monkeypatch.setattr(main.db, "get_plan_milestone_rows", lambda pid: [])
    client.post("/api/plans/5/races", json=BODY)
    assert [r["race_name"] for r in client.get("/api/coach/active-plan").json()["plan"]["b_races"]] == ["Ta Xua Trail"]


def test_setup_races_saved_and_bad_ones_skipped(api):
    saved = main.b_race.save_setup_races({"id": 7}, 5, [BODY, {"race_name": "No distance", "race_date": "2026-11-08"}])
    assert saved == 1 and [r["race_name"] for r in api["rows"]] == ["Ta Xua Trail"]
