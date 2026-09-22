"""Integration tests for conversation retention, pruning, and thread clearing."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest

import db
from db import prune_coach_chat


def test_retention_prune_deletes_91_day_messages_and_keeps_89_day(auth_headers):
    user_id = auth_headers["user_id"]
    thread = db.get_or_create_chat_thread(user_id)
    now = datetime.now(UTC)

    # 1. Insert message created 91 days ago (expired)
    old_time = now - timedelta(days=91)
    with db.engine.connect() as conn:
        res1 = conn.execute(
            db.text("""
                INSERT INTO chat_messages (thread_id, role, content, lang, status, created_at)
                VALUES (:tid, 'user', '91 days old', 'en', 'ok', :ts)
                RETURNING id
            """),
            {"tid": thread["id"], "ts": old_time},
        )
        old_msg_id = res1.scalar()

        # 2. Insert message created 89 days ago (retained)
        recent_time = now - timedelta(days=89)
        res2 = conn.execute(
            db.text("""
                INSERT INTO chat_messages (thread_id, role, content, lang, status, created_at)
                VALUES (:tid, 'assistant', '89 days old', 'en', 'ok', :ts)
                RETURNING id
            """),
            {"tid": thread["id"], "ts": recent_time},
        )
        recent_msg_id = res2.scalar()
        conn.commit()

    # 3. Run pruning
    stats = prune_coach_chat(now=now, batch_size=100)
    assert stats["deleted_messages"] >= 1

    # 4. Old message is physically deleted, recent message is kept
    assert db.get_chat_message(old_msg_id) is None
    assert db.get_chat_message(recent_msg_id) is not None


def test_retention_prune_clears_expired_summaries(auth_headers):
    user_id = auth_headers["user_id"]
    thread = db.get_or_create_chat_thread(user_id)
    now = datetime.now(UTC)
    old_time = now - timedelta(days=95)

    with db.engine.connect() as conn:
        res = conn.execute(
            db.text("""
                INSERT INTO chat_messages (thread_id, role, content, lang, status, created_at)
                VALUES (:tid, 'user', 'Deleted msg', 'en', 'ok', :ts)
                RETURNING id
            """),
            {"tid": thread["id"], "ts": old_time},
        )
        deleted_msg_id = res.scalar()
        conn.execute(
            db.text("""
                UPDATE chat_threads
                SET summary = 'Old summary from deleted message',
                    summarized_through_id = :mid,
                    updated_at = :ts
                WHERE id = :tid
            """),
            {"mid": deleted_msg_id, "ts": old_time, "tid": thread["id"]},
        )
        conn.commit()

    # Pruning deletes message and resets dangling summary
    prune_coach_chat(now=now)

    updated_thread = db.get_or_create_chat_thread(user_id)
    assert updated_thread["summary"] is None
    assert updated_thread["summarized_through_id"] is None


def test_clear_preserves_counters_and_calls(client, auth_headers):
    user_id = auth_headers["user_id"]
    headers = auth_headers["headers"]
    thread = db.get_or_create_chat_thread(user_id)
    req_id = uuid.uuid4()
    call_id = uuid.uuid4()

    # Set up turn, call accounting, and daily usage
    db.admit_chat_turn(request_id=req_id, user_id=user_id, thread_id=thread["id"], message="Hello")
    db.reserve_chat_call(call_id=call_id, request_id=req_id, feature="coach_chat", model="gemini-3.8-flash")
    db.finish_chat_call(call_id=call_id, status="ok", usage_known=True, input_tokens=50, output_tokens=10)

    # Execute clear
    resp = client.delete("/api/coach/chat/thread", headers=headers)
    assert resp.status_code == 200

    # Quotas and call records are preserved
    with db.engine.connect() as conn:
        usage_row = conn.execute(
            db.text("SELECT new_turns_count FROM chat_daily_usage WHERE user_id = :uid"),
            {"uid": user_id},
        ).fetchone()
        assert usage_row[0] >= 1

        call_row = conn.execute(
            db.text("SELECT status FROM chat_llm_calls WHERE call_id = :cid"),
            {"cid": call_id},
        ).fetchone()
        assert call_row[0] == "ok"


def test_cleared_uuid_returns_410(client, auth_headers):
    user_id = auth_headers["user_id"]
    headers = auth_headers["headers"]
    req_id = uuid.uuid4()

    db.create_chat_turn(
        request_id=req_id,
        user_id=user_id,
        thread_id=None,
        fingerprint="fp-cleared",
        status="cleared",
    )

    resp = client.get(f"/api/coach/chat/turns/{req_id}", headers=headers)
    assert resp.status_code == 410


def test_account_deletion_cascades_chat_tables(client, auth_headers):
    user_id = auth_headers["user_id"]
    thread = db.get_or_create_chat_thread(user_id)
    req_id = uuid.uuid4()
    call_id = uuid.uuid4()

    db.append_chat_message(thread["id"], "user", "Cascaded message")
    db.create_chat_turn(request_id=req_id, user_id=user_id, thread_id=thread["id"], fingerprint="fp-cascade")
    db.reserve_chat_call(call_id=call_id, request_id=req_id, feature="coach_chat", model="gemini-3.8-flash")

    # Delete the user row
    with db.engine.connect() as conn:
        conn.execute(db.text("DELETE FROM users WHERE id = :uid"), {"uid": user_id})
        conn.commit()

        # All child chat rows must be cascaded
        assert conn.execute(db.text("SELECT COUNT(*) FROM chat_threads WHERE user_id = :uid"), {"uid": user_id}).scalar() == 0
        assert conn.execute(db.text("SELECT COUNT(*) FROM chat_messages WHERE thread_id = :tid"), {"tid": thread["id"]}).scalar() == 0
        assert conn.execute(db.text("SELECT COUNT(*) FROM chat_turns WHERE user_id = :uid"), {"uid": user_id}).scalar() == 0
        assert conn.execute(db.text("SELECT COUNT(*) FROM chat_llm_calls WHERE call_id = :cid"), {"cid": call_id}).scalar() == 0
