"""Unit tests for the typed LangGraph runner in Coach Chat Foundation."""

from uuid import uuid4

import pytest

from services.coach_graph import (
    CitationsEvent,
    StatusEvent,
    TokenEvent,
    TurnState,
    astream_turn_graph,
    build_graph,
)
from services.coach_model import (
    ChatMessage,
    FakeCoachModel,
    ModelEvent,
    ToolCallsNotSupportedError,
)
from services.observability import Usage


@pytest.mark.asyncio
async def test_graph_retrieve_generate_order_and_events():
    execution_order = []

    def mock_retrieve(query: str):
        execution_order.append("retrieve")
        return [{"ref": "ref-1", "title": "Base Training", "content": "Keep it easy."}]

    fake_model = FakeCoachModel(
        responses=[
            ModelEvent(kind="text", text="Hello "),
            ModelEvent(kind="text", text="runner!"),
            ModelEvent(kind="usage", usage=Usage(input_tokens=50, output_tokens=10)),
        ]
    )

    # Wrap model.stream to track execution order
    orig_stream = fake_model.stream

    async def tracking_stream(req):
        execution_order.append("generate")
        async for evt in orig_stream(req):
            yield evt

    fake_model.stream = tracking_stream

    graph = build_graph(model=fake_model, retrieve_fn=mock_retrieve)

    initial_state: TurnState = {
        "user_id": 1,
        "request_id": str(uuid4()),
        "call_id": uuid4(),
        "question": "How to run easy?",
        "lang": "en",
        "messages": [ChatMessage(role="user", content="How to run easy?")],
        "context": {"athlete": {"current_weekly_km": 30.0}},
    }

    events = []
    async for event in astream_turn_graph(graph, initial_state):
        events.append(event)

    # 1. Verify retrieve then generate execution order
    assert execution_order == ["retrieve", "generate"]

    # 2. Verify emitted application events
    assert any(isinstance(e, StatusEvent) and e.step == "retrieving" for e in events)
    assert any(isinstance(e, StatusEvent) and e.step == "generating" for e in events)
    tokens = [e.text for e in events if isinstance(e, TokenEvent)]
    assert "".join(tokens) == "Hello runner!"
    citations_events = [e for e in events if isinstance(e, CitationsEvent)]
    assert len(citations_events) >= 1
    assert citations_events[0].evidence_status == "available"


@pytest.mark.asyncio
async def test_graph_retrieval_empty():
    def mock_retrieve_empty(query: str):
        return []

    fake_model = FakeCoachModel(
        responses=[
            ModelEvent(kind="text", text="General advice"),
            ModelEvent(kind="usage", usage=Usage(input_tokens=20, output_tokens=5)),
        ]
    )

    graph = build_graph(model=fake_model, retrieve_fn=mock_retrieve_empty)

    initial_state: TurnState = {
        "user_id": 1,
        "request_id": str(uuid4()),
        "call_id": uuid4(),
        "question": "What shoes are good?",
        "lang": "en",
    }

    events = []
    async for event in astream_turn_graph(graph, initial_state):
        events.append(event)

    citations_events = [e for e in events if isinstance(e, CitationsEvent)]
    assert citations_events[0].evidence_status == "empty"


@pytest.mark.asyncio
async def test_graph_retrieval_unavailable():
    def mock_retrieve_error(query: str):
        raise RuntimeError("Qdrant unavailable")

    fake_model = FakeCoachModel(
        responses=[
            ModelEvent(kind="text", text="General answer without KB"),
            ModelEvent(kind="usage", usage=Usage(input_tokens=20, output_tokens=5)),
        ]
    )

    graph = build_graph(model=fake_model, retrieve_fn=mock_retrieve_error)

    initial_state: TurnState = {
        "user_id": 1,
        "request_id": str(uuid4()),
        "call_id": uuid4(),
        "question": "Tell me about trails",
        "lang": "en",
    }

    events = []
    # Does not crash; continues and marks evidence_status as unavailable
    async for event in astream_turn_graph(graph, initial_state):
        events.append(event)

    citations_events = [e for e in events if isinstance(e, CitationsEvent)]
    assert citations_events[0].evidence_status == "unavailable"
    tokens = [e.text for e in events if isinstance(e, TokenEvent)]
    assert "".join(tokens) == "General answer without KB"


@pytest.mark.asyncio
async def test_graph_tool_calls_rejected():
    fake_model = FakeCoachModel(
        responses=[
            ModelEvent(kind="tool_call", tool_call={"name": "plan_workout", "args": {}}),
        ]
    )

    graph = build_graph(model=fake_model, retrieve_fn=lambda q: [])

    initial_state: TurnState = {
        "user_id": 1,
        "request_id": str(uuid4()),
        "call_id": uuid4(),
        "question": "Book me a run",
        "lang": "en",
    }

    with pytest.raises(ToolCallsNotSupportedError):
        async for _ in astream_turn_graph(graph, initial_state):
            pass


@pytest.mark.asyncio
async def test_graph_private_state_and_usage_finalization():
    fake_model = FakeCoachModel(
        responses=[
            ModelEvent(kind="text", text="Generated answer"),
            ModelEvent(kind="usage", usage=Usage(input_tokens=150, output_tokens=45, thinking_tokens=0)),
        ]
    )

    graph = build_graph(model=fake_model, retrieve_fn=lambda q: [{"ref": "ref-1", "title": "T", "content": "C"}])

    initial_state: TurnState = {
        "user_id": 1,
        "request_id": str(uuid4()),
        "call_id": uuid4(),
        "question": "Question",
        "lang": "en",
    }

    final_state = {}

    async def collect_updates(state: TurnState):
        # Mirrors astream_turn_graph's own chunk-shape normalization (dict, 2-tuple,
        # or 3-tuple depending on LangGraph's namespaced/non-namespaced streaming).
        async for chunk in graph.astream(state, stream_mode=["custom", "updates"], version="v2"):
            if isinstance(chunk, dict):
                mode, payload = chunk.get("type"), chunk.get("data")
            elif isinstance(chunk, tuple | list) and len(chunk) == 3:
                mode, payload = chunk[0], chunk[2]
            elif isinstance(chunk, tuple | list) and len(chunk) == 2:
                mode, payload = chunk
            else:
                continue
            if mode == "updates":
                for _node_name, updates in payload.items():
                    final_state.update(updates)

    await collect_updates(initial_state)

    assert final_state.get("reply_text") == "Generated answer"
    assert final_state.get("usage") == Usage(input_tokens=150, output_tokens=45, thinking_tokens=0)
    assert final_state.get("status") == "ok"
    assert final_state.get("evidence_status") == "available"


def test_parse_app_event_tool_call():
    from services.coach_graph import ToolCallEvent, parse_app_event

    evt = parse_app_event(
        {"type": "tool_call", "tool_call_id": "call_1", "name": "get_week", "args": {"week_number": 3}}
    )
    assert isinstance(evt, ToolCallEvent)
    assert evt.name == "get_week"
    assert evt.args == {"week_number": 3}


def test_parse_app_event_tool_result():
    from services.coach_graph import ToolResultEvent, parse_app_event

    evt = parse_app_event(
        {
            "type": "tool_result",
            "tool_call_id": "call_1",
            "name": "get_week",
            "status": "success",
            "card_type": "week_schedule",
            "card_data": {"week_number": 3},
        }
    )
    assert isinstance(evt, ToolResultEvent)
    assert evt.status == "success"
    assert evt.card_data == {"week_number": 3}


def test_parse_app_event_clarify():
    from services.coach_graph import ClarifyEvent, parse_app_event

    evt = parse_app_event({"type": "clarify", "prompt": "Which race?", "options": ["Dalat Ultra Trail", "VMM"]})
    assert isinstance(evt, ClarifyEvent)
    assert evt.options == ["Dalat Ultra Trail", "VMM"]
