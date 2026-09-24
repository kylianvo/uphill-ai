import db
from tests.integration.calendar_helpers import add_workout, make_plan, match_activity, this_monday


def _proposal(user_id, plan_id):
    thread = db.get_or_create_chat_thread(user_id)
    pid = db.create_chat_proposal(
        user_id=user_id,
        thread_id=thread["id"],
        plan_id=plan_id,
        operations=[{"op": "move", "workout_id": 1, "target_week": 1, "target_day": "Friday"}],
        fingerprints={"1": {"id": 1}},
        diff=[{"workout_id": 1}],
        warnings=[{"code": "W3_pending_draft", "params": {}}],
        rationale="travel",
    )
    return thread, pid


def test_create_and_lock_round_trip(auth_headers):
    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    thread, pid = _proposal(uid, plan_id)
    with db.engine.begin() as conn:
        row = db.lock_chat_proposal(conn, pid, uid)
        assert row["status"] == "proposed"
        assert row["operations"][0]["target_day"] == "Friday"
        assert row["fingerprints"] == {"1": {"id": 1}}
        assert db.lock_chat_proposal(conn, pid, uid + 999) is None
        db.resolve_chat_proposal(conn, pid, status="applied", result={"warnings": []})
    stored = db.get_chat_proposal(pid)
    assert stored["status"] == "applied" and stored["resolved_at"] is not None
    assert stored["result"] == {"warnings": []}


def test_discard_is_owner_only_and_idempotent(auth_headers):
    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    _, pid = _proposal(uid, plan_id)
    assert db.discard_chat_proposal(pid, uid + 999) is None
    assert db.discard_chat_proposal(pid, uid) == "discarded"
    assert db.discard_chat_proposal(pid, uid) == "discarded"


def test_statuses_by_message_and_clear_chat_removes_proposals(auth_headers):
    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    thread, pid = _proposal(uid, plan_id)
    mid = db.append_chat_message(thread["id"], "assistant", "Here's a proposal.")
    db.set_proposals_message_id(thread["id"], [pid], mid)
    assert db.get_chat_proposal_statuses(uid, [mid]) == {
        pid: {"status": "proposed", "stale_reason": None, "result": None, "kind": "schedule"}
    }
    _, orphan = _proposal(uid, plan_id)  # never attached to a message
    db.clear_chat_thread(user_id=uid)
    assert db.get_chat_proposal(pid) is None
    assert db.get_chat_proposal(orphan) is None


def test_placement_snapshot_and_moves(auth_headers):
    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    a = add_workout(plan_id, 1, "Thursday", missed=1)
    b = add_workout(plan_id, 1, "Friday")
    match_activity(uid, b)
    with db.engine.begin() as conn:
        rows = {r["id"]: r for r in db.get_plan_workouts_for_placement(conn, plan_id, lock=True)}
        assert rows[a]["matched_activity_id"] is None
        assert rows[b]["matched_activity_id"] is not None
        db.apply_workout_moves(
            conn, [{"workout_id": a, "from_week": 1, "from_day": "Thursday", "to_week": 2, "to_day": "Monday"}]
        )
    moved = db.get_workout_by_id(a)
    assert (moved["week_number"], moved["day_of_week"], moved["is_missed"]) == (2, "Monday", 0)
