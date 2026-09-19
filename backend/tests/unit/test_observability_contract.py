"""The observability API both parallel tracks code against. These behaviours must
hold in the no-op contract AND after the Langfuse implementation lands."""

from types import SimpleNamespace

import pytest

from services import observability as obs


def test_usage_from_genai_maps_every_token_field():
    meta = SimpleNamespace(
        prompt_token_count=1200,
        candidates_token_count=300,
        thoughts_token_count=150,
        cached_content_token_count=400,
    )

    assert obs.Usage.from_genai(meta) == obs.Usage(
        input_tokens=1200, output_tokens=300, thinking_tokens=150, cached_tokens=400
    )


def test_usage_from_genai_treats_missing_counts_as_zero():
    meta = SimpleNamespace(
        prompt_token_count=10,
        candidates_token_count=None,
        thoughts_token_count=None,
        cached_content_token_count=None,
    )

    assert obs.Usage.from_genai(meta) == obs.Usage(input_tokens=10)
    assert obs.Usage.from_genai(None) == obs.Usage()


def test_trace_and_span_never_swallow_the_callers_exception():
    with pytest.raises(ValueError, match="boom"):
        with obs.trace("coach_chat.turn", feature="coach_chat", user_id=1, thread_id=2):
            with obs.span("retrieval") as observation:
                observation.set(retrieval_k=6)
                raise ValueError("boom")


def test_disabled_mode_is_safe_to_call_everywhere():
    obs.init()  # the test environment has no Langfuse keys

    assert obs.enabled() is False
    assert obs.current_trace_id() is None
    obs.score(trace_id="0" * 32, name="thumbs", value=1.0)
    obs.flush()
