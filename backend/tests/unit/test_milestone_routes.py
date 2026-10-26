from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

import main

client = TestClient(main.app)
PLAN = {
    "id": 5,
    "user_id": 7,
    "goal_type": "start_running",
    "milestone_target": "5k",
    "has_target_event": False,
    "total_weeks": 12,
}
NOW = datetime(2026, 10, 20, tzinfo=UTC)


@pytest.fixture
def api(monkeypatch):
    st = {"plan": dict(PLAN), "rows": [], "calls": []}
    monkeypatch.setattr(main, "get_active_plan", lambda uid: st["plan"])
    monkeypatch.setattr(main, "get_plan_workouts", lambda pid: [])
    monkeypatch.setattr(main, "get_recent_plans", lambda uid, limit=3: [{"id": 5}] if uid == 7 else [])
    monkeypatch.setattr(main.db, "get_plan_by_id", lambda pid: st["plan"] if pid == 5 else None)
    monkeypatch.setattr(main.db, "get_plan_milestone_rows", lambda pid: st["rows"])

    def manual(pid, key):
        st["rows"][:] = [r for r in st["rows"] if r["milestone_key"] != key]
        st["rows"].append({"milestone_key": key, "source": "manual", "achieved_at": NOW})

    def revoke(pid, key):
        st["rows"][:] = [r for r in st["rows"] if r["milestone_key"] != key]
        st["rows"].append({"milestone_key": key, "source": "revoked", "achieved_at": None})

    st["jog"] = []
    monkeypatch.setattr(main.db, "set_max_continuous_jog_min", lambda uid, m: st["jog"].append(m) or True)

    def set_target(pid, target, weeks=None, clear_event=False, race_name=None, race_date=None):
        st["calls"].append((target, weeks, clear_event))
        st["ends"] = (race_name, race_date)
        st["plan"].update(milestone_target=target, total_weeks=weeks or st["plan"]["total_weeks"])
        if clear_event:
            st["plan"]["has_target_event"] = False

    monkeypatch.setattr(main.db, "set_milestone_manual", manual)
    monkeypatch.setattr(main.db, "revoke_milestone", revoke)
    monkeypatch.setattr(main.db, "set_plan_milestone_target", set_target)
    main.app.dependency_overrides[main.get_current_user] = lambda: {"id": 7}
    yield st
    main.app.dependency_overrides.pop(main.get_current_user, None)


def _items(resp):
    return {i["key"]: i for i in resp.json()["beginner_milestones"]["items"]}


def test_active_plan_includes_milestones_for_target_plan(api):
    r = client.get("/api/coach/active-plan")
    ms = r.json()["plan"]["beginner_milestones"]
    assert ms["target"] == "5k" and ms["next_key"] == "first_session" and len(ms["items"]) == 6


def test_active_plan_milestones_null_for_legacy_plan(api):
    api["plan"]["milestone_target"] = None
    assert client.get("/api/coach/active-plan").json()["plan"]["beginner_milestones"] is None


def test_post_milestone_marks_manual(api):
    r = client.post("/api/plans/5/milestones/jog_5")
    assert r.status_code == 200 and _items(r)["jog_5"]["source"] == "manual"


def test_post_unknown_key_400(api):
    assert client.post("/api/plans/5/milestones/first_10k").status_code == 400


def test_other_users_plan_404(api):
    main.app.dependency_overrides[main.get_current_user] = lambda: {"id": 99}
    assert client.post("/api/plans/5/milestones/jog_5").status_code == 404


def test_delete_then_refresh_stays_revoked(api, monkeypatch):
    client.post("/api/plans/5/milestones/jog_5")
    r = client.delete("/api/plans/5/milestones/jog_5")
    assert _items(r)["jog_5"]["achieved_at"] is None and _items(r)["jog_5"]["source"] == "revoked"
    # a later sync finds the same completed workout: the real insert is a no-op on a revoked row
    from services import beginner_milestones as bm

    found = bm.evaluate(
        "5k",
        __import__("datetime").date(2026, 10, 5),
        [{"id": 1, "week_number": 1, "type": "Easy Run", "duration_minutes": 10}],
        [],
        {"jog_5"},
    )
    assert "jog_5" not in {a.key for a in found}


def test_patch_target_5k_to_10k_extends_weeks(api):
    r = client.patch("/api/plans/5/milestone-target", json={"target": "10k"})
    assert r.status_code == 200 and api["calls"] == [("10k", 22, False)]
    assert r.json()["plan"]["beginner_milestones"]["target"] == "10k"


def test_patch_target_with_event_keeps_weeks(api):
    api["plan"]["has_target_event"] = True
    client.patch("/api/plans/5/milestone-target", json={"target": "10k"})
    assert api["calls"] == [("10k", None, False)]


def test_patch_target_clear_event_extends_weeks(api):
    api["plan"]["has_target_event"] = True
    client.patch("/api/plans/5/milestone-target", json={"target": "10k", "clear_event": True})
    assert api["calls"] == [("10k", 22, True)]


def test_patch_target_10k_to_5k_400(api):
    api["plan"]["milestone_target"] = "10k"
    assert client.patch("/api/plans/5/milestone-target", json={"target": "5k"}).status_code == 400


def test_manual_tick_raises_the_jog_ceiling(api):
    client.post("/api/plans/5/milestones/jog_5")
    assert api["jog"] == [5]
    client.post("/api/plans/5/milestones/first_session")  # not a jog milestone
    assert api["jog"] == [5]


def test_upgrade_without_event_moves_the_end_date_and_name(api):
    api["plan"].update(start_date="2026-10-05", race_name="First 5K", race_date="2026-12-21")
    client.patch("/api/plans/5/milestone-target", json={"target": "10k"})
    assert api["ends"] == ("First 10K", "2027-03-01")  # start + 21 weeks


def test_upgrade_keeping_event_leaves_name_and_date(api):
    api["plan"].update(start_date="2026-10-05", has_target_event=True)
    client.patch("/api/plans/5/milestone-target", json={"target": "10k"})
    assert api["ends"] == (None, None)
