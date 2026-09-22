"""Integration tests for Coach Chat streaming SSE, thread pagination, sources, and clear endpoints."""

import uuid
from unittest.mock import patch

import pytest

import db
from services.coach_graph import DoneEvent, StatusEvent, TokenEvent


def test_stream_api_pre_validation(client, auth_headers):
    headers = auth_headers["headers"]

    # 1. Invalid UUID
    resp = client.post(
        "/api/coach/chat/stream",
        headers=headers,
        json={"request_id": "not-a-uuid", "message": "Hi"},
    )
    assert resp.status_code == 422

    # 2. Both message and retry_of provided
    resp = client.post(
        "/api/coach/chat/stream",
        headers=headers,
        json={
            "request_id": str(uuid.uuid4()),
            "message": "Hi",
            "retry_of": str(uuid.uuid4()),
        },
    )
    assert resp.status_code == 400

    # 3. Neither message nor retry_of provided
    resp = client.post(
        "/api/coach/chat/stream",
        headers=headers,
        json={"request_id": str(uuid.uuid4())},
    )
    assert resp.status_code == 400

    # 4. Message exceeds max allowed length
    resp = client.post(
        "/api/coach/chat/stream",
        headers=headers,
        json={
            "request_id": str(uuid.uuid4()),
            "message": "A" * 2001,
        },
    )
    assert resp.status_code == 400


def test_stream_api_sse_streaming(client, auth_headers):
    headers = auth_headers["headers"]
    req_id = uuid.uuid4()

    async def fake_run_turn(user, request, model=None):
        yield StatusEvent(step="retrieving", request_id=str(req_id))
        yield StatusEvent(step="generating", request_id=str(req_id))
        yield TokenEvent(text="Hello ")
        yield TokenEvent(text="athlete!")
        yield DoneEvent(request_id=str(req_id), message_id=42, replayed=False)

    with patch("services.coach_chat.run_turn", side_effect=fake_run_turn):
        resp = client.post(
            "/api/coach/chat/stream",
            headers=headers,
            json={"request_id": str(req_id), "message": "Hello coach"},
        )

        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]
        assert resp.headers.get("x-accel-buffering") == "no"

        content = resp.text
        assert "event: status" in content
        assert "event: token" in content
        assert "Hello " in content
        assert "athlete!" in content
        assert "event: done" in content


def test_get_chat_thread_and_pagination(client, auth_headers):
    user_id = auth_headers["user_id"]
    headers = auth_headers["headers"]
    thread = db.get_or_create_chat_thread(user_id)

    # Insert test messages
    m1 = db.append_chat_message(thread["id"], "user", "Message 1")
    m2 = db.append_chat_message(thread["id"], "assistant", "Reply 1")

    resp = client.get("/api/coach/chat/thread?limit=10", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["messages"]) == 2
    assert data["messages"][0]["id"] == m1
    assert data["messages"][1]["id"] == m2


def test_get_chat_turn_status(client, auth_headers):
    user_id = auth_headers["user_id"]
    headers = auth_headers["headers"]
    req_id = uuid.uuid4()

    db.create_chat_turn(
        request_id=req_id,
        user_id=user_id,
        thread_id=None,
        fingerprint="fp-test",
        status="ok",
        result_message_id=99,
    )

    # 1. Owned turn
    resp = client.get(f"/api/coach/chat/turns/{req_id}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["request_id"] == str(req_id)
    assert data["status"] == "ok"
    assert data["result_message_id"] == 99

    # 2. Non-existent turn -> 404
    missing_id = uuid.uuid4()
    resp_missing = client.get(f"/api/coach/chat/turns/{missing_id}", headers=headers)
    assert resp_missing.status_code == 404


def test_get_chat_message_sources(client, auth_headers):
    user_id = auth_headers["user_id"]
    headers = auth_headers["headers"]
    thread = db.get_or_create_chat_thread(user_id)

    evidence_data = [{"ref": "ref-1", "title": "Hydration", "content": "Drink water"}]
    citations_data = [{"ref": "ref-1", "title": "Hydration"}]

    msg_id = db.append_chat_message(
        thread_id=thread["id"],
        role="assistant",
        content="Drink water [ref-1]",
        evidence=evidence_data,
        citations=citations_data,
    )

    # 1. Owned message sources
    resp = client.get(f"/api/coach/chat/messages/{msg_id}/sources", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["message_id"] == msg_id
    assert len(data["evidence"]) == 1
    assert data["evidence_status"] == "available"

    # 2. Non-existent message -> 404
    resp_missing = client.get("/api/coach/chat/messages/999999/sources", headers=headers)
    assert resp_missing.status_code == 404


def test_clear_chat_thread(client, auth_headers):
    user_id = auth_headers["user_id"]
    headers = auth_headers["headers"]
    thread = db.get_or_create_chat_thread(user_id)

    db.append_chat_message(thread["id"], "user", "Old msg")
    db.append_chat_message(thread["id"], "assistant", "Old reply")

    # 1. Clear thread
    resp = client.delete("/api/coach/chat/thread", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "cleared"

    # 2. Verify messages deleted
    thread_data = client.get("/api/coach/chat/thread", headers=headers).json()
    assert len(thread_data["messages"]) == 0

    # 3. Conflict when active turn in progress
    req_id = uuid.uuid4()
    db.create_chat_turn(
        request_id=req_id,
        user_id=user_id,
        thread_id=thread["id"],
        fingerprint="fp-active",
        status="active",
    )
    resp_conflict = client.delete("/api/coach/chat/thread", headers=headers)
    assert resp_conflict.status_code == 409
