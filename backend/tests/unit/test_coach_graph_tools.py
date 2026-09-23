import asyncio
from uuid import uuid4

import pytest
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from services.coach_graph import ClarifyEvent, ToolResultEvent, astream_turn_graph, build_graph
from services.coach_model import FakeCoachModel, ModelEvent
from services.observability import Usage


class _EchoInput(BaseModel):
    value: str = Field(description="value to echo")


def _echo_tool(name: str, delay: float = 0.0):
    async def _run(value: str) -> dict:
        if delay:
            await asyncio.sleep(delay)
        return {
            "tool_call_id": "",
            "name": name,
            "status": "success",
            "card_type": "echo",
            "card_data": {"value": value},
            "error": None,
        }

    return StructuredTool.from_function(coroutine=_run, name=name, description="echo", args_schema=_EchoInput)


@pytest.mark.asyncio
async def test_single_tool_call_then_final_reply():
    fake_model = FakeCoachModel(
        responses=[
            ModelEvent(kind="tool_call", tool_call={"id": "call_1", "name": "echo_a", "args": {"value": "hi"}}),
            ModelEvent(kind="text", text="Done."),
            ModelEvent(kind="usage", usage=Usage(input_tokens=10, output_tokens=5)),
        ]
    )
    graph = build_graph(model=fake_model, retrieve_fn=lambda q: [], tools=[_echo_tool("echo_a")])
    initial_state = {"user_id": 1, "request_id": str(uuid4()), "call_id": uuid4(), "question": "hi", "lang": "en"}

    events = [e async for e in astream_turn_graph(graph, initial_state)]
    tool_results = [e for e in events if isinstance(e, ToolResultEvent)]
    assert len(tool_results) == 1
    assert tool_results[0].card_data == {"value": "hi"}


@pytest.mark.asyncio
async def test_parallel_tool_calls_execute_concurrently():
    # Two 0.2s tools; if run sequentially this takes >=0.4s, in parallel ~0.2s.
    fake_model = FakeCoachModel(
        responses=[
            ModelEvent(kind="tool_call", tool_call={"id": "call_1", "name": "echo_a", "args": {"value": "a"}}),
            ModelEvent(kind="tool_call", tool_call={"id": "call_2", "name": "echo_b", "args": {"value": "b"}}),
            ModelEvent(kind="text", text="Done."),
        ]
    )
    graph = build_graph(
        model=fake_model,
        retrieve_fn=lambda q: [],
        tools=[_echo_tool("echo_a", delay=0.2), _echo_tool("echo_b", delay=0.2)],
    )
    initial_state = {"user_id": 1, "request_id": str(uuid4()), "call_id": uuid4(), "question": "hi", "lang": "en"}

    import time

    start = time.monotonic()
    events = [e async for e in astream_turn_graph(graph, initial_state)]
    elapsed = time.monotonic() - start

    assert elapsed < 0.35
    assert len([e for e in events if isinstance(e, ToolResultEvent)]) == 2


@pytest.mark.asyncio
async def test_tool_call_cap_forces_final_reply():
    # 5 sequential tool-call rounds requested; only 4 should execute before the
    # graph forces a final generate without tools.
    responses = []
    for i in range(5):
        responses.append(
            ModelEvent(kind="tool_call", tool_call={"id": f"call_{i}", "name": "echo_a", "args": {"value": str(i)}})
        )
    fake_model = FakeCoachModel(responses=responses + [ModelEvent(kind="text", text="Capped.")])
    graph = build_graph(model=fake_model, retrieve_fn=lambda q: [], tools=[_echo_tool("echo_a")])
    initial_state = {"user_id": 1, "request_id": str(uuid4()), "call_id": uuid4(), "question": "hi", "lang": "en"}

    events = [e async for e in astream_turn_graph(graph, initial_state)]
    tool_results = [e for e in events if isinstance(e, ToolResultEvent)]
    assert len(tool_results) <= 4


def _clarify_tool(name: str):
    async def _run(value: str) -> dict:
        return {
            "tool_call_id": "",
            "name": name,
            "status": "error",
            "card_type": None,
            "card_data": None,
            "error": "distance_required",
            "clarify": {"prompt": "Which distance are you racing?", "options": ["50km", "75km"]},
        }

    return StructuredTool.from_function(coroutine=_run, name=name, description="clarify", args_schema=_EchoInput)


@pytest.mark.asyncio
async def test_tool_result_with_clarify_emits_clarify_event():
    fake_model = FakeCoachModel(
        responses=[
            ModelEvent(kind="tool_call", tool_call={"id": "call_1", "name": "pace_strategy", "args": {"value": "x"}}),
            ModelEvent(kind="text", text="Which distance?"),
        ]
    )
    graph = build_graph(model=fake_model, retrieve_fn=lambda q: [], tools=[_clarify_tool("pace_strategy")])
    initial_state = {"user_id": 1, "request_id": str(uuid4()), "call_id": uuid4(), "question": "hi", "lang": "en"}

    events = [e async for e in astream_turn_graph(graph, initial_state)]
    clarify_events = [e for e in events if isinstance(e, ClarifyEvent)]
    tool_results = [e for e in events if isinstance(e, ToolResultEvent)]

    assert len(clarify_events) == 1
    assert clarify_events[0].prompt == "Which distance are you racing?"
    assert clarify_events[0].options == ["50km", "75km"]
    assert len(tool_results) == 1
    assert tool_results[0].status == "error"


@pytest.mark.asyncio
async def test_tool_failure_degrades_gracefully_without_crashing_turn():
    async def _boom(value: str) -> dict:
        raise RuntimeError("tool exploded")

    failing_tool = StructuredTool.from_function(
        coroutine=_boom, name="echo_a", description="echo", args_schema=_EchoInput
    )
    fake_model = FakeCoachModel(
        responses=[
            ModelEvent(kind="tool_call", tool_call={"id": "call_1", "name": "echo_a", "args": {"value": "x"}}),
            ModelEvent(kind="text", text="I couldn't run that, but here's what I know."),
        ]
    )
    graph = build_graph(model=fake_model, retrieve_fn=lambda q: [], tools=[failing_tool])
    initial_state = {"user_id": 1, "request_id": str(uuid4()), "call_id": uuid4(), "question": "hi", "lang": "en"}

    events = [e async for e in astream_turn_graph(graph, initial_state)]
    tool_results = [e for e in events if isinstance(e, ToolResultEvent)]
    assert tool_results[0].status == "error"
    from services.coach_graph import TokenEvent

    tokens = "".join(e.text for e in events if isinstance(e, TokenEvent))
    assert "couldn't run" in tokens
