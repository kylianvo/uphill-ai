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
    previous_client, obs._client = obs._client, None
    previous_init_failed, obs._init_failed = obs._init_failed, False
    try:
        yield
    finally:
        obs._client = previous_client
        obs._init_failed = previous_init_failed


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


def test_generation_links_a_langfuse_prompt_by_name_and_version(langfuse_spans):
    prompt = obs.PromptTemplate(name="coach_chat", version="3", template="", source="langfuse")
    with obs.generation("generation", feature="coach_chat", model="gemini-3.8-flash", prompt=prompt):
        pass

    attrs = _attrs(_by_name(langfuse_spans, "generation"))
    assert attrs["langfuse.observation.prompt.name"] == "coach_chat"
    assert attrs["langfuse.observation.prompt.version"] == 3


def test_generation_does_not_link_a_local_fallback_prompt(langfuse_spans):
    prompt = obs.PromptTemplate(name="coach_chat", version="local", template="", source="local_fallback")
    with obs.generation("generation", feature="coach_chat", model="gemini-3.8-flash", prompt=prompt):
        pass

    attrs = _attrs(_by_name(langfuse_spans, "generation"))
    assert "langfuse.observation.prompt.name" not in attrs
    assert "langfuse.observation.prompt.version" not in attrs


def test_compile_prompt_fills_variables_in_one_pass():
    tpl = obs.PromptTemplate(name="gear_finder", version="1", template="A {{x}} B {{y}} {{z}}", source="langfuse")
    # A value that itself looks like a placeholder is not re-substituted; unknown ones stay literal.
    assert obs.compile_prompt(tpl, {"x": "{{y}}", "y": 2}) == "A {{y}} B 2 {{z}}"


def test_load_prompt_rejects_a_langfuse_version_that_drops_a_variable(monkeypatch):
    remote = obs.PromptTemplate(name="gear_finder", version="4", template="no vars here", source="langfuse")
    monkeypatch.setattr(obs, "get_prompt_template", lambda *a, **k: remote)

    tpl = obs.load_prompt("gear_finder", "catalog: {{catalog_context}}")

    assert tpl.source == "local_fallback"
    assert tpl.template == "catalog: {{catalog_context}}"


def test_load_prompt_keeps_a_langfuse_version_with_every_variable(monkeypatch):
    remote = obs.PromptTemplate(name="gear_finder", version="4", template="new {{catalog_context}}", source="langfuse")
    monkeypatch.setattr(obs, "get_prompt_template", lambda *a, **k: remote)

    assert obs.load_prompt("gear_finder", "catalog: {{catalog_context}}") is remote


@pytest.fixture
def release_sha(monkeypatch):
    monkeypatch.setattr(settings, "LANGFUSE_RELEASE", "52d941a")


def test_traces_carry_the_configured_release(release_sha, langfuse_spans):
    with obs.trace("plan_generation", feature="plan_generation"):
        pass

    assert _attrs(_by_name(langfuse_spans, "plan_generation"))["langfuse.release"] == "52d941a"


def test_generation_exports_first_token_time_once(langfuse_spans):
    with obs.generation("generation", feature="coach_chat", model="gemini-3.8-flash") as gen:
        gen.mark_first_token()
        gen.mark_first_token()  # no-op: the first call wins

    attrs = _attrs(_by_name(langfuse_spans, "generation"))
    assert attrs["langfuse.observation.completion_start_time"].startswith('"20')
