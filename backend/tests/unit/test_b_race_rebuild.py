from datetime import date

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import main
from services import b_race, course_match, goal_service, race_matcher, week_rebuild

client = TestClient(main.app)
MON = date(2026, 9, 28)
PLAN = {"id": 5, "user_id": 7, "goal_type": "time", "race_name": "VMM 70K", "race_date": "2026-12-13",
        "course_distance_km": 70, "course_elevation_gain_m": 4000, "start_date": "2026-09-28", "total_weeks": 12}  # fmt: skip
BODY = {"race_name": "Ta Xua Trail", "race_date": "2026-11-01", "distance_km": 25, "elevation_gain_m": 1000}


def rows(weeks):
    return [{"id": wk * 10 + i, "week_number": wk, "day_of_week": d, "type": "Easy", "duration_minutes": 50,
             "plan_race_id": None, "is_completed": 0}
            for wk in weeks for i, d in enumerate(b_race.DAYS)]  # fmt: skip


def test_affected_weeks_cover_taper_race_and_recovery():
    race = {"id": 1, "race_date": "2026-11-02", "distance_km": 50, "elevation_gain_m": 2500, "effort": "race"}
    assert b_race.affected_weeks(race, MON) == {5, 6, 7}  # Monday race: taper in week 5, 10 days recovery
    assert b_race.generated_weeks(rows([1, 2, 6])) == {1, 2, 6}


@pytest.fixture
def api(monkeypatch):
    st = {"rows": [], "workouts": rows(range(1, 7)), "adapted": [], "deleted": []}
    monkeypatch.setattr(main, "get_recent_plans", lambda uid, limit=3: [{"id": 5}])
    monkeypatch.setattr(main.db, "get_plan_by_id", lambda pid: dict(PLAN))
    monkeypatch.setattr(main.db, "longest_recent_run", lambda uid, since: (34.0, 200.0))
    monkeypatch.setattr(main.db, "get_plan_workouts", lambda pid: st["workouts"])
    monkeypatch.setattr(main, "get_plan_workouts", lambda pid: st["workouts"])
    monkeypatch.setattr(
        main.db, "get_plan_races",
        lambda pid, include_cancelled=False: [r for r in st["rows"] if include_cancelled or r["status"] != "cancelled"],
    )  # fmt: skip
    monkeypatch.setattr(
        main.db, "get_plan_race", lambda pid, rid: next((r for r in st["rows"] if r["id"] == rid), None)
    )
    monkeypatch.setattr(
        main.db, "insert_plan_race",
        lambda pid, f: st["rows"].append({"id": len(st["rows"]) + 1, "status": "planned", "options_km": [], **f})
        or len(st["rows"]),
    )  # fmt: skip
    monkeypatch.setattr(main.db, "update_plan_race", lambda rid, f: st["rows"][rid - 1].update(f))
    monkeypatch.setattr(main.db, "delete_race_workouts", lambda rid: st["deleted"].append(rid) or 1)
    monkeypatch.setattr(race_matcher, "race_distances", lambda name: [])
    monkeypatch.setattr(race_matcher, "match_race", lambda name, **k: None)
    monkeypatch.setattr(course_match, "resolve_course_match", lambda n, d, g: (d, g, None))
    monkeypatch.setattr(goal_service, "run", lambda **kw: {"goals": {"a": 185, "b": 195, "c": 205}})
    monkeypatch.setattr(b_race, "current_date", lambda: date(2026, 10, 26))

    async def adapt(request, athlete_id, job_owner_user_id):
        if request.week_number < 5:
            raise HTTPException(status_code=422, detail={"code": "G3_past_target"})
        st["adapted"].append((request.week_number, request.coach_notes))
        return {"job_id": f"job-{request.week_number}"}

    monkeypatch.setattr(main, "_adapt_week_for_athlete", adapt)
    main.app.dependency_overrides[main.get_current_user] = lambda: {"id": 7}
    yield st
    main.app.dependency_overrides.pop(main.get_current_user, None)


def test_add_rebuilds_race_and_recovery_weeks_only_if_generated(api):
    r = client.post("/api/plans/5/races", json=BODY)  # week 5 Sunday; recovery Mon–Fri week 6
    assert r.json()["rebuild_job_ids"] == ["job-5", "job-6"]
    assert [w for w, _ in api["adapted"]] == [5, 6] and "B-race" in api["adapted"][0][1]
    api["adapted"].clear()
    r = client.post(
        "/api/plans/5/races", json={**BODY, "race_date": "2026-11-22", "distance_km": 10, "elevation_gain_m": 0}
    )
    assert r.json()["rebuild_job_ids"] == [] and api["adapted"] == []  # week 8 isn't generated yet


def test_cancel_removes_race_row_and_rebuilds(api):
    rid = client.post("/api/plans/5/races", json=BODY).json()["race"]["id"]
    api["adapted"].clear()
    r = client.delete(f"/api/plans/5/races/{rid}")
    assert api["deleted"] == [rid] and r.json()["rebuild_job_ids"] == ["job-5", "job-6"]


def test_past_week_never_rebuilt(api):
    rid = client.post("/api/plans/5/races", json=BODY).json()["race"]["id"]
    api["adapted"].clear()
    # moving the race earlier puts its taper in a past week: that week is skipped, not an error
    r = client.patch(f"/api/plans/5/races/{rid}", json={"race_date": "2026-10-27"})
    assert r.status_code == 200 and 4 not in [w for w, _ in api["adapted"]]


def test_partly_logged_week_keeps_logged_rows():
    ws = rows([5])
    ws[3]["is_completed"] = 1  # Thursday already done
    rng = week_rebuild.rebuild_range(PLAN, ws, 5, date(2026, 10, 27))  # Tuesday of week 5
    assert 53 not in rng.replaceable_ids and 53 in rng.kept_ids and rng.from_day == "Tuesday"


def test_editing_assesses_the_race_without_itself(api):
    rid = client.post("/api/plans/5/races", json=BODY).json()["race"]["id"]
    same = client.post("/api/plans/5/races/assess", json={**BODY, "race_id": rid}).json()
    assert "stacked" not in same["verdict"]["reasons"]
    other = client.post("/api/plans/5/races/assess", json=BODY).json()  # a second race on the same day does stack
    assert "stacked" in other["verdict"]["reasons"]


def test_model_calls_run_off_the_event_loop(api, monkeypatch):
    import asyncio

    seen = []

    def create(user, plan, data):
        try:
            asyncio.get_running_loop()
            seen.append("on the loop")
        except RuntimeError:
            seen.append("worker thread")
        return {**data, "id": 1, "race_date": data["race_date"], "verdict": {"level": "good"}, "status": "planned",
                "effort": "race", "kept_against": None}  # fmt: skip

    monkeypatch.setattr(b_race, "create", create)
    monkeypatch.setattr(main, "_b_race_words", lambda user, plan, race: _same(race))
    client.post("/api/plans/5/races", json=BODY)
    assert seen == ["worker thread"]


async def _same(race):
    return race


def test_edit_while_its_weeks_rebuild_is_409(api):
    rid = client.post("/api/plans/5/races", json=BODY).json()["race"]["id"]
    main.plan_jobs["busy"] = {"plan_id": 5, "kind": "adapt_week", "target_week": 6, "status": "generating"}
    try:
        r = client.patch(f"/api/plans/5/races/{rid}", json={"effort": "training"})
        assert r.status_code == 409 and r.json()["detail"] == "rebuild_in_progress"
        assert client.delete(f"/api/plans/5/races/{rid}").status_code == 409
        assert api["deleted"] == []  # nothing was removed while the week was being rebuilt
    finally:
        main.plan_jobs.pop("busy", None)
