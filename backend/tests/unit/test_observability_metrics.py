"""record_generation feeds bounded Prometheus llm_* series whether or not Langfuse is on."""

import pytest
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
    labels = {"feature": "plan_generation", "model": "other"}
    before_calls = _sample("llm_calls_total", {**labels, "status": "ok"})
    before_input = _sample("llm_tokens_total", {**labels, "kind": "input"})
    before_output = _sample("llm_tokens_total", {**labels, "kind": "output"})
    before_thinking = _sample("llm_tokens_total", {**labels, "kind": "thinking"})
    before_cost = _sample("llm_cost_usd_total", labels)
    before_latency = _sample("llm_latency_seconds_count", labels)

    cost = obs.record_generation(feature="plan_generation", model="m-metrics-ok", usage=usage, latency_s=1.5)

    assert cost == 2.0
    assert _sample("llm_calls_total", {**labels, "status": "ok"}) - before_calls == 1
    assert _sample("llm_tokens_total", {**labels, "kind": "input"}) - before_input == 1_000_000
    assert _sample("llm_tokens_total", {**labels, "kind": "output"}) - before_output == 250_000
    assert _sample("llm_tokens_total", {**labels, "kind": "thinking"}) - before_thinking == 250_000
    assert _sample("llm_cost_usd_total", labels) - before_cost == 2.0
    assert _sample("llm_latency_seconds_count", labels) - before_latency == 1


def test_error_status_is_labelled(monkeypatch):
    labels = {"feature": "gear_finder", "model": "other", "status": "error"}
    before = _sample("llm_calls_total", labels)

    obs.record_generation(
        feature="gear_finder", model="m-metrics-err", usage=obs.Usage(), latency_s=0.2, status="error"
    )

    assert _sample("llm_calls_total", labels) - before == 1


@pytest.mark.parametrize("status", ["error", "attempt", "success", "used", "fallback"])
def test_record_generation_preserves_closed_compatibility_status_labels(status):
    labels = {"feature": "coach_chat", "model": "gemini-3.8-flash", "status": status}
    before = _sample("llm_calls_total", labels)

    obs.record_generation(
        feature="coach_chat",
        model="gemini-3.8-flash",
        usage=obs.Usage(),
        latency_s=0.1,
        status=status,
    )

    assert _sample("llm_calls_total", labels) - before == 1


@pytest.mark.parametrize(
    "unknown_status",
    [
        pytest.param("timeout-error-canary", id="error-like"),
        pytest.param("", id="empty"),
        pytest.param(None, id="none"),
        pytest.param(["error"], id="non-string"),
    ],
)
def test_unknown_status_is_bounded_other_not_success(unknown_status):
    other_labels = {"feature": "coach_chat", "model": "gemini-3.8-flash", "status": "other"}
    ok_labels = {"feature": "coach_chat", "model": "gemini-3.8-flash", "status": "ok"}
    before_other = _sample("llm_calls_total", other_labels)
    before_ok = _sample("llm_calls_total", ok_labels)

    obs.record_generation(
        feature="coach_chat",
        model="gemini-3.8-flash",
        usage=obs.Usage(),
        latency_s=0.1,
        status=unknown_status,
    )

    assert _sample("llm_calls_total", other_labels) - before_other == 1
    assert _sample("llm_calls_total", ok_labels) - before_ok == 0
    assert (
        _sample(
            "llm_calls_total",
            {"feature": "coach_chat", "model": "gemini-3.8-flash", "status": str(unknown_status)},
        )
        == 0
    )


def test_arbitrary_models_share_bounded_other_metric_labels(monkeypatch):
    models = ("attacker-model-alpha", "attacker-model-beta")
    monkeypatch.setattr(
        settings,
        "LLM_PRICES_USD_PER_M",
        {model: [{"input": 1.0, "cached_input": 0.5, "output": 2.0}] for model in models},
    )
    call_labels = {"feature": "coach_chat", "model": "other", "status": "ok"}
    metric_labels = {"feature": "coach_chat", "model": "other"}
    before_calls = _sample("llm_calls_total", call_labels)
    before_tokens = _sample("llm_tokens_total", {**metric_labels, "kind": "input"})
    before_latency = _sample("llm_latency_seconds_count", metric_labels)
    before_cost = _sample("llm_cost_usd_total", metric_labels)

    for model in models:
        obs.record_generation(
            feature="coach_chat",
            model=model,
            usage=obs.Usage(input_tokens=1_000_000),
            latency_s=0.1,
        )

    assert _sample("llm_calls_total", call_labels) - before_calls == 2
    assert _sample("llm_tokens_total", {**metric_labels, "kind": "input"}) - before_tokens == 2_000_000
    assert _sample("llm_latency_seconds_count", metric_labels) - before_latency == 2
    assert _sample("llm_cost_usd_total", metric_labels) - before_cost == 2.0
    for model in models:
        assert _sample("llm_calls_total", {"feature": "coach_chat", "model": model, "status": "ok"}) == 0
        assert _sample("llm_tokens_total", {"feature": "coach_chat", "model": model, "kind": "input"}) == 0
        assert _sample("llm_latency_seconds_count", {"feature": "coach_chat", "model": model}) == 0
        assert _sample("llm_cost_usd_total", {"feature": "coach_chat", "model": model}) == 0


def test_unknown_feature_is_labelled_other():
    labels = {"feature": "other", "model": "other", "status": "ok"}
    before = _sample("llm_calls_total", labels)

    obs.record_generation(feature="made_up_feature", model="m-metrics-other", usage=obs.Usage(), latency_s=0.1)

    assert _sample("llm_calls_total", labels) - before == 1
    assert _sample("llm_calls_total", {"feature": "made_up_feature", "model": "m-metrics-other", "status": "ok"}) == 0


def test_unpriced_model_counts_as_unpriced_and_adds_no_cost():
    before_unpriced = _sample("llm_unpriced_calls_total", {"model": "other"})
    before_cost = _sample("llm_cost_usd_total", {"feature": "coach_chat", "model": "other"})

    cost = obs.record_generation(
        feature="coach_chat", model="m-metrics-unpriced", usage=obs.Usage(input_tokens=500), latency_s=0.1
    )

    assert cost is None
    assert _sample("llm_unpriced_calls_total", {"model": "other"}) - before_unpriced == 1
    assert _sample("llm_unpriced_calls_total", {"model": "m-metrics-unpriced"}) == 0
    assert _sample("llm_cost_usd_total", {"feature": "coach_chat", "model": "other"}) - before_cost == 0


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
        {"feature": "coach_chat", "model": "other", "status": "ok"},
    )

    with obs.generation("gemini", feature="coach_chat", model="m-missing-usage"):
        pass

    assert _sample("llm_unknown_usage_calls_total", labels) - before_unknown == 1
    assert (
        _sample(
            "llm_calls_total",
            {"feature": "coach_chat", "model": "other", "status": "ok"},
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
    labels = {"feature": "plan_generation", "model": "other"}
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
