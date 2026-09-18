"""record_generation feeds the Prometheus llm_* series whether or not Langfuse is on.
Each test uses its own model label so counters don't leak between tests."""

from prometheus_client import REGISTRY

from config import settings
from services import observability as obs


def _sample(name, labels):
    return REGISTRY.get_sample_value(name, labels) or 0.0


def test_records_calls_tokens_latency_and_cost(monkeypatch):
    monkeypatch.setattr(
        settings, "LLM_PRICES_USD_PER_M", {"m-metrics-ok": [{"input": 1.0, "cached_input": 0.5, "output": 2.0}]}
    )
    usage = obs.Usage(input_tokens=1_000_000, output_tokens=250_000, thinking_tokens=250_000)

    cost = obs.record_generation(feature="plan_generation", model="m-metrics-ok", usage=usage, latency_s=1.5)

    assert cost == 2.0
    labels = {"feature": "plan_generation", "model": "m-metrics-ok"}
    assert _sample("llm_calls_total", {**labels, "status": "ok"}) == 1
    assert _sample("llm_tokens_total", {**labels, "kind": "input"}) == 1_000_000
    assert _sample("llm_tokens_total", {**labels, "kind": "output"}) == 250_000
    assert _sample("llm_tokens_total", {**labels, "kind": "thinking"}) == 250_000
    assert _sample("llm_cost_usd_total", labels) == 2.0
    assert _sample("llm_latency_seconds_count", labels) == 1


def test_error_status_is_labelled(monkeypatch):
    obs.record_generation(
        feature="gear_finder", model="m-metrics-err", usage=obs.Usage(), latency_s=0.2, status="error"
    )

    assert _sample("llm_calls_total", {"feature": "gear_finder", "model": "m-metrics-err", "status": "error"}) == 1


def test_unknown_feature_is_labelled_other():
    obs.record_generation(feature="made_up_feature", model="m-metrics-other", usage=obs.Usage(), latency_s=0.1)

    assert _sample("llm_calls_total", {"feature": "other", "model": "m-metrics-other", "status": "ok"}) == 1
    assert _sample("llm_calls_total", {"feature": "made_up_feature", "model": "m-metrics-other", "status": "ok"}) == 0


def test_unpriced_model_counts_as_unpriced_and_adds_no_cost():
    cost = obs.record_generation(
        feature="coach_chat", model="m-metrics-unpriced", usage=obs.Usage(input_tokens=500), latency_s=0.1
    )

    assert cost is None
    assert _sample("llm_unpriced_calls_total", {"model": "m-metrics-unpriced"}) == 1
    assert _sample("llm_cost_usd_total", {"feature": "coach_chat", "model": "m-metrics-unpriced"}) == 0


def test_a_broken_metric_never_raises_into_the_caller(monkeypatch):
    class Exploding:
        def labels(self, **kwargs):
            raise RuntimeError("registry broke")

    monkeypatch.setattr(obs, "llm_calls_total", Exploding())

    obs.record_generation(feature="coach_chat", model="m-metrics-broken", usage=obs.Usage(), latency_s=0.1)


def test_generation_with_missing_usage_counts_unknown_not_zero_cost():
    labels = {"feature": "coach_chat", "status": "ok"}
    before_unknown = _sample("llm_unknown_usage_calls_total", labels)
    before_calls = _sample(
        "llm_calls_total",
        {"feature": "coach_chat", "model": "m-missing-usage", "status": "ok"},
    )

    with obs.generation("gemini", feature="coach_chat", model="m-missing-usage"):
        pass

    assert _sample("llm_unknown_usage_calls_total", labels) - before_unknown == 1
    assert (
        _sample(
            "llm_calls_total",
            {"feature": "coach_chat", "model": "m-missing-usage", "status": "ok"},
        )
        - before_calls
        == 1
    )
    assert _sample("llm_cost_usd_total", {"feature": "coach_chat", "model": "m-missing-usage"}) == 0


def test_generation_reports_monotonic_cumulative_stream_usage_once(monkeypatch):
    monkeypatch.setattr(
        settings,
        "LLM_PRICES_USD_PER_M",
        {"m-stream": [{"input": 1.0, "cached_input": 0.5, "output": 2.0}]},
    )
    labels = {"feature": "plan_generation", "model": "m-stream"}
    before_calls = _sample("llm_calls_total", {**labels, "status": "ok"})
    before_input = _sample("llm_tokens_total", {**labels, "kind": "input"})
    before_output = _sample("llm_tokens_total", {**labels, "kind": "output"})
    before_latency = _sample("llm_latency_seconds_count", labels)

    with obs.generation("gemini", feature="plan_generation", model="m-stream") as generation:
        generation.set_usage(obs.Usage(input_tokens=100, output_tokens=10))
        generation.set_usage(obs.Usage(input_tokens=100, output_tokens=25))
        generation.set_usage(obs.Usage(input_tokens=90, output_tokens=20))

    assert _sample("llm_calls_total", {**labels, "status": "ok"}) - before_calls == 1
    assert _sample("llm_tokens_total", {**labels, "kind": "input"}) - before_input == 100
    assert _sample("llm_tokens_total", {**labels, "kind": "output"}) - before_output == 25
    assert _sample("llm_latency_seconds_count", labels) - before_latency == 1
