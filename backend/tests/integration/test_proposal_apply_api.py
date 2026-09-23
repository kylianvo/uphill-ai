import datetime as dt
from concurrent.futures import ThreadPoolExecutor

import db
from services import calendar_ops, schedule_proposals
from tests.integration.calendar_helpers import add_workout, link_coach, make_plan, match_activity, this_monday

TODAY = dt.datetime.now(dt.UTC).date()


def _proposal(uid, plan_id, wid, day="Friday", week=2):
    op = [{"op": "move", "workout_id": wid, "target_week": week, "target_day": day}]
    changes = calendar_ops.preview(uid, plan_id, op, TODAY, agent=True)
    thread = db.get_or_create_chat_thread(uid)
    pid = db.create_chat_proposal(
        user_id=uid,
        thread_id=thread["id"],
        plan_id=plan_id,
        operations=op,
        fingerprints=changes.fingerprints,
        diff=changes.diff,
        warnings=changes.warnings,
        rationale="r",
    )
    mid = db.append_chat_message(thread["id"], "assistant", "proposal")
    db.set_proposals_message_id(thread["id"], [pid], mid)
    return pid


def _apply(client, auth_headers, pid):
    return client.post(
        f"/api/coach/chat/proposals/{pid}/apply",
        headers=auth_headers["headers"],
        json={"client_today": TODAY.isoformat()},
    )


def _setup(auth_headers):
    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    wid = add_workout(plan_id, 2, "Tuesday")
    return uid, plan_id, wid


def test_apply_happy_path_and_duplicate_is_idempotent(client, auth_headers):
    uid, plan_id, wid = _setup(auth_headers)
    pid = _proposal(uid, plan_id, wid)
    first = _apply(client, auth_headers, pid)
    assert first.status_code == 200, first.text
    assert first.json()["status"] == "applied"
    assert any(w["id"] == wid and w["day_of_week"] == "Friday" for w in first.json()["workouts"])
    second = _apply(client, auth_headers, pid)
    assert second.status_code == 200
    assert second.json()["result"] == first.json()["result"]


def test_concurrent_applies_write_once(auth_headers):
    uid, plan_id, wid = _setup(auth_headers)
    pid = _proposal(uid, plan_id, wid)
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: schedule_proposals.apply_proposal(uid, pid, TODAY.isoformat()), range(2)))
    assert [o[0] for o in outcomes] == [200, 200]
    assert outcomes[0][1]["result"] == outcomes[1][1]["result"]
    assert db.get_chat_proposal(pid)["status"] == "applied"


def test_stale_when_the_workout_moved_since(client, auth_headers):
    uid, plan_id, wid = _setup(auth_headers)
    pid = _proposal(uid, plan_id, wid)
    calendar_ops.apply(
        uid,
        plan_id,
        [{"op": "move", "workout_id": wid, "target_week": 2, "target_day": "Wednesday"}],
        TODAY,
        agent=False,
    )
    resp = _apply(client, auth_headers, pid)
    assert resp.status_code == 409
    assert resp.json() == {"status": "stale", "stale_reason": "STALE_changed"}
    assert db.get_workout_by_id(wid)["day_of_week"] == "Wednesday"


def test_stale_when_matched_since(client, auth_headers):
    uid, plan_id, wid = _setup(auth_headers)
    pid = _proposal(uid, plan_id, wid)
    match_activity(uid, wid)
    resp = _apply(client, auth_headers, pid)
    assert resp.status_code == 409 and resp.json()["stale_reason"] == "G2_history"


def test_stale_when_coach_linked_since(client, auth_headers):
    uid, plan_id, wid = _setup(auth_headers)
    pid = _proposal(uid, plan_id, wid)
    link_coach(uid)
    resp = _apply(client, auth_headers, pid)
    assert resp.status_code == 409 and resp.json()["stale_reason"] == "G6_coach_linked"


def test_bogus_client_today_is_clamped_to_server_date(client, auth_headers):
    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    wid = add_workout(plan_id, 2, "Tuesday")
    pid = _proposal(uid, plan_id, wid)
    tomorrow_plus_8 = (TODAY + dt.timedelta(days=9)).isoformat()  # far outside the +-1 clamp -> server today used
    resp = client.post(
        f"/api/coach/chat/proposals/{pid}/apply",
        headers=auth_headers["headers"],
        json={"client_today": tomorrow_plus_8},
    )
    assert resp.status_code == 200  # clamp ignores the bogus client date; target is still in the future


def test_other_users_proposal_is_404_and_discard_is_idempotent(client, auth_headers):
    uid, plan_id, wid = _setup(auth_headers)
    pid = _proposal(uid, plan_id, wid)
    other = client.post("/api/auth/mock-login", json={"email": "someone-else@uphill.ai"}).json()
    other_headers = {"Authorization": f"Bearer {other['session_token']}"}
    assert client.post(f"/api/coach/chat/proposals/{pid}/apply", headers=other_headers, json={}).status_code == 404
    assert client.post(f"/api/coach/chat/proposals/{pid}/discard", headers=other_headers).status_code == 404
    d1 = client.post(f"/api/coach/chat/proposals/{pid}/discard", headers=auth_headers["headers"])
    d2 = client.post(f"/api/coach/chat/proposals/{pid}/discard", headers=auth_headers["headers"])
    assert d1.json() == d2.json() == {"status": "discarded"}
    assert _apply(client, auth_headers, pid).status_code == 409


def test_thread_load_includes_live_proposal_status(client, auth_headers):
    uid, plan_id, wid = _setup(auth_headers)
    pid = _proposal(uid, plan_id, wid)
    _apply(client, auth_headers, pid)
    data = client.get("/api/coach/chat/thread", headers=auth_headers["headers"]).json()
    assert data["proposals"][str(pid)]["status"] == "applied"
