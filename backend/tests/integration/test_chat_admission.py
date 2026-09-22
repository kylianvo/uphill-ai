"""Integration tests for Coach Chat cross-worker admission, locking, deduplication, and quotas."""

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import text

import db
from db import (
    ChatDailyLimitError,
    ChatInProgressError,
    ChatRequestConflictError,
    ChatRetryLimitError,
    NothingToRetryError,
    admit_chat_turn,
    chat_turn_lock,
    compute_chat_fingerprint,
    engine,
)


def test_chat_turn_lock_contention_same_athlete(auth_headers):
    user_id = auth_headers["user_id"]

    with chat_turn_lock(user_id):
        # Second attempt on same athlete should raise ChatInProgressError
        with pytest.raises(ChatInProgressError) as exc_info:
            with chat_turn_lock(user_id):
                pass
        assert exc_info.value.code == "chat_in_progress"

    # After exiting, lock is released and can be acquired again
    with chat_turn_lock(user_id):
        pass


def test_chat_turn_lock_independent_athletes(client):
    u1 = client.post("/api/auth/mock-login", json={"email": "u1@uphill.ai"}).json()["user"]["id"]
    u2 = client.post("/api/auth/mock-login", json={"email": "u2@uphill.ai"}).json()["user"]["id"]

    with chat_turn_lock(u1):
        # u2 should be able to acquire concurrently
        with chat_turn_lock(u2):
            pass


def test_chat_turn_lock_connection_drop_releases(auth_headers):
    user_id = auth_headers["user_id"]

    # Acquire lock directly on a connection and close connection without explicit unlock
    conn = engine.connect()
    # Namespace is CHAT_ADVISORY_NAMESPACE
    res = conn.execute(
        text("SELECT pg_try_advisory_lock(:ns, :uid)"),
        {"ns": db.CHAT_ADVISORY_NAMESPACE, "uid": user_id},
    ).scalar()
    assert res is True

    # Closing connection drops the session lock
    conn.close()

    # Now chat_turn_lock should succeed immediately
    with chat_turn_lock(user_id):
        pass


def test_fingerprint_deterministic_and_normalized():
    fp1 = compute_chat_fingerprint(message="  Hello Coach  ", retry_of=None, lang="en", is_legacy=False)
    fp2 = compute_chat_fingerprint(message="Hello Coach", retry_of=None, lang="EN", is_legacy=False)
    assert fp1 == fp2

    fp_retry = compute_chat_fingerprint(message=None, retry_of="uuid-1234", lang="vi", is_legacy=False)
    assert fp1 != fp_retry


def test_admit_turn_replay_same_uuid_and_fingerprint(auth_headers):
    user_id = auth_headers["user_id"]
    thread = db.get_or_create_chat_thread(user_id)
    req_id = uuid.uuid4()
    msg = "How do I pace my long run?"

    # First admission -> new turn
    res1 = admit_chat_turn(
        user_id=user_id,
        request_id=req_id,
        thread_id=thread["id"],
        message=msg,
        lang="en",
    )
    assert res1["kind"] == "new"
    assert res1["attempt_number"] == 1

    # Attach result message and mark ok
    msg_id = db.append_chat_message(thread["id"], role="assistant", content="Pace by feel.")
    db.update_chat_turn_status(request_id=req_id, status="ok", result_message_id=msg_id)

    # Replay with same request_id and message
    res2 = admit_chat_turn(
        user_id=user_id,
        request_id=req_id,
        thread_id=thread["id"],
        message=msg,
        lang="en",
    )
    assert res2["kind"] == "replay"
    assert res2["result_message_id"] == msg_id


def test_admit_turn_conflict_same_uuid_different_fingerprint(auth_headers):
    user_id = auth_headers["user_id"]
    thread = db.get_or_create_chat_thread(user_id)
    req_id = uuid.uuid4()

    admit_chat_turn(
        user_id=user_id,
        request_id=req_id,
        thread_id=thread["id"],
        message="Initial question",
        lang="en",
    )

    # Same request_id, different message -> Conflict
    with pytest.raises(ChatRequestConflictError) as exc_info:
        admit_chat_turn(
            user_id=user_id,
            request_id=req_id,
            thread_id=thread["id"],
            message="Different question",
            lang="en",
        )
    assert exc_info.value.code == "request_conflict"


def test_admit_turn_daily_new_turns_quota(auth_headers):
    user_id = auth_headers["user_id"]
    thread = db.get_or_create_chat_thread(user_id)
    today = datetime.now(UTC).date()

    # Pre-seed daily usage to 50
    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO chat_daily_usage (usage_date, user_id, new_turns_count, retries_count)
                VALUES (:d, :uid, 50, 0)
                ON CONFLICT (usage_date, user_id) DO UPDATE SET new_turns_count = 50
            """),
            {"d": today, "uid": user_id},
        )
        conn.commit()

    # 51st new turn should raise ChatDailyLimitError
    with pytest.raises(ChatDailyLimitError) as exc_info:
        admit_chat_turn(
            user_id=user_id,
            request_id=uuid.uuid4(),
            thread_id=thread["id"],
            message="Over the limit",
            lang="en",
        )
    assert exc_info.value.code == "chat_daily_limit"


def test_admit_turn_daily_retries_quota(auth_headers):
    user_id = auth_headers["user_id"]
    thread = db.get_or_create_chat_thread(user_id)
    today = datetime.now(UTC).date()

    # Create a failed turn to retry
    root_id = uuid.uuid4()
    db.create_chat_turn(
        request_id=root_id,
        user_id=user_id,
        thread_id=thread["id"],
        fingerprint="fp-root",
        status="error",
    )

    # Pre-seed daily retries to 10
    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO chat_daily_usage (usage_date, user_id, new_turns_count, retries_count)
                VALUES (:d, :uid, 5, 10)
                ON CONFLICT (usage_date, user_id) DO UPDATE SET retries_count = 10
            """),
            {"d": today, "uid": user_id},
        )
        conn.commit()

    # 11th retry should raise ChatRetryLimitError
    with pytest.raises(ChatRetryLimitError) as exc_info:
        admit_chat_turn(
            user_id=user_id,
            request_id=uuid.uuid4(),
            thread_id=thread["id"],
            retry_of=root_id,
            lang="en",
        )
    assert exc_info.value.code == "chat_retry_limit"


def test_admit_turn_max_retries_per_root(auth_headers):
    user_id = auth_headers["user_id"]
    thread = db.get_or_create_chat_thread(user_id)

    root_id = uuid.uuid4()
    db.create_chat_turn(
        request_id=root_id,
        user_id=user_id,
        thread_id=thread["id"],
        fingerprint="fp-root",
        status="error",
    )

    # Retry 1 succeeds
    r1_id = uuid.uuid4()
    res1 = admit_chat_turn(
        user_id=user_id,
        request_id=r1_id,
        thread_id=thread["id"],
        retry_of=root_id,
        lang="en",
    )
    assert res1["attempt_number"] == 2
    db.update_chat_turn_status(request_id=r1_id, status="error")

    # Retry 2 succeeds
    r2_id = uuid.uuid4()
    res2 = admit_chat_turn(
        user_id=user_id,
        request_id=r2_id,
        thread_id=thread["id"],
        retry_of=root_id,
        lang="en",
    )
    assert res2["attempt_number"] == 3
    db.update_chat_turn_status(request_id=r2_id, status="error")

    # Retry 3 of this root should fail
    r3_id = uuid.uuid4()
    with pytest.raises(ChatRetryLimitError) as exc_info:
        admit_chat_turn(
            user_id=user_id,
            request_id=r3_id,
            thread_id=thread["id"],
            retry_of=root_id,
            lang="en",
        )
    assert exc_info.value.code == "chat_retry_limit"


def test_admit_turn_nothing_to_retry(auth_headers):
    user_id = auth_headers["user_id"]
    thread = db.get_or_create_chat_thread(user_id)

    # Target turn does not exist
    with pytest.raises(NothingToRetryError) as exc_info:
        admit_chat_turn(
            user_id=user_id,
            request_id=uuid.uuid4(),
            thread_id=thread["id"],
            retry_of=uuid.uuid4(),
            lang="en",
        )
    assert exc_info.value.code == "nothing_to_retry"

    # Target turn succeeded (status="ok") -> nothing to retry
    root_id = uuid.uuid4()
    db.create_chat_turn(
        request_id=root_id,
        user_id=user_id,
        thread_id=thread["id"],
        fingerprint="fp-ok",
        status="ok",
    )
    with pytest.raises(NothingToRetryError) as exc_info:
        admit_chat_turn(
            user_id=user_id,
            request_id=uuid.uuid4(),
            thread_id=thread["id"],
            retry_of=root_id,
            lang="en",
        )
    assert exc_info.value.code == "nothing_to_retry"


def test_admit_turn_utc_rollover(auth_headers):
    user_id = auth_headers["user_id"]
    thread = db.get_or_create_chat_thread(user_id)
    yesterday = datetime.now(UTC).date() - timedelta(days=1)

    # Yesterday was maxed out
    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO chat_daily_usage (usage_date, user_id, new_turns_count, retries_count)
                VALUES (:d, :uid, 50, 10)
            """),
            {"d": yesterday, "uid": user_id},
        )
        conn.commit()

    # Today should be admitted cleanly
    res = admit_chat_turn(
        user_id=user_id,
        request_id=uuid.uuid4(),
        thread_id=thread["id"],
        message="Good morning fresh day",
        lang="en",
    )
    assert res["kind"] == "new"
