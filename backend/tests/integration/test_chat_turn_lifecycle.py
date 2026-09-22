"""Integration tests for Coach Chat turn lifecycle, partial persistence, and recovery."""

import uuid
from unittest.mock import patch

import pytest

import db
from db import ChatRequestConflictError
from services.coach_chat import run_turn
from services.coach_graph import DoneEvent, ErrorEvent, StatusEvent, TokenEvent
from services.coach_model import FakeCoachModel, ModelEvent
from services.observability import Usage


@pytest.mark.asyncio
async def test_turn_lifecycle_success_stream(auth_headers):
    user_id = auth_headers["user_id"]
    req_id = uuid.uuid4()
    fake_model = FakeCoachModel(
        responses=[
            ModelEvent(kind="text", text="Pace "),
            ModelEvent(kind="text", text="is 5:00/km"),
            ModelEvent(kind="usage", usage=Usage(input_tokens=80, output_tokens=20)),
        ]
    )

    request_data = {
        "request_id": str(req_id),
        "message": "What is my tempo pace?",
        "lang": "en",
    }

    events = []
    async for event in run_turn(user={"id": user_id}, request=request_data, model=fake_model):
        events.append(event)

    # 1. Assert application events received
    assert any(isinstance(e, StatusEvent) and e.step == "retrieving" for e in events)
    assert any(isinstance(e, StatusEvent) and e.step == "generating" for e in events)
    tokens = [e.text for e in events if isinstance(e, TokenEvent)]
    assert "".join(tokens) == "Pace is 5:00/km"
    done_events = [e for e in events if isinstance(e, DoneEvent)]
    assert len(done_events) == 1
    assert done_events[0].replayed is False
    assert done_events[0].message_id is not None

    # 2. Assert DB state
    assistant_msg = db.get_chat_message(done_events[0].message_id)
    assert assistant_msg is not None
    assert assistant_msg["content"] == "Pace is 5:00/km"
    assert assistant_msg["status"] == "ok"
    assert assistant_msg["role"] == "assistant"

    turn_row = db.get_chat_turn(user_id=user_id, request_id=req_id)
    assert turn_row is not None
    assert turn_row["status"] == "ok"
    assert turn_row["result_message_id"] == assistant_msg["id"]


@pytest.mark.asyncio
async def test_turn_lifecycle_error_preserves_partial(auth_headers):
    user_id = auth_headers["user_id"]
    req_id = uuid.uuid4()

    # Fake model streams one token, then raises exception
    class FailingModel(FakeCoachModel):
        async def stream(self, req):
            yield ModelEvent(kind="text", text="Partial answer before ")
            raise RuntimeError("Upstream stream broken")

    failing_model = FailingModel()

    request_data = {
        "request_id": str(req_id),
        "message": "Plan my week",
        "lang": "en",
    }

    events = []
    async for event in run_turn(user={"id": user_id}, request=request_data, model=failing_model):
        events.append(event)

    # Assert ErrorEvent yielded
    assert any(isinstance(e, ErrorEvent) for e in events)
    # Assert no DoneEvent
    assert not any(isinstance(e, DoneEvent) for e in events)

    # Assert partial text is preserved in DB without fabricated replacement
    turn_row = db.get_chat_turn(user_id=user_id, request_id=req_id)
    assert turn_row is not None
    assert turn_row["status"] in ("error", "interrupted")

    msg_id = turn_row["result_message_id"]
    assert msg_id is not None
    assistant_msg = db.get_chat_message(msg_id)
    assert assistant_msg["status"] in ("error", "interrupted")
    assert "Partial answer before " in assistant_msg["content"]


@pytest.mark.asyncio
async def test_turn_lifecycle_replay_does_not_call_model(auth_headers):
    user_id = auth_headers["user_id"]
    req_id = uuid.uuid4()

    fake_model = FakeCoachModel(
        responses=[
            ModelEvent(kind="text", text="Original reply"),
            ModelEvent(kind="usage", usage=Usage(input_tokens=50, output_tokens=10)),
        ]
    )

    request_data = {
        "request_id": str(req_id),
        "message": "Question to be replayed",
        "lang": "en",
    }

    # 1. First execution
    events1 = [e async for e in run_turn(user={"id": user_id}, request=request_data, model=fake_model)]
    done1 = [e for e in events1 if isinstance(e, DoneEvent)][0]
    assert done1.replayed is False

    # 2. Second execution with same req_id and same message -> replay
    mock_model = FakeCoachModel(responses=[])
    # If model.stream is called, it will be noticed
    stream_called = False
    orig_stream = mock_model.stream

    async def tracking_stream(req):
        nonlocal stream_called
        stream_called = True
        async for evt in orig_stream(req):
            yield evt

    mock_model.stream = tracking_stream

    events2 = [e async for e in run_turn(user={"id": user_id}, request=request_data, model=mock_model)]
    done2 = [e for e in events2 if isinstance(e, DoneEvent)][0]
    assert done2.replayed is True
    assert stream_called is False
    assert "".join(e.text for e in events2 if isinstance(e, TokenEvent)) == "Original reply"


@pytest.mark.asyncio
async def test_turn_lifecycle_conflict(auth_headers):
    user_id = auth_headers["user_id"]
    req_id = uuid.uuid4()

    fake_model = FakeCoachModel(responses=[ModelEvent(kind="text", text="Ans")])

    req1 = {"request_id": str(req_id), "message": "Initial message", "lang": "en"}
    _ = [e async for e in run_turn(user={"id": user_id}, request=req1, model=fake_model)]

    # Same request_id with DIFFERENT message -> conflict
    req2 = {"request_id": str(req_id), "message": "Conflicting message", "lang": "en"}
    with pytest.raises(ChatRequestConflictError):
        async for _ in run_turn(user={"id": user_id}, request=req2, model=fake_model):
            pass


@pytest.mark.asyncio
async def test_turn_lifecycle_db_finalization_failure_emits_no_done(auth_headers):
    user_id = auth_headers["user_id"]
    req_id = uuid.uuid4()
    fake_model = FakeCoachModel(responses=[ModelEvent(kind="text", text="Finished token")])

    request_data = {
        "request_id": str(req_id),
        "message": "Test DB failure",
        "lang": "en",
    }

    # Simulate DB finalization failure
    with patch("db.finish_chat_turn", side_effect=RuntimeError("Database lock failure")):
        events = []
        with pytest.raises(RuntimeError):
            async for event in run_turn(user={"id": user_id}, request=request_data, model=fake_model):
                events.append(event)

        # Confirm done event was NEVER emitted
        assert not any(isinstance(e, DoneEvent) for e in events)
