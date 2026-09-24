import json

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

import db
from tests.integration.calendar_helpers import make_plan, this_monday


def _insert(uid, thread_id, plan_id, **cols):
    base = {"kind": "rebuild", "status": "generating"}
    base.update(cols)
    with db.engine.connect() as conn:
        pid = conn.execute(
            text(
                """
                INSERT INTO chat_proposals (user_id, thread_id, plan_id, kind, status, operations, fingerprints, diff)
                VALUES (:uid, :tid, :pid, :kind, :status, '{}'::jsonb, '{}'::jsonb, '{}'::jsonb)
                RETURNING id
                """
            ),
            {"uid": uid, "tid": thread_id, "pid": plan_id, **base},
        ).scalar()
        conn.commit()
    return pid


def test_rebuild_kind_and_new_statuses_are_accepted(auth_headers):
    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    thread = db.get_or_create_chat_thread(uid)
    for status in ("generating", "failed"):
        pid = _insert(uid, thread["id"], plan_id, status=status)
        row = db.get_chat_proposal(pid)
        assert row["kind"] == "rebuild" and row["status"] == status and row["draft"] is None


def test_existing_4a_insert_defaults_to_schedule_kind(auth_headers):
    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    thread = db.get_or_create_chat_thread(uid)
    pid = db.create_chat_proposal(
        user_id=uid,
        thread_id=thread["id"],
        plan_id=plan_id,
        operations=[],
        fingerprints={},
        diff=[],
        warnings=[],
        rationale=None,
    )
    assert db.get_chat_proposal(pid)["kind"] == "schedule"


def test_unknown_kind_and_status_are_rejected(auth_headers):
    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    thread = db.get_or_create_chat_thread(uid)
    with pytest.raises(IntegrityError):
        _insert(uid, thread["id"], plan_id, kind="rewrite")
    with pytest.raises(IntegrityError):
        _insert(uid, thread["id"], plan_id, status="queued")


def test_draft_column_round_trips_and_rebuilds_count_defaults_to_zero(auth_headers):
    uid = auth_headers["user_id"]
    plan_id = make_plan(uid, start_date=this_monday())
    thread = db.get_or_create_chat_thread(uid)
    pid = _insert(uid, thread["id"], plan_id)
    with db.engine.connect() as conn:
        conn.execute(
            text("UPDATE chat_proposals SET draft = CAST(:d AS JSONB) WHERE id = :id"),
            {"d": json.dumps({"workouts": [], "resolved_tier": "recreational"}), "id": pid},
        )
        conn.execute(
            text(
                "INSERT INTO chat_daily_usage (usage_date, user_id) VALUES (CURRENT_DATE, :uid) "
                "ON CONFLICT (usage_date, user_id) DO NOTHING"
            ),
            {"uid": uid},
        )
        count = conn.execute(
            text("SELECT rebuilds_count FROM chat_daily_usage WHERE usage_date = CURRENT_DATE AND user_id = :uid"),
            {"uid": uid},
        ).scalar()
        conn.commit()
    assert db.get_chat_proposal(pid)["draft"] == {"workouts": [], "resolved_tier": "recreational"}
    assert count == 0
