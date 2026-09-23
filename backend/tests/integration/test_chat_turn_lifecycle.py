"""Integration tests for Coach Chat turn lifecycle, partial persistence, and recovery."""

import uuid
from unittest.mock import AsyncMock, patch

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


@pytest.mark.asyncio
async def test_turn_with_tool_call_persists_tool_calls_json(auth_headers, monkeypatch):
    import json

    from services.coach_model import ModelEvent

    user_id = auth_headers["user_id"]
    req_id = uuid.uuid4()

    fake_model = FakeCoachModel(
        responses=[
            ModelEvent(kind="tool_call", tool_call={"id": "call_1", "name": "kb_search", "args": {"query": "zone 2"}}),
            ModelEvent(kind="text", text="Here's what I found."),
            ModelEvent(kind="usage", usage=Usage(input_tokens=80, output_tokens=20)),
        ]
    )

    from services.coach_tools.base import ToolResult

    monkeypatch.setattr(
        "services.coach_tools.knowledge_tools.kb_search_impl",
        lambda **kwargs: ToolResult(
            tool_call_id="",
            name="kb_search",
            status="success",
            card_type="knowledge_citations",
            card_data={"citations": []},
        ),
    )

    request_data = {"request_id": str(req_id), "message": "What does Scott Johnston say about Zone 2?", "lang": "en"}
    events = [e async for e in run_turn(user={"id": user_id}, request=request_data, model=fake_model)]

    done_events = [e for e in events if isinstance(e, DoneEvent)]
    assert len(done_events) == 1

    assistant_msg = db.get_chat_message(done_events[0].message_id)
    stored = assistant_msg["tool_calls_json"]
    parsed = json.loads(stored) if isinstance(stored, str) else stored
    assert parsed is not None
    assert parsed[0]["name"] == "kb_search"


@pytest.mark.asyncio
async def test_run_turn_constructs_model_with_tools_bound(auth_headers):
    """Regression test for commit 0772600: run_turn must construct
    GeminiCoachModel(api_key=..., tools=...) with the per-turn tools when no
    model is injected. Before that fix, tools were only handed to build_graph,
    so the real model never gained function-calling ability and could never
    call a tool -- no test caught it because every other test in this suite
    injects FakeCoachModel directly, bypassing the GeminiCoachModel
    construction path entirely."""
    user_id = auth_headers["user_id"]
    req_id = uuid.uuid4()

    fake_model = FakeCoachModel(responses=[ModelEvent(kind="text", text="Hello")])

    with patch("services.coach_model.GeminiCoachModel", return_value=fake_model) as mock_ctor:
        request_data = {
            "request_id": str(req_id),
            "message": "What is my tempo pace?",
            "lang": "en",
        }
        events = [e async for e in run_turn(user={"id": user_id}, request=request_data, model=None)]

    assert any(isinstance(e, DoneEvent) for e in events)
    mock_ctor.assert_called_once()
    _, kwargs = mock_ctor.call_args
    assert kwargs.get("api_key")
    tools = kwargs.get("tools")
    assert tools
    tool_names = {t.name for t in tools}
    assert tool_names == {"get_week", "pace_strategy", "week_review", "kb_search"}


@pytest.mark.asyncio
async def test_second_turn_includes_prior_history_once(auth_headers):
    """A stateless model call broke conversational continuity in live testing:
    the coach showed distance clarify chips, the athlete answered "75km", and
    the next turn's model request had no memory of the first turn at all. The
    second turn's ModelRequest must carry the first turn's user question and
    assistant reply (in order), end with the second question, and must not
    duplicate the second question."""
    user_id = auth_headers["user_id"]

    fake_model = FakeCoachModel(
        responses=[
            ModelEvent(kind="text", text="Dalat Ultra Trail has 25km, 45km, 75km and 100km options."),
            ModelEvent(kind="usage", usage=Usage(input_tokens=50, output_tokens=10)),
        ]
    )

    # Disable summary generation for this test so fake_model.requests only
    # contains the two turns' generate() calls -- summary generation reuses
    # the same model and would otherwise append its own request in between,
    # per the task-24 brief this task does not touch summary scheduling.
    with patch("services.coach_chat._update_thread_summary", new=AsyncMock(return_value=None)):
        req_id_1 = uuid.uuid4()
        request_1 = {
            "request_id": str(req_id_1),
            "message": "Give me a pacing plan for Dalat Ultra Trail",
            "lang": "en",
        }
        events_1 = [e async for e in run_turn(user={"id": user_id}, request=request_1, model=fake_model)]
        assert any(isinstance(e, DoneEvent) for e in events_1)

        fake_model_2 = FakeCoachModel(
            responses=[
                ModelEvent(kind="text", text="Got it, 75km. Here's your pacing plan."),
                ModelEvent(kind="usage", usage=Usage(input_tokens=60, output_tokens=15)),
            ]
        )

        req_id_2 = uuid.uuid4()
        request_2 = {
            "request_id": str(req_id_2),
            "message": "75km",
            "lang": "en",
        }
        events_2 = [e async for e in run_turn(user={"id": user_id}, request=request_2, model=fake_model_2)]
        assert any(isinstance(e, DoneEvent) for e in events_2)

    assert len(fake_model.requests) == 1
    assert len(fake_model_2.requests) == 1
    second_request = fake_model_2.requests[-1]
    contents = [m.content for m in second_request.messages]

    assert contents[0] == "Give me a pacing plan for Dalat Ultra Trail"
    assert "Dalat Ultra Trail has 25km, 45km, 75km and 100km options." in contents
    assert contents[-1] == "75km"
    assert contents.count("75km") == 1


@pytest.mark.asyncio
async def test_retry_turn_does_not_duplicate_question_in_history(auth_headers):
    """Retry recovers `question` from the last user message already persisted
    in the thread; the same no-duplication rule as a fresh turn applies."""
    user_id = auth_headers["user_id"]

    class FailingOnce(FakeCoachModel):
        async def stream(self, req):
            self.requests.append(req)
            raise RuntimeError("upstream broken")

    failing_model = FailingOnce()

    with patch("services.coach_chat._update_thread_summary", new=AsyncMock(return_value=None)):
        req_id_1 = uuid.uuid4()
        request_1 = {"request_id": str(req_id_1), "message": "What's my long run pace?", "lang": "en"}
        events_1 = [e async for e in run_turn(user={"id": user_id}, request=request_1, model=failing_model)]
        assert any(isinstance(e, ErrorEvent) for e in events_1)

        retry_model = FakeCoachModel(responses=[ModelEvent(kind="text", text="Your long run pace is 5:30/km.")])
        req_id_retry = uuid.uuid4()
        request_retry = {"request_id": str(req_id_retry), "retry_of": str(req_id_1), "lang": "en"}
        events_2 = [e async for e in run_turn(user={"id": user_id}, request=request_retry, model=retry_model)]
        assert any(isinstance(e, DoneEvent) for e in events_2)

    retry_request = retry_model.requests[-1]
    contents = [m.content for m in retry_request.messages]
    assert contents.count("What's my long run pace?") == 1
    assert contents[-1] == "What's my long run pace?"


@pytest.mark.asyncio
async def test_thread_summary_rendered_in_system_prompt_when_present(auth_headers):
    """The retained thread summary must reach the compiled system prompt as a
    labeled, untrusted section -- and only when a summary actually exists."""
    user_id = auth_headers["user_id"]
    thread = db.get_or_create_chat_thread(user_id)

    fake_model = FakeCoachModel(responses=[ModelEvent(kind="text", text="Sure thing.")])

    with patch("services.coach_chat._update_thread_summary", new=AsyncMock(return_value=None)):
        req_id = uuid.uuid4()
        request_data = {"request_id": str(req_id), "message": "How's my training going?", "lang": "en"}
        events = [e async for e in run_turn(user={"id": user_id}, request=request_data, model=fake_model)]
    done_events = [e for e in events if isinstance(e, DoneEvent)]
    assert len(done_events) == 1

    no_summary_system = fake_model.requests[-1].system
    assert "Earlier conversation summary" not in no_summary_system

    db.update_chat_thread_summary_cas(
        thread_id=thread["id"],
        user_id=user_id,
        new_summary="Athlete is training for Dalat Ultra Trail 75km; prefers morning runs.",
        new_summarized_through_id=done_events[0].message_id,
        expected_summarized_through_id=thread.get("summarized_through_id"),
    )

    fake_model_2 = FakeCoachModel(responses=[ModelEvent(kind="text", text="Sure thing again.")])
    with patch("services.coach_chat._update_thread_summary", new=AsyncMock(return_value=None)):
        req_id_2 = uuid.uuid4()
        request_data_2 = {"request_id": str(req_id_2), "message": "How's my training going?", "lang": "en"}
        events_2 = [e async for e in run_turn(user={"id": user_id}, request=request_data_2, model=fake_model_2)]
    assert any(isinstance(e, DoneEvent) for e in events_2)

    with_summary_system = fake_model_2.requests[-1].system
    assert "Earlier conversation summary" in with_summary_system
    assert "Athlete is training for Dalat Ultra Trail 75km; prefers morning runs." in with_summary_system
