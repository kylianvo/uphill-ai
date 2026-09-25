"""Goal assessment endpoints (docs/superpowers/specs/2026-09-26-llm-goal-estimation-design.md).
Gemini is never called: GOAL_LLM_ENABLED is off by default, so the rules tier answers,
except where a test patches the judge's model call explicitly."""

import json
from datetime import date, timedelta

import pytest

import db
from config import settings
from services import goal_judge, race_history

RACE_DATE = (date.today() + timedelta(weeks=10)).isoformat()


def _add_result(user_id, **kw):
    data = {
        "discipline": "trail",
        "race_name": "Some Mountain 50K",
        "race_date": (date.today() - timedelta(days=200)).isoformat(),
        "distance_km": 50.0,
        "elevation_gain_m": 2500.0,
        "finish_time_sec": 7 * 3600,
        "is_dnf": False,
        "rank_overall": None,
        "total_overall": None,
        **kw,
    }
    return race_history.create_manual(user_id, data)


def _plan(user_id, weeks_ago=0, target_hours=9.0):
    start = (date.today() - timedelta(weeks=weeks_ago)).isoformat()
    return db.create_plan(
        user_id,
        "Unknown Test Ultra",
        RACE_DATE,
        "time",
        target_hours,
        12,
        course_distance_km=70.0,
        course_elevation_gain_m=3500.0,
        start_date=start,
    )


def _assess(client, headers=None, **body):
    payload = {
        "race_name": "Unknown Test Ultra",
        "distance_km": 70,
        "elevation_gain_m": 3500,
        "race_date": RACE_DATE,
        **body,
    }
    return client.post("/api/goal/assess", json=payload, headers=headers or {})


def test_signed_out_manual_reference(client):
    resp = _assess(client, reference={"distance_km": 50, "elevation_gain_m": 2500, "time": "7:00:00"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["engine"] == "rules"
    assert data["goals"]["a"] < data["goals"]["b"] < data["goals"]["c"]
    assert [a["method"] for a in data["anchors"]] == ["physics"]


def test_signed_out_without_any_data_has_no_goals(client):
    data = _assess(client).json()
    assert data["goals"] is None and data["engine"] == "none"


def test_distance_required(client):
    assert client.post("/api/goal/assess", json={"race_name": "Nowhere"}).status_code == 422


def test_signed_in_uses_history_and_exclusions(client, auth_headers):
    uid = auth_headers["user_id"]
    first = _add_result(uid)
    second = _add_result(uid, race_name="Other Trail 60K", distance_km=60.0, finish_time_sec=9 * 3600)
    data = _assess(client, auth_headers["headers"]).json()
    assert {a["id"] for a in data["anchors"]} == {f"phys_r{first['id']}", f"phys_r{second['id']}"}
    assert {s["key"] for s in data["sources"]} >= {f"result:{first['id']}", f"result:{second['id']}"}

    excluded = _assess(client, auth_headers["headers"], exclude=[f"result:{second['id']}"]).json()
    assert [a["id"] for a in excluded["anchors"]] == [f"phys_r{first['id']}"]
    assert next(s for s in excluded["sources"] if s["key"] == f"result:{second['id']}")["included"] is False


def test_identical_inputs_reuse_stored_row(client, auth_headers):
    _add_result(auth_headers["user_id"])
    first = _assess(client, auth_headers["headers"]).json()
    again = _assess(client, auth_headers["headers"]).json()
    assert again["id"] == first["id"] and again["reused"] is True


def test_llm_answer_is_stored(client, auth_headers, monkeypatch):
    result = _add_result(auth_headers["user_id"])
    monkeypatch.setattr(settings, "GOAL_LLM_ENABLED", True)

    def fake(prompt, key):
        anchors = json.loads(prompt.split("ANCHORS:\n", 1)[1])
        b = anchors[0]["minutes"]
        return json.dumps(
            {
                "goals": {"a": b * 0.95, "b": b, "c": b * 1.08},
                "confidence": "medium",
                "reasoning": ["one", "two", "three"],
                "anchors_weighted": [{"id": anchors[0]["id"], "weight": 1}],
                "missing": ["watch"],
            }
        )

    monkeypatch.setattr(goal_judge, "_call_gemini", fake)
    data = _assess(client, auth_headers["headers"]).json()
    assert data["engine"] == "gemini"
    assert data["reasoning"] == ["one", "two", "three"]
    assert f"phys_r{result['id']}" in [a["id"] for a in data["anchors"]]


def test_plan_goal_status_and_apply(client, auth_headers):
    uid = auth_headers["user_id"]
    _add_result(uid)
    plan_id = _plan(uid, target_hours=20.0)
    headers = auth_headers["headers"]

    empty = client.get(f"/api/plans/{plan_id}/goal", headers=headers).json()
    assert empty["status"]["state"] == "not_assessed"

    reassessed = client.post(f"/api/plans/{plan_id}/goal/reassess", json={}, headers=headers).json()
    assert reassessed["status"]["state"] == "ahead"  # 20 h target vs a ~12 h estimate
    suggested = reassessed["status"]["suggested_mins"]

    applied = client.post(f"/api/plans/{plan_id}/goal/apply", json={"target_mins": suggested}, headers=headers)
    assert applied.status_code == 200
    assert applied.json()["status"]["state"] == "on_track"
    assert db.get_plan_by_id(plan_id)["target_time_hours"] == pytest.approx(suggested / 60, abs=0.001)


def test_manual_reassess_rate_limit(client, auth_headers, monkeypatch):
    uid = auth_headers["user_id"]
    plan_id = _plan(uid)
    headers = auth_headers["headers"]
    for i in range(3):
        _add_result(uid, race_name=f"Race {i}", finish_time_sec=7 * 3600 + i * 60)  # change inputs each time
        assert client.post(f"/api/plans/{plan_id}/goal/reassess", json={}, headers=headers).status_code == 200
    _add_result(uid, race_name="Race 4", finish_time_sec=8 * 3600)
    assert client.post(f"/api/plans/{plan_id}/goal/reassess", json={}, headers=headers).status_code == 429


def test_weekly_reassess_runs_once_per_completed_week(client, auth_headers):
    uid = auth_headers["user_id"]
    _add_result(uid)
    plan_id = _plan(uid, weeks_ago=2)  # current week 3 -> 2 weeks done
    headers = auth_headers["headers"]
    client.get(f"/api/plans/{plan_id}/goal", headers=headers)  # schedules the weekly run (TestClient runs it)
    latest = db.get_latest_goal_assessment(plan_id)
    assert latest["trigger"] == "weekly" and latest["plan_week"] == 2
    client.get(f"/api/plans/{plan_id}/goal", headers=headers)
    assert db.get_latest_goal_assessment(plan_id)["id"] == latest["id"]


def test_plan_goal_is_owner_only(client, auth_headers):
    other = client.post("/api/auth/mock-login", json={"email": "someone-else@uphill.ai"}).json()
    plan_id = _plan(other["user"]["id"])
    assert client.get(f"/api/plans/{plan_id}/goal", headers=auth_headers["headers"]).status_code == 404
    resp = client.post(f"/api/plans/{plan_id}/goal/apply", json={"target_mins": 500}, headers=auth_headers["headers"])
    assert resp.status_code == 404


def test_coach_needs_roster_link(client, auth_headers):
    other = client.post("/api/auth/mock-login", json={"email": "athlete2@uphill.ai"}).json()
    athlete_id = other["user"]["id"]
    plan_id = _plan(athlete_id)
    resp = client.get(f"/api/coaching/athletes/{athlete_id}/plans/{plan_id}/goal", headers=auth_headers["headers"])
    assert resp.status_code == 403


def test_race_history_payload_drops_scenarios(client, auth_headers):
    assert "scenarios" not in client.get("/api/race-history", headers=auth_headers["headers"]).json()
