"""Unit tests for provider-neutral CoachModel protocol and GeminiCoachModel adapter."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from services.coach_model import (
    ChatMessage,
    CoachModel,
    CoachModelUpstreamError,
    FakeCoachModel,
    GeminiCoachModel,
    ModelEvent,
    ModelRequest,
    ToolCallsNotSupportedError,
)
from services.observability import Usage


def test_model_request_and_event_immutability():
    req = ModelRequest(
        messages=(ChatMessage(role="user", content="hello"),),
        system="system prompt",
        max_output_tokens=1000,
        call_id=uuid4(),
    )
    with pytest.raises((AttributeError, TypeError)):
        req.system = "new system"

    event = ModelEvent(kind="text", text="hello")
    with pytest.raises((AttributeError, TypeError)):
        event.text = "world"


@pytest.mark.asyncio
async def test_fake_coach_model_implements_protocol():
    fake = FakeCoachModel(
        responses=[
            ModelEvent(kind="text", text="Xin chào"),
            ModelEvent(kind="usage", usage=Usage(input_tokens=10, output_tokens=5)),
        ],
        token_count=42,
    )
    assert isinstance(fake, CoachModel)

    req = ModelRequest(
        messages=(ChatMessage(role="user", content="hi"),),
        system="sys",
        max_output_tokens=100,
        call_id=uuid4(),
    )

    tokens = await fake.count_tokens(req)
    assert tokens == 42

    events = []
    async for ev in fake.stream(req):
        events.append(ev)

    assert len(events) == 2
    assert events[0].text == "Xin chào"
    assert events[1].usage.input_tokens == 10
    await fake.close()
    assert fake.closed is True


@pytest.mark.asyncio
async def test_gemini_adapter_streams_vietnamese_text_chunks():
    chunks_text = ["Chào ", "bạn! ", "Hôm ", "nay ", "bài ", "chạy ", "Zone 2 ", "nhé."]

    async def fake_astream(messages):
        for t in chunks_text:
            chunk = MagicMock()
            chunk.content = t
            chunk.additional_kwargs = {}
            chunk.tool_calls = []
            chunk.tool_call_chunks = []
            chunk.usage_metadata = None
            yield chunk

    adapter = GeminiCoachModel(api_key="test-key", model="gemini-3.8-flash")
    adapter._chat = MagicMock()
    adapter._chat.astream = fake_astream

    req = ModelRequest(
        messages=(ChatMessage(role="user", content="Hôm nay chạy gì?"),),
        system="Bạn là Coach Uphill.",
        max_output_tokens=500,
        call_id=uuid4(),
    )

    assembled = []
    async for event in adapter.stream(req):
        if event.kind == "text":
            assembled.append(event.text)

    assert "".join(assembled) == "Chào bạn! Hôm nay bài chạy Zone 2 nhé."


@pytest.mark.asyncio
async def test_gemini_adapter_excludes_thinking_blocks():
    async def fake_astream(messages):
        # 1: Thinking block (should be excluded)
        c1 = MagicMock()
        c1.content = ""
        c1.additional_kwargs = {"thinking": "Thinking about heart rate zones..."}
        c1.tool_calls = []
        c1.tool_call_chunks = []
        c1.usage_metadata = None
        yield c1

        # 2: Actual response text
        c2 = MagicMock()
        c2.content = "Hãy khởi động 10 phút."
        c2.additional_kwargs = {}
        c2.tool_calls = []
        c2.tool_call_chunks = []
        c2.usage_metadata = None
        yield c2

    adapter = GeminiCoachModel(api_key="test-key")
    adapter._chat = MagicMock()
    adapter._chat.astream = fake_astream

    req = ModelRequest(
        messages=(ChatMessage(role="user", content="Khởi động thế nào?"),),
        system="Coach",
        max_output_tokens=200,
        call_id=uuid4(),
    )

    events = [ev async for ev in adapter.stream(req)]
    text_events = [ev for ev in events if ev.kind == "text"]

    assert len(text_events) == 1
    assert text_events[0].text == "Hãy khởi động 10 phút."
    assert "Thinking" not in text_events[0].text


@pytest.mark.asyncio
async def test_gemini_adapter_normalizes_usage_once():
    async def fake_astream(messages):
        c1 = MagicMock()
        c1.content = "Đã rõ."
        c1.additional_kwargs = {}
        c1.tool_calls = []
        c1.tool_call_chunks = []
        c1.usage_metadata = None
        yield c1

        c2 = MagicMock()
        c2.content = ""
        c2.additional_kwargs = {}
        c2.tool_calls = []
        c2.tool_call_chunks = []
        c2.usage_metadata = {
            "input_tokens": 120,
            "output_tokens": 15,
            "total_tokens": 135,
            "input_token_details": {"cache_read": 20},
        }
        yield c2

    adapter = GeminiCoachModel(api_key="test-key")
    adapter._chat = MagicMock()
    adapter._chat.astream = fake_astream

    req = ModelRequest(
        messages=(ChatMessage(role="user", content="Ok"),),
        system="Coach",
        max_output_tokens=100,
        call_id=uuid4(),
    )

    events = [ev async for ev in adapter.stream(req)]
    usage_events = [ev for ev in events if ev.kind == "usage"]

    assert len(usage_events) == 1
    u = usage_events[0].usage
    assert u.input_tokens == 120
    assert u.output_tokens == 15
    assert u.cached_tokens == 20


@pytest.mark.asyncio
async def test_gemini_adapter_rejects_tool_calls_in_foundation():
    async def fake_astream(messages):
        c1 = MagicMock()
        c1.content = ""
        c1.additional_kwargs = {}
        c1.tool_calls = [{"name": "calculator", "args": {}}]
        c1.tool_call_chunks = [{"name": "calculator", "args": "{}"}]
        c1.usage_metadata = None
        yield c1

    adapter = GeminiCoachModel(api_key="test-key")
    adapter._chat = MagicMock()
    adapter._chat.astream = fake_astream

    req = ModelRequest(
        messages=(ChatMessage(role="user", content="Tính pace"),),
        system="Coach",
        max_output_tokens=100,
        call_id=uuid4(),
    )

    with pytest.raises(ToolCallsNotSupportedError):
        async for _ in adapter.stream(req):
            pass


@pytest.mark.asyncio
async def test_gemini_adapter_maps_provider_errors_to_stable_local_exception():
    async def fake_astream(messages):
        raise RuntimeError("Google API 503 Service Unavailable: overloaded")
        yield  # make it an async generator

    adapter = GeminiCoachModel(api_key="test-key")
    adapter._chat = MagicMock()
    adapter._chat.astream = fake_astream

    req = ModelRequest(
        messages=(ChatMessage(role="user", content="Chạy"),),
        system="Coach",
        max_output_tokens=100,
        call_id=uuid4(),
    )

    with pytest.raises(CoachModelUpstreamError) as exc_info:
        async for _ in adapter.stream(req):
            pass

    # Never leak raw provider message
    assert "Google API 503" not in str(exc_info.value)
    assert exc_info.value.error_type == "RuntimeError"


@pytest.mark.asyncio
async def test_gemini_adapter_wraps_in_canonical_generation():
    async def fake_astream(messages):
        c = MagicMock()
        c.content = "OK"
        c.additional_kwargs = {}
        c.tool_calls = []
        c.tool_call_chunks = []
        c.usage_metadata = {"input_tokens": 50, "output_tokens": 5}
        yield c

    adapter = GeminiCoachModel(api_key="test-key", model="gemini-3.8-flash")
    adapter._chat = MagicMock()
    adapter._chat.astream = fake_astream

    req = ModelRequest(
        messages=(ChatMessage(role="user", content="Hi"),),
        system="Coach",
        max_output_tokens=100,
        call_id=uuid4(),
    )

    with patch("services.observability.generation") as mock_gen:
        mock_scope = MagicMock()
        mock_gen.return_value.__enter__.return_value = mock_scope

        async for _ in adapter.stream(req):
            pass

        mock_gen.assert_called_once()
        assert mock_gen.call_args.kwargs["feature"] == "coach_chat"
        assert mock_gen.call_args.kwargs["model"] == "gemini-3.8-flash"
        mock_scope.set_usage.assert_called_once()
