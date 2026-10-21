"""refresh_milestones against an in-memory fake of the db module, plus the log_workout hook."""

import pytest
from fastapi.testclient import TestClient

import main
from services import beginner_milestones as bm

PLAN = {"id": 5, "user_id": 7, "goal_type": "start_running", "milestone_target": "5k", "start_date": "2026-10-05"}


@pytest.fixture
def fake(monkeypatch):
    st = {"plan": dict(PLAN), "rows": [], "workouts": [], "acts": [], "jog": []}
    import db

    monkeypatch.setattr(db, "get_active_plan", lambda uid: st["plan"])
    monkeypatch.setattr(db, "get_plan_milestone_rows", lambda pid: st["rows"])
    monkeypatch.setattr(db, "get_completed_run_workouts", lambda pid: st["workouts"])
    monkeypatch.setattr(db, "get_run_activities_since", lambda uid, since: st["acts"])
    monkeypatch.setattr(db, "set_max_continuous_jog_min", lambda uid, m: st["jog"].append(m) or True)

    def insert(pid, key, source, at, activity_id=None, workout_id=None):
        st["rows"].append({"milestone_key": key, "source": source, "achieved_at": at})
        return True

    monkeypatch.setattr(db, "insert_milestone_if_absent", insert)
    return st


def _w(wid, minutes):
    return {"id": wid, "week_number": 1, "type": "Easy Run", "duration_minutes": minutes, "walk_interval_value": None}


def test_refresh_noop_without_target(fake):
    fake["plan"]["milestone_target"] = None
    fake["workouts"] = [_w(1, 20)]
    assert bm.refresh_milestones(7) == [] and fake["rows"] == []


def test_refresh_noop_for_non_beginner_goal(fake):
    fake["plan"]["goal_type"] = "race"
    fake["workouts"] = [_w(1, 20)]
    assert bm.refresh_milestones(7) == []


def test_refresh_noop_without_plan(fake):
    fake["plan"] = None
    assert bm.refresh_milestones(7) == []


def test_refresh_inserts_auto_rows_and_raises_jog_ceiling(fake):
    fake["workouts"] = [_w(1, 10)]
    got = bm.refresh_milestones(7)
    assert set(got) == {"first_session", "jog_5", "jog_10"}
    assert {r["source"] for r in fake["rows"]} == {"auto"}
    assert max(fake["jog"]) == 10


def test_refresh_is_idempotent_over_existing_rows(fake):
    fake["workouts"] = [_w(1, 10)]
    bm.refresh_milestones(7)
    fake["rows"][:] = [{**r} for r in fake["rows"]]
    assert bm.refresh_milestones(7) == []


def test_safe_refresh_swallows_errors(fake, monkeypatch):
    monkeypatch.setattr(bm, "refresh_milestones", lambda uid: (_ for _ in ()).throw(RuntimeError("boom")))
    bm.safe_refresh_milestones(7)  # must not raise


# --- log_workout hook -------------------------------------------------------

client = TestClient(main.app)


@pytest.fixture
def logged(monkeypatch):
    calls = []
    monkeypatch.setattr(main, "get_active_plan", lambda uid: {"id": 5})
    monkeypatch.setattr(main, "get_plan_workouts", lambda pid: [{"id": 11}])
    monkeypatch.setattr(main, "update_workout_log", lambda *a, **k: True)
    monkeypatch.setattr(main.beginner_milestones, "safe_refresh_milestones", lambda uid: calls.append(uid))
    main.app.dependency_overrides[main.get_current_user] = lambda: {"id": 7}
    yield calls
    main.app.dependency_overrides.pop(main.get_current_user, None)


def test_log_workout_complete_ticks_jog_milestone(logged):
    r = client.patch("/api/coach/workouts/log", json={"workout_id": 11, "is_completed": 1})
    assert r.status_code == 200 and logged == [7]


def test_log_workout_uncomplete_does_not_refresh(logged):
    r = client.patch("/api/coach/workouts/log", json={"workout_id": 11, "is_completed": 0})
    assert r.status_code == 200 and logged == []
