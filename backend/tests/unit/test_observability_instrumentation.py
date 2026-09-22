"""The real OpenInference instrumentor + real Langfuse client, with google-genai's HTTP
layer replaced by httpx.MockTransport. Proves that no athlete content reaches exported
spans (attributes OR events) and pins that streamed calls are auto-traced."""

import asyncio
import json

import httpx
import pytest
from google import genai
from google.genai import errors, types

from services import observability as obs

MODEL = "gemini-3.8-flash"
CANARY = "CANARY-9d41-left-achilles-tendinopathy"
REPLY_CANARY = "REPLY-CANARY-5e2b-ease-off"
FAIL_MARKER = "TRIGGER-429"


def _body():
    return {
        "candidates": [
            {"content": {"role": "model", "parts": [{"text": REPLY_CANARY}]}, "finishReason": "STOP", "index": 0}
        ],
        "usageMetadata": {
            "promptTokenCount": 120,
            "candidatesTokenCount": 8,
            "thoughtsTokenCount": 5,
            "totalTokenCount": 133,
        },
        "modelVersion": MODEL,
    }


def _handler(request: httpx.Request) -> httpx.Response:
    if FAIL_MARKER in request.content.decode():
        return httpx.Response(
            429,
            json={"error": {"code": 429, "message": "Resource has been exhausted.", "status": "RESOURCE_EXHAUSTED"}},
        )
    if request.url.path.endswith(":streamGenerateContent"):
        frame = "data: " + json.dumps(_body()) + "\r\n\r\n"
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, content=frame.encode())
    if request.url.path.endswith(":generateContent"):
        return httpx.Response(200, json=_body())
    return httpx.Response(404, json={"error": {"code": 404, "message": "not stubbed", "status": "NOT_FOUND"}})


def _options(**client_kwargs):
    return types.HttpOptions(retry_options=types.HttpRetryOptions(attempts=1), **client_kwargs)


def _sync_client():
    return genai.Client(
        api_key="test-key", http_options=_options(httpx_client=httpx.Client(transport=httpx.MockTransport(_handler)))
    )


def _async_client():
    return genai.Client(
        api_key="test-key",
        http_options=_options(httpx_async_client=httpx.AsyncClient(transport=httpx.MockTransport(_handler))),
    )


def _exported_text(exporter) -> str:
    obs.flush()
    parts = []
    for span in exporter.get_finished_spans():
        parts.append(span.name)
        parts.extend(f"{k}={v}" for k, v in (span.attributes or {}).items())
        for event in span.events:
            parts.append(event.name)
            parts.extend(f"{k}={v}" for k, v in (event.attributes or {}).items())
    return "\n".join(parts)


def _llm_spans(exporter):
    obs.flush()
    return [s for s in exporter.get_finished_spans() if (s.attributes or {}).get("openinference.span.kind") == "LLM"]


def test_prompt_system_instruction_reply_and_free_text_metadata_never_export(langfuse_spans):
    client = _sync_client()
    with obs.trace("coach_chat.turn", feature="coach_chat", user_id=42, thread_id=7, metadata={"notes": CANARY}):
        with obs.span("generation") as generation:
            generation.set(retrieval_k=6, notes=CANARY)
            client.models.generate_content(
                model=MODEL,
                contents=f"My achilles: {CANARY}",
                config=types.GenerateContentConfig(system_instruction=f"Athlete injury notes: {CANARY}"),
            )

    exported = _exported_text(langfuse_spans)
    assert CANARY not in exported
    assert REPLY_CANARY not in exported
    llm = _llm_spans(langfuse_spans)
    assert llm, "the instrumentor produced no LLM span -- instrumentation is not wired"
    attributes = dict(llm[0].attributes)
    assert MODEL in str(attributes.get("llm.model_name"))
    assert attributes.get("llm.token_count.prompt") == 120


def test_sdk_observation_input_output_and_free_text_metadata_are_dropped(langfuse_spans):
    # Simulates a future caller bypassing the wrapper and using the client directly.
    with obs._client.start_as_current_observation(
        as_type="span", name="direct", input=CANARY, output=CANARY, metadata={"notes": CANARY, "feature": "coach_chat"}
    ):
        pass

    exported = _exported_text(langfuse_spans)
    assert CANARY not in exported
    assert "coach_chat" in exported


def test_a_failing_gemini_call_exports_no_prompt_content(langfuse_spans):
    client = _sync_client()
    with pytest.raises(errors.ClientError):
        with obs.trace("plan_generation", feature="plan_generation"):
            client.models.generate_content(model=MODEL, contents=f"{FAIL_MARKER} {CANARY}")

    assert _llm_spans(langfuse_spans), "failed call produced no LLM span"
    assert CANARY not in _exported_text(langfuse_spans)


def test_sync_streaming_calls_are_auto_traced_without_content(langfuse_spans):
    chunks = list(_sync_client().models.generate_content_stream(model=MODEL, contents=f"Stream: {CANARY}"))

    assert chunks
    assert obs.INSTRUMENTOR_TRACES_STREAMS is True
    assert _llm_spans(langfuse_spans), "instrumentor no longer traces generate_content_stream"
    exported = _exported_text(langfuse_spans)
    assert CANARY not in exported
    assert REPLY_CANARY not in exported


def test_async_streaming_calls_are_auto_traced_without_content(langfuse_spans):
    async def consume():
        stream = await _async_client().aio.models.generate_content_stream(model=MODEL, contents=f"Async: {CANARY}")
        return [chunk async for chunk in stream]

    assert asyncio.run(consume())
    assert _llm_spans(langfuse_spans), "instrumentor no longer traces AsyncModels.generate_content_stream"
    assert CANARY not in _exported_text(langfuse_spans)
