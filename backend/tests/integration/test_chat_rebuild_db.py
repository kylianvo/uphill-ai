import datetime as dt

from sqlalchemy import text

import db
from tests.integration.calendar_helpers import add_workout, make_plan, match_activity, this_monday

TODAY = dt.datetime.now(dt.UTC).date()


def _new(uid, *, week=2, limit=5, thread=None, plan_id=None):
    plan_id = plan_id or make_plan(uid, start_date=this_monday())
    thread = thread or db.get_or_create_chat_thread(uid)
    outcome, pid = db.create_rebuild_proposal(
        user_id=uid,
        thread_id=thread["id"],
        plan_id=plan_id,
        week=week,
        operations={"week": week, "from_day": "Monday", "replaceable_ids": []},
        fingerprints={},
        rationale="tired",
        daily_limit=limit,
        usage_date=TODAY,
    )
    return outcome, pid, plan_id, thread


def _draft_workout(day, title="New Easy"):
    return {
        "week_number": 2,
        "day_of_week": day,
        "phase": "Base",
        "title": title,
        "type": "Easy",
        "duration_minutes": 40,
        "target_zone": "Zone 2",
        "description": "d",
    }


def test_replace_week_workouts_deletes_exactly_the_listed_ids(auth_headers):
    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    keep = add_workout(plan_id, 2, "Monday", title="Keep me")
    gone = add_workout(plan_id, 2, "Tuesday", title="Replace me")
    matched = add_workout(plan_id, 2, "Wednesday", title="Matched")
    match_activity(uid, matched)
    with db.engine.begin() as conn:
        db.replace_week_workouts(conn, plan_id, [gone], [_draft_workout("Tuesday"), _draft_workout("Friday")])
    titles = {(w["day_of_week"], w["title"]) for w in db.get_plan_workouts(plan_id) if w["week_number"] == 2}
    assert ("Monday", "Keep me") in titles and ("Wednesday", "Matched") in titles
    assert ("Tuesday", "Replace me") not in titles
    assert ("Tuesday", "New Easy") in titles and ("Friday", "New Easy") in titles
    assert db.get_workout_by_id(keep)["title"] == "Keep me"


def test_save_workouts_still_inserts_the_same_rows(auth_headers):
    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    db.save_workouts(plan_id, [_draft_workout("Thursday", title="Via save")])
    row = next(w for w in db.get_plan_workouts(plan_id) if w["title"] == "Via save")
    assert row["session_slot"] == "main" and row["approved_at"] is not None and row["treadmill_speed"] == "0"


def test_create_rebuild_proposal_counts_dedupes_and_caps(auth_headers):
    uid = auth_headers["user_id"]
    outcome, pid, plan_id, thread = _new(uid, week=2, limit=2)
    assert outcome == "created"
    row = db.get_chat_proposal(pid)
    assert row["kind"] == "rebuild" and row["status"] == "generating"
    # same week while open -> duplicate, no cap consumed
    assert _new(uid, week=2, limit=2, thread=thread, plan_id=plan_id)[:2] == ("duplicate", pid)
    assert _new(uid, week=3, limit=2, thread=thread, plan_id=plan_id)[0] == "created"
    # third distinct request exceeds the cap of 2
    assert _new(uid, week=4, limit=2, thread=thread, plan_id=plan_id)[:2] == ("limit", None)


def test_clearing_the_thread_does_not_reset_the_cap(auth_headers):
    uid = auth_headers["user_id"]
    _, _, plan_id, _ = _new(uid, week=2, limit=1)
    db.clear_chat_thread(uid)
    thread = db.get_or_create_chat_thread(uid)
    assert _new(uid, week=3, limit=1, thread=thread, plan_id=plan_id)[0] == "limit"


def test_finish_and_fail_only_move_generating_rows(auth_headers):
    uid = auth_headers["user_id"]
    _, pid, _, _ = _new(uid)
    assert db.finish_rebuild_proposal(pid, draft={"workouts": []}, diff={"days": []}, warnings=[]) is True
    row = db.get_chat_proposal(pid)
    assert row["status"] == "proposed" and row["draft"] == {"workouts": []} and row["diff"] == {"days": []}
    assert db.fail_rebuild_proposal(pid, "generation_error") is False  # already proposed
    assert db.get_chat_proposal(pid)["status"] == "proposed"


def test_discard_while_generating_wins_over_a_late_finish(auth_headers):
    uid = auth_headers["user_id"]
    _, pid, _, _ = _new(uid)
    assert db.discard_chat_proposal(pid, uid) == "discarded"
    assert db.finish_rebuild_proposal(pid, draft={"workouts": []}, diff={}, warnings=[]) is False
    assert db.get_chat_proposal(pid)["status"] == "discarded"


def test_orphaned_generating_rows_expire_to_failed(auth_headers):
    uid = auth_headers["user_id"]
    _, pid, _, _ = _new(uid)
    _, fresh, _, _ = _new(uid, week=3)
    with db.engine.connect() as conn:
        conn.execute(
            text("UPDATE chat_proposals SET created_at = NOW() - INTERVAL '10 minutes' WHERE id = :id"), {"id": pid}
        )
        conn.commit()
    db.expire_orphaned_rebuilds(uid)
    old = db.get_chat_proposal(pid)
    assert old["status"] == "failed" and old["stale_reason"] == "generation_orphaned"
    assert db.get_chat_proposal(fresh)["status"] == "generating"


def test_get_chat_proposal_for_user_is_owner_scoped(auth_headers):
    uid = auth_headers["user_id"]
    _, pid, _, _ = _new(uid)
    other = db.create_or_get_user("rebuild-other@uphill.ai", "Other", "mock", "mock-rebuild-other")
    assert db.get_chat_proposal_for_user(pid, uid)["id"] == pid
    assert db.get_chat_proposal_for_user(pid, other["id"]) is None


def test_statuses_include_kind(auth_headers):
    uid = auth_headers["user_id"]
    _, pid, _, thread = _new(uid)
    mid = db.append_chat_message(thread["id"], "assistant", "drafting")
    db.set_proposals_message_id(thread["id"], [pid], mid)
    assert db.get_chat_proposal_statuses(uid, [mid])[pid]["kind"] == "rebuild"
