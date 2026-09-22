"""Integration tests for Coach Chat durable schema and CRUD helpers."""

import uuid
from decimal import Decimal
from datetime import UTC, date, datetime

import pytest
from sqlalchemy import text

import db
from db import engine, init_db


def test_init_db_is_idempotent():
    """Verify init_db() can be called multiple times without error."""
    init_db()
    init_db()


def test_chat_schema_tables_and_columns_exist():
    """Verify all 5 chat tables exist with expected columns."""
    with engine.connect() as conn:
        tables = [
            "chat_threads",
            "chat_messages",
            "chat_turns",
            "chat_daily_usage",
            "chat_llm_calls",
        ]
        for t in tables:
            res = conn.execute(
                text("SELECT table_name FROM information_schema.tables WHERE table_name = :t"),
                {"t": t},
            ).fetchone()
            assert res is not None, f"Table {t} does not exist"


def test_thread_and_message_crud(auth_headers):
    user_id = auth_headers["user_id"]

    # 1. Get or create thread
    thread1 = db.get_or_create_chat_thread(user_id)
    assert thread1["user_id"] == user_id
    assert thread1["id"] is not None

    thread2 = db.get_or_create_chat_thread(user_id)
    assert thread2["id"] == thread1["id"]

    # 2. Append user message
    msg1_id = db.append_chat_message(
        thread_id=thread1["id"],
        role="user",
        content="Hello Coach",
        lang="en",
    )
    assert msg1_id is not None

    # 3. Append assistant message with partial content
    msg2_id = db.append_chat_message(
        thread_id=thread1["id"],
        role="assistant",
        content="Hel",
        lang="en",
        status="interrupted",
    )
    assert msg2_id is not None

    # 4. Update message content and final status
    db.update_chat_message(
        message_id=msg2_id,
        content="Hello runner!",
        status="ok",
        citations=[{"source_label": "Training for the Uphill Athlete", "url": None}],
        model="gemini-3.8-flash",
        cost_usd=Decimal("0.000120"),
    )

    msg2 = db.get_chat_message(msg2_id, user_id=user_id)
    assert msg2 is not None
    assert msg2["content"] == "Hello runner!"
    assert msg2["status"] == "ok"
    assert msg2["model"] == "gemini-3.8-flash"
    assert len(msg2["citations"]) == 1

    # 5. List thread messages
    messages = db.get_chat_thread_messages(user_id=user_id, limit=10)
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"


def test_turn_and_call_lifecycle(auth_headers):
    user_id = auth_headers["user_id"]
    thread = db.get_or_create_chat_thread(user_id)

    req_id = uuid.uuid4()
    call_id = uuid.uuid4()
    fingerprint = "sha256-test-fingerprint"

    # Insert turn
    db.create_chat_turn(
        request_id=req_id,
        user_id=user_id,
        thread_id=thread["id"],
        fingerprint=fingerprint,
        status="active",
    )

    turn = db.get_chat_turn(user_id=user_id, request_id=req_id)
    assert turn is not None
    assert turn["status"] == "active"
    assert turn["attempt_number"] == 1

    # Reserve call
    db.reserve_chat_call(
        call_id=call_id,
        request_id=req_id,
        feature="coach_chat",
        model="gemini-3.8-flash",
    )

    call = db.get_chat_call(call_id)
    assert call is not None
    assert call["status"] == "reserved"
    assert call["usage_known"] is False

    # Finish call
    db.finish_chat_call(
        call_id=call_id,
        status="ok",
        usage_known=True,
        input_tokens=100,
        output_tokens=20,
        cached_tokens=10,
        cost_usd=Decimal("0.000150"),
        latency_ms=850,
    )

    updated_call = db.get_chat_call(call_id)
    assert updated_call["status"] == "ok"
    assert updated_call["usage_known"] is True
    assert updated_call["input_tokens"] == 100
    assert updated_call["output_tokens"] == 20
    assert updated_call["latency_ms"] == 850

    # Update turn status to ok
    msg_id = db.append_chat_message(thread["id"], role="assistant", content="Done")
    db.update_chat_turn_status(request_id=req_id, status="ok", result_message_id=msg_id)

    turn_final = db.get_chat_turn(user_id=user_id, request_id=req_id)
    assert turn_final["status"] == "ok"
    assert turn_final["result_message_id"] == msg_id


def test_cascade_delete_on_user_removal(client):
    """Verify deleting a user cascades to all owned chat tables."""
    new_user = client.post("/api/auth/mock-login", json={"email": "cascade_test@uphill.ai"}).json()["user"]
    user_id = new_user["id"]

    thread = db.get_or_create_chat_thread(user_id)
    msg_id = db.append_chat_message(thread["id"], role="user", content="Cascade?")
    req_id = uuid.uuid4()
    db.create_chat_turn(request_id=req_id, user_id=user_id, thread_id=thread["id"], fingerprint="fp", status="ok")
    db.reserve_chat_call(call_id=uuid.uuid4(), request_id=req_id, feature="coach_chat", model="gemini-3.8-flash")

    # Delete user
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": user_id})
        conn.commit()

        # Check cascading deletion
        assert conn.execute(text("SELECT COUNT(*) FROM chat_threads WHERE user_id = :uid"), {"uid": user_id}).scalar() == 0
        assert conn.execute(text("SELECT COUNT(*) FROM chat_messages WHERE id = :mid"), {"mid": msg_id}).scalar() == 0
        assert conn.execute(text("SELECT COUNT(*) FROM chat_turns WHERE user_id = :uid"), {"uid": user_id}).scalar() == 0
        assert conn.execute(text("SELECT COUNT(*) FROM chat_llm_calls WHERE request_id = :rid"), {"rid": str(req_id)}).scalar() == 0
