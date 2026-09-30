"""Live quality signals that need the database: goal outcomes, plan generation traces,
and result feedback tokens."""

import datetime as dt

import db
from config import settings
from services import goal_outcomes, observability, plan_signals, quality_signals, race_history
from tests.integration.calendar_helpers import add_workout, make_plan, this_monday

TRACE_A = "a" * 32
TRACE_B = "b" * 32


def _record_scores(monkeypatch):
    calls = []
    monkeypatch.setattr(observability, "score", lambda **kw: calls.append(kw))
    return calls


def _assessment(uid, plan_id, race_date, trace_id=TRACE_A):
    return db.insert_goal_assessment(
        {
            "user_id": uid,
            "plan_id": plan_id,
            "race_name": "Regional 50K",
            "race_date": race_date,
            "distance_km": 50,
            "elevation_gain_m": 2500,
            "input_hash": "h",
            "context_summary": {},
            "anchors": [],
            "output": {"goals": {"a": 360, "b": 400, "c": 450}, "confidence": "medium"},
            "engine": "gemini",
            "confidence": "medium",
            "lang": "en",
            "trigger": "manual",
            "plan_week": 1,
            "trace_id": trace_id,
        }
    )


def test_a_manual_race_result_resolves_and_scores_the_goal(auth_headers, monkeypatch):
    calls = _record_scores(monkeypatch)
    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    assessment = _assessment(uid, plan_id, "2026-06-14")

    race_history.create_manual(
        uid,
        {
            "discipline": "trail",
            "race_name": "Regional 50K",
            "race_date": dt.date(2026, 6, 15),
            "distance_km": 51.0,
            "elevation_gain_m": 2500,
            "finish_time_sec": 410 * 60,
            "is_dnf": False,
            "rank_overall": None,
            "total_overall": None,
        },
    )

    assert db.latest_goal_assessment_for_plan(plan_id)["actual_finish_sec"] == 410 * 60
    assert {c["name"]: c["value"] for c in calls} == {"goal_hit": 1, "goal_error": 10 / 410}
    assert all(c["trace_id"] == TRACE_A for c in calls)
    assert goal_outcomes.reconcile(uid) == 0  # already resolved
    assert assessment["id"]


def test_applying_a_goal_records_which_option(client, auth_headers, monkeypatch):
    calls = _record_scores(monkeypatch)
    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    _assessment(uid, plan_id, None)

    goal_outcomes.score_applied(plan_id, 360)

    assert calls[0]["name"] == "goal_applied" and calls[0]["value"] == "ambitious"


def test_plan_generation_scores_rework_then_block_compliance(auth_headers, monkeypatch):
    calls = _record_scores(monkeypatch)
    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    workouts = [{"title": "Easy", "type": "Easy", "target_zone": "Zone 2", "duration_minutes": 45, "week_number": 1}]

    plan_signals.record_generation(plan_id=plan_id, user_id=uid, block_number=1, workouts=workouts, trace_id=TRACE_A)
    plan_signals.record_generation(plan_id=plan_id, user_id=uid, block_number=1, workouts=workouts, trace_id=TRACE_B)
    reworked = [c for c in calls if c["name"] == "plan_reworked"]
    assert reworked == [
        {"trace_id": TRACE_A, "name": "plan_reworked", "value": 1, "score_id": f"plan-reworked-{TRACE_A}"}
    ]

    add_workout(plan_id, 1, "Monday", completed=1)
    add_workout(plan_id, 1, "Wednesday")
    calls.clear()
    plan_signals.record_generation(plan_id=plan_id, user_id=uid, block_number=2, workouts=workouts, trace_id="c" * 32)

    compliance = [c for c in calls if c["name"] == "block_compliance"]
    assert len(compliance) == 1 and compliance[0]["trace_id"] == TRACE_B and 0 < compliance[0]["value"] < 1
    assert db.get_plan_generation_trace(plan_id)["generation_block"] == 2


def test_result_feedback_accepts_only_issued_tokens(client, monkeypatch):
    monkeypatch.setattr(settings, "OBSERVABILITY_ID_SALT", "salt")
    calls = _record_scores(monkeypatch)
    token = quality_signals.feedback_token(TRACE_A, "nutrition_lab")

    ok = client.post("/api/feedback/result", json={"token": token, "value": -1})
    assert ok.status_code == 200, ok.text
    assert calls == [{"trace_id": TRACE_A, "name": "thumbs", "value": -1, "score_id": f"thumbs-{TRACE_A}"}]

    forged = client.post("/api/feedback/result", json={"token": f"{TRACE_B}.nutrition_lab.{'0' * 32}", "value": 1})
    assert forged.status_code == 400
