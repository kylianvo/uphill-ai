"""The coach LangGraph's nodes are exported as spans through the masked Langfuse
pipeline, and no question/reply content leaks into any span attribute or event."""

import uuid

import pytest

from services import observability
from services.coach_chat import run_turn
from services.coach_model import FakeCoachModel, ModelEvent
from services.observability import Usage

QUESTION_CANARY = "SPAN-CANARY-Q-7f3a what is my week"
REPLY_CANARY = "SPAN-CANARY-R-91bd easy week ahead"


def _exported_text(exporter) -> str:
    observability.flush()
    parts = []
    for span in exporter.get_finished_spans():
        parts.append(span.name)
        parts.extend(f"{k}={v}" for k, v in (span.attributes or {}).items())
        for event in span.events:
            parts.append(event.name)
            parts.extend(f"{k}={v}" for k, v in (event.attributes or {}).items())
    return "\n".join(parts)


@pytest.mark.asyncio
async def test_graph_nodes_are_exported_as_masked_spans(langfuse_spans, auth_headers):
    model = FakeCoachModel(
        responses=[
            [ModelEvent(kind="tool_call", tool_call={"id": "c1", "name": "get_week", "args": {}})],
            [
                ModelEvent(kind="text", text=REPLY_CANARY),
                ModelEvent(kind="usage", usage=Usage(input_tokens=10, output_tokens=5)),
            ],
        ]
    )
    request = {"request_id": str(uuid.uuid4()), "message": QUESTION_CANARY, "lang": "en"}
    async for _ in run_turn(user={"id": auth_headers["user_id"]}, request=request, model=model):
        pass

    observability.flush()
    spans = langfuse_spans.get_finished_spans()

    # The coach graph's node identifiers (retrieve/generate/tools/etc.) are now on
    # services/observability_policy.py's _SPAN_NAMES allowlist, so they pass through the
    # masked Langfuse pipeline under their real names instead of the generic "operation"
    # placeholder.
    names = {span.name for span in spans}
    assert {"retrieve", "generate", "tools"} <= names, sorted(names)

    kinds = [span.attributes.get("openinference.span.kind") for span in spans]
    # retrieve, generate (x2 rounds), tools node wrapper, the _tools_condition routing
    # step, and the LangGraph root are all CHAIN-kind; the get_week tool invocation
    # itself is TOOL-kind. Kept alongside the name check as extra node-level-granularity
    # evidence.
    assert kinds.count("TOOL") >= 1, kinds
    assert kinds.count("CHAIN") >= 3, kinds

    exported = _exported_text(langfuse_spans)
    assert "SPAN-CANARY-Q-7f3a" not in exported
    assert "SPAN-CANARY-R-91bd" not in exported
