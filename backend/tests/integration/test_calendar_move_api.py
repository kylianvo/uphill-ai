"""Integration tests for POST /api/coach/calendar/move."""

import datetime as dt

import db
from tests.integration.calendar_helpers import add_workout, make_plan, match_activity, this_monday

TODAY = dt.datetime.now(dt.UTC).date()


def _post(client, auth_headers, plan_id, ops):
    return client.post(
        "/api/coach/calendar/move",
        headers=auth_headers["headers"],
        json={"plan_id": plan_id, "operations": ops, "client_today": TODAY.isoformat()},
    )


def test_move_one_workout_to_next_week(client, auth_headers):
    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    wid = add_workout(plan_id, 1, "Sunday")  # week 1 Sunday is always today-or-later
    target_week = 2
    resp = _post(
        client, auth_headers, plan_id, [{"workout_id": wid, "target_week": target_week, "target_day": "Thursday"}]
    )
    assert resp.status_code == 200, resp.text
    moved = next(w for w in resp.json()["workouts"] if w["id"] == wid)
    assert (moved["week_number"], moved["day_of_week"]) == (target_week, "Thursday")
    assert isinstance(resp.json()["warnings"], list)


def test_move_refused_with_guard_code(client, auth_headers):
    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    wid = add_workout(plan_id, 2, "Tuesday")
    match_activity(uid, wid)
    resp = _post(client, auth_headers, plan_id, [{"workout_id": wid, "target_week": 2, "target_day": "Friday"}])
    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "G2_history"
    assert db.get_workout_by_id(wid)["day_of_week"] == "Tuesday"


def test_move_on_someone_elses_plan_is_403(client, auth_headers):
    other = db.create_or_get_user("other-move@uphill.ai", "Other", "mock", "mock-other-move")
    plan_id = make_plan(other["id"], start_date=this_monday())
    wid = add_workout(plan_id, 2, "Tuesday")
    resp = _post(client, auth_headers, plan_id, [{"workout_id": wid, "target_week": 2, "target_day": "Friday"}])
    assert resp.status_code == 403


def test_move_requires_one_to_five_operations(client, auth_headers):
    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    resp = _post(client, auth_headers, plan_id, [])
    assert resp.status_code == 422
