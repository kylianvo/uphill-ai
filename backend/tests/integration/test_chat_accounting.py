"""Integration tests for Coach Chat call accounting and turn aggregation."""

import uuid
from decimal import Decimal

import pytest

import db
from db import (
    chat_turn_totals,
    finish_chat_call,
    get_chat_call,
    reserve_chat_call,
)
from services.coach_chat import track_chat_call
from services.coach_model import FakeCoachModel, ModelEvent, ModelRequest
from services.observability import Usage


def test_finish_chat_call_conditional_transition(auth_headers):
    user_id = auth_headers["user_id"]
    thread = db.get_or_create_chat_thread(user_id)
    req_id = uuid.uuid4()
    call_id = uuid.uuid4()

    db.create_chat_turn(request_id=req_id, user_id=user_id, thread_id=thread["id"], fingerprint="fp1")
    reserve_chat_call(call_id=call_id, request_id=req_id, feature="coach_chat", model="gemini-3.8-flash")

    # 1. First finish call transitions from 'reserved' to 'ok'
    first_res = finish_chat_call(
        call_id=call_id,
        status="ok",
        usage_known=True,
        input_tokens=100,
        output_tokens=50,
        thinking_tokens=10,
        cached_tokens=20,
        cost_usd=Decimal("0.000250"),
        latency_ms=620,
    )
    assert first_res is True

    # 2. Second finish call should fail conditional check (already 'ok')
    second_res = finish_chat_call(
        call_id=call_id,
        status="error",
        usage_known=False,
        input_tokens=0,
        output_tokens=0,
    )
    assert second_res is False

    # 3. Call record should maintain original values
    call = get_chat_call(call_id)
    assert call["status"] == "ok"
    assert call["usage_known"] is True
    assert call["input_tokens"] == 100
    assert call["output_tokens"] == 50
    assert call["latency_ms"] == 620


def test_retry_call_accounting_isolation(auth_headers):
    user_id = auth_headers["user_id"]
    thread = db.get_or_create_chat_thread(user_id)
    root_id = uuid.uuid4()
    retry_id = uuid.uuid4()

    db.create_chat_turn(request_id=root_id, user_id=user_id, thread_id=thread["id"], fingerprint="fp-root", status="error")
    db.create_chat_turn(
        request_id=retry_id,
        user_id=user_id,
        thread_id=thread["id"],
        fingerprint="fp-retry",
        root_turn_id=root_id,
        attempt_number=2,
        status="ok",
    )

    c1 = uuid.uuid4()
    reserve_chat_call(call_id=c1, request_id=root_id, feature="coach_chat", model="gemini-3.8-flash")
    finish_chat_call(call_id=c1, status="error", usage_known=True, input_tokens=80, output_tokens=10, cost_usd=Decimal("0.000090"))

    c2 = uuid.uuid4()
    reserve_chat_call(call_id=c2, request_id=retry_id, feature="coach_chat", model="gemini-3.8-flash")
    finish_chat_call(call_id=c2, status="ok", usage_known=True, input_tokens=90, output_tokens=60, cost_usd=Decimal("0.000200"))

    # Root totals
    root_totals = chat_turn_totals(root_id)
    assert root_totals["total_calls"] == 1
    assert root_totals["total_input_tokens"] == 80
    assert root_totals["total_output_tokens"] == 10

    # Retry totals
    retry_totals = chat_turn_totals(retry_id)
    assert retry_totals["total_calls"] == 1
    assert retry_totals["total_input_tokens"] == 90
    assert retry_totals["total_output_tokens"] == 60


def test_turn_totals_multi_call_aggregation(auth_headers):
    user_id = auth_headers["user_id"]
    thread = db.get_or_create_chat_thread(user_id)
    req_id = uuid.uuid4()
    db.create_chat_turn(request_id=req_id, user_id=user_id, thread_id=thread["id"], fingerprint="fp-multi")

    # 1. Retrieval embedding
    c_retrieval = uuid.uuid4()
    reserve_chat_call(c_retrieval, req_id, feature="chat_retrieval", model="gemini-embedding-2")
    finish_chat_call(c_retrieval, status="ok", usage_known=True, input_tokens=50, output_tokens=0, cost_usd=Decimal("0.000030"))

    # 2. Main answer
    c_answer = uuid.uuid4()
    reserve_chat_call(c_answer, req_id, feature="coach_chat", model="gemini-3.8-flash")
    finish_chat_call(
        c_answer,
        status="ok",
        usage_known=True,
        input_tokens=200,
        output_tokens=80,
        thinking_tokens=20,
        cached_tokens=40,
        cost_usd=Decimal("0.000450"),
    )

    # 3. Summary
    c_summary = uuid.uuid4()
    reserve_chat_call(c_summary, req_id, feature="chat_summary", model="gemini-3.8-flash")
    finish_chat_call(c_summary, status="ok", usage_known=True, input_tokens=150, output_tokens=40, cost_usd=Decimal("0.000200"))

    totals = chat_turn_totals(req_id)
    assert totals["total_calls"] == 3
    assert totals["total_input_tokens"] == 400
    assert totals["total_output_tokens"] == 120
    assert totals["total_thinking_tokens"] == 20
    assert totals["total_cached_tokens"] == 40
    assert totals["usage_known"] is True


def test_interrupted_call_usage_unknown(auth_headers):
    user_id = auth_headers["user_id"]
    thread = db.get_or_create_chat_thread(user_id)
    req_id = uuid.uuid4()
    call_id = uuid.uuid4()

    db.create_chat_turn(request_id=req_id, user_id=user_id, thread_id=thread["id"], fingerprint="fp-cancel")
    reserve_chat_call(call_id, req_id, feature="coach_chat", model="gemini-3.8-flash")

    finish_chat_call(call_id, status="interrupted", usage_known=False)

    call = get_chat_call(call_id)
    assert call["status"] == "interrupted"
    assert call["usage_known"] is False

    totals = chat_turn_totals(req_id)
    assert totals["total_calls"] == 1
    assert totals["usage_known"] is False


@pytest.mark.asyncio
async def test_track_chat_call_lifecycle_orchestration(auth_headers):
    user_id = auth_headers["user_id"]
    thread = db.get_or_create_chat_thread(user_id)
    req_id = uuid.uuid4()
    call_id = uuid.uuid4()

    db.create_chat_turn(request_id=req_id, user_id=user_id, thread_id=thread["id"], fingerprint="fp-orch")

    fake_model = FakeCoachModel(
        responses=[
            ModelEvent(kind="text", text="Hello runner!"),
            ModelEvent(
                kind="usage",
                usage=Usage(input_tokens=120, output_tokens=30, thinking_tokens=0, cached_tokens=10),
            ),
        ]
    )

    req = ModelRequest(messages=(), system="System prompt", max_output_tokens=1000, call_id=call_id)

    collected_text = []
    async for event in track_chat_call(
        call_id=call_id,
        request_id=req_id,
        feature="coach_chat",
        model_name="gemini-3.8-flash",
        model_adapter=fake_model,
        model_request=req,
    ):
        if event.kind == "text":
            collected_text.append(event.text)

    assert "".join(collected_text) == "Hello runner!"

    # Verify call accounting recorded in DB
    call = get_chat_call(call_id)
    assert call is not None
    assert call["status"] == "ok"
    assert call["usage_known"] is True
    assert call["input_tokens"] == 120
    assert call["output_tokens"] == 30
    assert call["cached_tokens"] == 10
