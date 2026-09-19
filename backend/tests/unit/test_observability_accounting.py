"""One canonical billable record is emitted for each explicit model invocation."""

import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import httpx
import pytest
from google import genai
from google.genai import types
from prometheus_client import REGISTRY

from config import settings
from services import observability as obs


def _sample(name, labels):
    return REGISTRY.get_sample_value(name, labels) or 0.0


def _attrs(span):
    return dict(span.attributes or {})


def _finished(exporter):
    obs.flush()
    return exporter.get_finished_spans()


def test_generation_exports_native_usage_and_cost_on_canonical_child_only(langfuse_spans, monkeypatch):
    monkeypatch.setattr(
        settings,
        "LLM_PRICES_USD_PER_M",
        {"gemini-3.8-flash": [{"input": 1.0, "cached_input": 0.5, "output": 2.0}]},
    )

    with obs.span("plan_generation"):
        with obs.generation(
            "gemini",
            feature="plan_generation",
            model="gemini-3.8-flash",
        ) as generation:
            generation.set_usage(
                obs.Usage(
                    input_tokens=1_000_000,
                    output_tokens=250_000,
                    thinking_tokens=250_000,
                    cached_tokens=200_000,
                )
            )

    spans = _finished(langfuse_spans)
    canonical = _attrs(next(span for span in spans if span.name == "gemini"))
    parent = _attrs(next(span for span in spans if span.name == "plan_generation"))
    usage = json.loads(canonical["langfuse.observation.usage_details"])
    costs = json.loads(canonical["langfuse.observation.cost_details"])

    assert canonical["langfuse.observation.type"] == "generation"
    assert canonical["langfuse.observation.model.name"] == "gemini-3.8-flash"
    assert usage == {
        "cached_input": 200_000,
        "input": 800_000,
        "output": 250_000,
        "output_reasoning": 250_000,
        "total": 1_500_000,
    }
    provider_total = 1_000_000 + 250_000 + 250_000
    exported_bucket_total = sum(usage[key] for key in ("input", "cached_input", "output", "output_reasoning"))
    assert usage["total"] == provider_total
    assert exported_bucket_total == provider_total
    assert costs == {"cached_input": 0.1, "input": 0.8, "output": 1.0, "total": 1.9}
    assert "langfuse.observation.usage_details" not in parent
    assert "langfuse.observation.cost_details" not in parent
    assert "langfuse.observation.model.name" not in parent


def test_nested_auto_span_is_debilled_but_unrelated_auto_span_keeps_native_usage(langfuse_spans):
    provider = obs._client._resources.tracer_provider
    tracer = provider.get_tracer("openinference.instrumentation.google_genai")
    native = {
        "openinference.span.kind": "LLM",
        "llm.model_name": "gemini-3.8-flash",
        "llm.token_count.prompt": 123,
        "llm.token_count.completion": 45,
        "llm.token_count.total": 168,
    }

    with obs.generation(
        "gemini",
        feature="plan_generation",
        model="gemini-3.8-flash",
    ) as generation:
        with tracer.start_as_current_span("GenerateContent", attributes=native):
            pass
        with obs._client.start_as_current_observation(
            as_type="generation",
            name="generation",
            model="gemini-3.8-flash",
            usage_details={"input": 123, "output": 45, "total": 168},
            cost_details={"total": 99.0},
        ):
            pass
        generation.set_usage(obs.Usage(input_tokens=123, output_tokens=45))

    with tracer.start_as_current_span("GenerateContentStream", attributes=native):
        pass

    spans = _finished(langfuse_spans)
    nested = _attrs(next(span for span in spans if span.name == "GenerateContent"))
    nested_generation = _attrs(next(span for span in spans if span.name == "generation"))
    unrelated = _attrs(next(span for span in spans if span.name == "GenerateContentStream"))

    assert "llm.model_name" not in nested
    assert not any(key.startswith("llm.token_count.") for key in nested)
    assert "langfuse.observation.model.name" not in nested_generation
    assert "langfuse.observation.usage_details" not in nested_generation
    assert "langfuse.observation.cost_details" not in nested_generation
    assert unrelated["llm.model_name"] == "gemini-3.8-flash"
    assert unrelated["llm.token_count.prompt"] == 123
    assert unrelated["llm.token_count.completion"] == 45


def test_direct_google_sdk_child_keeps_timing_but_canonical_generation_owns_usage(langfuse_spans):
    def handler(_request):
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {"content": {"role": "model", "parts": [{"text": "synthetic"}]}, "finishReason": "STOP"}
                ],
                "usageMetadata": {
                    "promptTokenCount": 120,
                    "candidatesTokenCount": 8,
                    "thoughtsTokenCount": 5,
                    "totalTokenCount": 133,
                },
                "modelVersion": "gemini-3.8-flash",
            },
        )

    client = genai.Client(
        api_key="test-key",
        http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(attempts=1),
            httpx_client=httpx.Client(transport=httpx.MockTransport(handler)),
        ),
    )
    with obs.generation(
        "gemini",
        feature="plan_generation",
        model="gemini-3.8-flash",
    ) as generation:
        response = client.models.generate_content(model="gemini-3.8-flash", contents="synthetic fixture")
        generation.set_usage(obs.Usage.from_genai(response.usage_metadata))

    spans = _finished(langfuse_spans)
    canonical = _attrs(next(span for span in spans if span.name == "gemini"))
    auto = _attrs(next(span for span in spans if span.name == "GenerateContent"))

    assert json.loads(canonical["langfuse.observation.usage_details"])["total"] == 133
    assert auto["openinference.span.kind"] == "LLM"
    assert "llm.model_name" not in auto
    assert not any(key.startswith("llm.token_count.") for key in auto)


def test_private_invocation_identity_reaches_nested_spans_and_never_exports(langfuse_spans):
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    provider = obs._client._resources.tracer_provider
    raw = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(raw))
    tracer = provider.get_tracer("openinference.instrumentation.google_genai")

    with obs.generation("gemini", feature="coach_chat", model="gemini-3.8-flash") as generation:
        with tracer.start_as_current_span("GenerateContent"):
            pass
        generation.set_usage(obs.Usage(input_tokens=1, output_tokens=1))

    raw_spans = raw.get_finished_spans()
    raw_ids = {
        _attrs(span)[obs._INVOCATION_ATTRIBUTE] for span in raw_spans if span.name in {"gemini", "GenerateContent"}
    }
    assert len(raw_ids) == 1

    exported = _finished(langfuse_spans)
    assert all(obs._INVOCATION_ATTRIBUTE not in _attrs(span) for span in exported)
    assert all(obs._INVOCATION_PROOF_ATTRIBUTE not in _attrs(span) for span in exported)


def test_concurrent_generations_do_not_share_invocation_identity():
    barrier = Barrier(2)

    def invoke():
        with obs.generation("gemini", feature="coach_chat", model="gemini-3.8-flash") as generation:
            barrier.wait()
            invocation_id = obs._current_invocation_id.get()
            generation.set_usage(obs.Usage(input_tokens=1, output_tokens=1))
            return invocation_id

    with ThreadPoolExecutor(max_workers=2) as pool:
        ids = list(pool.map(lambda _: invoke(), range(2)))

    assert all(ids)
    assert ids[0] != ids[1]
    assert obs._current_invocation_id.get() is None


def test_exception_without_usage_is_one_failed_unknown_invocation():
    call_labels = {"feature": "gear_finder", "model": "other", "status": "error"}
    unknown_labels = {"feature": "gear_finder", "status": "error"}
    before_calls = _sample("llm_calls_total", call_labels)
    before_unknown = _sample("llm_unknown_usage_calls_total", unknown_labels)

    with pytest.raises(RuntimeError, match="provider failed"):
        with obs.generation("gemini", feature="gear_finder", model="m-exception"):
            raise RuntimeError("provider failed")

    assert _sample("llm_calls_total", call_labels) - before_calls == 1
    assert _sample("llm_unknown_usage_calls_total", unknown_labels) - before_unknown == 1


def test_unknown_usage_exports_no_native_usage_or_zero_cost(langfuse_spans):
    with obs.generation("gemini", feature="coach_chat", model="gemini-3.8-flash"):
        pass

    canonical = _attrs(next(span for span in _finished(langfuse_spans) if span.name == "gemini"))
    assert "langfuse.observation.usage_details" not in canonical
    assert "langfuse.observation.cost_details" not in canonical
    assert "langfuse.observation.metadata.cost_usd" not in canonical


def test_retry_records_each_provider_invocation_once():
    first = {"feature": "nutrition_lab", "model": "other", "status": "error"}
    second = {"feature": "nutrition_lab", "model": "other", "status": "ok"}
    before_first = _sample("llm_calls_total", first)
    before_second = _sample("llm_calls_total", second)

    with pytest.raises(TimeoutError):
        with obs.generation("gemini", feature="nutrition_lab", model="m-retry"):
            raise TimeoutError
    with obs.generation("gemini", feature="nutrition_lab", model="m-retry") as generation:
        generation.set_usage(obs.Usage(input_tokens=10, output_tokens=3))

    assert _sample("llm_calls_total", first) - before_first == 1
    assert _sample("llm_calls_total", second) - before_second == 1


def test_cached_and_thinking_usage_are_accounted_at_their_distinct_rates(monkeypatch):
    monkeypatch.setattr(
        settings,
        "LLM_PRICES_USD_PER_M",
        {"m-cached-thinking": [{"input": 1.0, "cached_input": 0.5, "output": 2.0}]},
    )
    labels = {"feature": "evaluation", "model": "other"}
    before_cost = _sample("llm_cost_usd_total", labels)
    before_cached = _sample("llm_tokens_total", {**labels, "kind": "cached"})
    before_thinking = _sample("llm_tokens_total", {**labels, "kind": "thinking"})

    with obs.generation("gemini", feature="evaluation", model="m-cached-thinking") as generation:
        generation.set_usage(
            obs.Usage(
                input_tokens=1_000_000,
                output_tokens=250_000,
                thinking_tokens=250_000,
                cached_tokens=200_000,
            )
        )

    assert _sample("llm_cost_usd_total", labels) - before_cost == 1.9
    assert _sample("llm_tokens_total", {**labels, "kind": "cached"}) - before_cached == 200_000
    assert _sample("llm_tokens_total", {**labels, "kind": "thinking"}) - before_thinking == 250_000


def test_sample_rate_zero_still_accounts_exactly_once(monkeypatch):
    from openinference.instrumentation.google_genai import GoogleGenAIInstrumentor
    from openinference.instrumentation.langchain import LangChainInstrumentor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    previous_client, obs._client = obs._client, None
    previous_failed, obs._init_failed = obs._init_failed, False
    client = None
    exporter = InMemorySpanExporter()
    monkeypatch.setattr(settings, "LANGFUSE_PUBLIC_KEY", f"pk-sampled-out-{uuid.uuid4().hex}")
    monkeypatch.setattr(settings, "LANGFUSE_SECRET_KEY", "sk-sampled-out")
    monkeypatch.setattr(settings, "OBSERVABILITY_ID_SALT", "sampled-out-salt")
    monkeypatch.setattr(settings, "LANGFUSE_SAMPLE_RATE", 0.0)
    labels = {"feature": "embeddings", "model": "other"}
    before_calls = _sample("llm_calls_total", {**labels, "status": "ok"})
    before_latency = _sample("llm_latency_seconds_count", labels)

    try:
        obs.init(span_exporter=exporter)
        client = obs._client
        with obs.generation("gemini", feature="embeddings", model="m-sampled-out") as generation:
            generation.set_usage(obs.Usage(input_tokens=20))
        obs.flush()
    finally:
        GoogleGenAIInstrumentor().uninstrument()
        LangChainInstrumentor().uninstrument()
        if client is not None:
            client.shutdown()
        obs._client = previous_client
        obs._init_failed = previous_failed

    assert _sample("llm_calls_total", {**labels, "status": "ok"}) - before_calls == 1
    assert _sample("llm_latency_seconds_count", labels) - before_latency == 1
    assert exporter.get_finished_spans() == ()


def test_false_known_flag_keeps_usage_unknown():
    unknown_labels = {"feature": "coach_chat", "status": "ok"}
    before_unknown = _sample("llm_unknown_usage_calls_total", unknown_labels)

    with obs.generation("gemini", feature="coach_chat", model="m-withheld") as generation:
        generation.set_usage(obs.Usage(input_tokens=99), known=False)

    assert _sample("llm_unknown_usage_calls_total", unknown_labels) - before_unknown == 1
