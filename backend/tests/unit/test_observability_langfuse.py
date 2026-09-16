"""Langfuse enablement against an in-memory exporter (langfuse_spans fixture)."""

import hashlib
import hmac
import sys

import pytest

from config import settings
from services import observability as obs


def _attrs(span):
    return dict(span.attributes or {})


def _by_name(exporter, name):
    obs.flush()
    matches = [s for s in exporter.get_finished_spans() if s.name == name]
    assert matches, f"no exported span named {name!r}; got {[s.name for s in exporter.get_finished_spans()]}"
    return matches[0]


def test_trace_exports_pseudonymous_ids_trace_name_and_allowlisted_metadata(langfuse_spans):
    with obs.trace("coach_chat.turn", feature="coach_chat", user_id=42, thread_id=7, metadata={"lang": "vi"}):
        with obs.span("retrieval") as retrieval:
            retrieval.set(retrieval_k=6, notes="free text that must not export")

    root = _attrs(_by_name(langfuse_spans, "coach_chat.turn"))
    child = _attrs(_by_name(langfuse_spans, "retrieval"))
    # HMAC-SHA256("test-salt", "42")[:32], derived with the stdlib, not the code under test.
    expected_user = hmac.new(b"test-salt", b"42", hashlib.sha256).hexdigest()[:32]
    expected_session = hmac.new(b"test-salt", b"7", hashlib.sha256).hexdigest()[:32]
    assert root["user.id"] == expected_user
    assert root["session.id"] == expected_session
    assert root["langfuse.trace.name"] == "coach_chat.turn"
    assert child["user.id"] == expected_user
    assert "langfuse.observation.metadata.retrieval_k" in child
    assert "langfuse.observation.metadata.notes" not in child


def test_current_trace_id_matches_the_exported_trace(langfuse_spans):
    with obs.trace("plan_generation", feature="plan_generation"):
        seen = obs.current_trace_id()

    root = _by_name(langfuse_spans, "plan_generation")
    assert seen == format(root.context.trace_id, "032x")


def test_body_exception_propagates_and_the_span_is_marked_as_error(langfuse_spans):
    with pytest.raises(RuntimeError):
        with obs.trace("gear_finder", feature="gear_finder"):
            raise RuntimeError("upstream failed")

    root = _attrs(_by_name(langfuse_spans, "gear_finder"))
    assert "langfuse.observation.metadata.error_type" in root
    assert "RuntimeError" in str(root["langfuse.observation.metadata.error_type"])


def test_record_generation_attaches_usage_and_cost_to_the_enclosing_span(langfuse_spans, monkeypatch):
    monkeypatch.setattr(
        settings, "LLM_PRICES_USD_PER_M", {"m-lf": [{"input": 1.0, "cached_input": 0.5, "output": 2.0}]}
    )
    with obs.span("gemini"):
        obs.record_generation(
            feature="plan_generation",
            model="m-lf",
            usage=obs.Usage(input_tokens=1_000_000, output_tokens=500_000),
            latency_s=1.25,
        )

    attrs = _attrs(_by_name(langfuse_spans, "gemini"))
    assert str(attrs["langfuse.observation.metadata.input_tokens"]) == "1000000"
    assert str(attrs["langfuse.observation.metadata.cost_usd"]) == "2.0"
    assert str(attrs["langfuse.observation.metadata.latency_ms"]) == "1250"


def test_a_failing_client_never_raises_into_callers(langfuse_spans):
    class Exploding:
        def __getattr__(self, name):
            def boom(*args, **kwargs):
                raise RuntimeError("langfuse broke")

            return boom

    # Swapped by hand, not with monkeypatch: the langfuse_spans teardown calls
    # _client.shutdown() before monkeypatch would restore the real client.
    real_client = obs._client
    obs._client = Exploding()
    try:
        with obs.trace("t", feature="coach_chat", user_id=1) as observation:
            observation.set(retrieval_k=1)
            with obs.span("s"):
                obs.record_generation(feature="coach_chat", model="m", usage=obs.Usage(), latency_s=0.1)
        obs.score(trace_id="0" * 32, name="thumbs", value=1.0)
        assert obs.current_trace_id() is None
        obs.flush()
    finally:
        obs._client = real_client


@pytest.fixture
def clean_observability():
    obs._client = None
    yield
    obs._client = None


def test_keys_without_salt_refuse_to_enable(monkeypatch, clean_observability):
    monkeypatch.setattr(settings, "LANGFUSE_PUBLIC_KEY", "pk-lf-nosalt")
    monkeypatch.setattr(settings, "LANGFUSE_SECRET_KEY", "sk-lf-nosalt")
    monkeypatch.setattr(settings, "OBSERVABILITY_ID_SALT", "")

    obs.init()

    assert obs.enabled() is False


def test_missing_packages_degrade_to_disabled(monkeypatch, clean_observability):
    monkeypatch.setattr(settings, "LANGFUSE_PUBLIC_KEY", "pk-lf-nopkg")
    monkeypatch.setattr(settings, "LANGFUSE_SECRET_KEY", "sk-lf-nopkg")
    monkeypatch.setattr(settings, "OBSERVABILITY_ID_SALT", "salt")
    monkeypatch.setitem(sys.modules, "langfuse", None)  # `import langfuse` now raises ImportError

    obs.init()

    assert obs.enabled() is False


def test_langchain_runnables_are_auto_traced_alongside_gemini_calls(langfuse_spans):
    """Sub-project 2 hasn't built the LangGraph agent yet -- a bare RunnableLambda is
    the smallest LangChain construct that proves LangChainInstrumentor is actually
    wired to our shared TracerProvider, ahead of the real agent existing."""
    from langchain_core.runnables import RunnableLambda

    with obs.trace("coach_chat.turn", feature="coach_chat", user_id=1):
        RunnableLambda(lambda x: x.upper()).invoke("hi")

    obs.flush()
    names = [s.name for s in langfuse_spans.get_finished_spans()]
    assert any("RunnableLambda" in n for n in names), f"no LangChain-instrumented span found; got {names}"
