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

    # The LangChain instrumentor does see the LangGraph run -- confirmed by temporarily
    # intercepting services.observability_policy.sanitize_span_envelope during diagnosis,
    # which showed the real (pre-mask) span names: 'retrieve', '_tools_condition',
    # 'generate', 'get_week' (the tool call), 'tools', '_tools_condition', 'generate',
    # 'LangGraph' (the graph root) -- exactly the retrieve -> generate -> tools -> generate
    # path this test drives. But services/observability_policy.py's `_SPAN_NAMES` is a
    # default-deny allowlist for span *names* specifically, and none of the coach graph's
    # node names are on it, so every one of them is exported as the generic "operation"
    # placeholder. That masking rule is out of scope for this task (task-2-brief.md: modify
    # observability.py only, for instrumentor wiring, "masking rules unchanged"), so this
    # test asserts node-level export via the one identity signal that *is* allowlisted --
    # `openinference.span.kind` -- instead of by name.
    names = {span.name for span in spans}
    assert names == {"operation"}, sorted(names)

    kinds = [span.attributes.get("openinference.span.kind") for span in spans]
    # retrieve, generate (x2 rounds), tools node wrapper, the _tools_condition routing
    # step, and the LangGraph root are all CHAIN-kind; the get_week tool invocation
    # itself is TOOL-kind. Asserting both kinds appear, with enough CHAIN spans to cover
    # more than just the root, is the node-level-granularity check available without
    # touching the name allowlist.
    assert kinds.count("TOOL") >= 1, kinds
    assert kinds.count("CHAIN") >= 3, kinds

    exported = _exported_text(langfuse_spans)
    assert "SPAN-CANARY-Q-7f3a" not in exported
    assert "SPAN-CANARY-R-91bd" not in exported
