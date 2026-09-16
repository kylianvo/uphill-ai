"""LLM observability (Langfuse traces + Prometheus token/cost) behind one small API.

This is the ONLY module allowed to import langfuse, openinference or opentelemetry --
the services/mcp_client.py containment pattern. Every other module calls the
functions below. See docs/superpowers/specs/llm-observability-design.md.

Contract stage: these signatures are what sub-projects 1 and 2 code against. Until
the implementation lands, every function is a no-op returning its disabled-mode value.
"""

import contextlib
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

from config import settings
from log_utils import get_logger
from services import observability_policy as policy
from telemetry import (
    llm_calls_total,
    llm_cost_usd_total,
    llm_latency_seconds,
    llm_tokens_total,
    llm_unpriced_calls_total,
)

logger = get_logger(__name__)

FEATURES = frozenset(
    {
        "coach_chat",
        "chat_summary",
        "plan_generation",
        "workout_ai_create",
        "block_narrative",
        "gear_finder",
        "nutrition_lab",
        "kb_distill",
        "knowledge_cards",
    }
)

_warned: set[str] = set()


def _warn_once(event: str, exc: BaseException) -> None:
    """Log an observability failure once per (event, exception type). Never logs the
    exception message: it can carry prompt or athlete content."""
    key = f"{event}:{type(exc).__name__}"
    if key in _warned:
        return
    _warned.add(key)
    logger.warning(
        "observability degraded",
        extra={"fields": {"service": "observability", "event": event, "error_type": type(exc).__name__}},
    )


@dataclass(frozen=True)
class Usage:
    input_tokens: int = 0  # prompt_token_count (includes cached tokens)
    output_tokens: int = 0  # candidates_token_count
    thinking_tokens: int = 0  # thoughts_token_count
    cached_tokens: int = 0  # cached_content_token_count

    @classmethod
    def from_genai(cls, usage_metadata: Any) -> "Usage":
        if usage_metadata is None:
            return cls()
        return cls(
            input_tokens=getattr(usage_metadata, "prompt_token_count", None) or 0,
            output_tokens=getattr(usage_metadata, "candidates_token_count", None) or 0,
            thinking_tokens=getattr(usage_metadata, "thoughts_token_count", None) or 0,
            cached_tokens=getattr(usage_metadata, "cached_content_token_count", None) or 0,
        )


def cost_usd(model: str, usage: Usage, on: date | None = None) -> float | None:
    """USD cost of one call, or None when `model` has no price window covering `on`
    (UTC today by default). prompt_token_count includes cached tokens, so cached
    tokens are subtracted from the input bill and charged at the cached rate."""
    day = on or datetime.now(UTC).date()
    for window in settings.LLM_PRICES_USD_PER_M.get(model, []):
        starts, ends = window.get("from"), window.get("until")
        if starts and day < date.fromisoformat(starts):
            continue
        if ends and day > date.fromisoformat(ends):
            continue
        uncached = max(usage.input_tokens - usage.cached_tokens, 0)
        total = (
            uncached * window["input"]
            + usage.cached_tokens * window["cached_input"]
            + (usage.output_tokens + usage.thinking_tokens) * window["output"]
        )
        return round(total / 1_000_000, 6)
    return None


class Observation:
    """Handle yielded by trace()/span(). set() attaches allowlisted metadata only."""

    def __init__(self, handle: Any = None) -> None:
        self._handle = handle

    def set(self, **metadata: Any) -> None:
        if self._handle is None:
            return
        try:
            self._handle.update(metadata=policy.filter_metadata(metadata))
        except Exception as exc:
            _warn_once("observation_set", exc)


_NOOP = Observation()

# openinference-instrumentation-google-genai 1.4.7 wraps Models/AsyncModels
# .generate_content AND .generate_content_stream, so streamed Gemini calls are
# auto-traced too. Pinned by tests/unit/test_observability_instrumentation.py.
INSTRUMENTOR_TRACES_STREAMS = True

_client: Any = None


def enabled() -> bool:
    return _client is not None


def pseudonym(value: int | str) -> str:
    return policy.pseudonym(value, settings.OBSERVABILITY_ID_SALT)


def _mask(*, data: Any, **kwargs: Any) -> Any:
    try:
        return policy.mask_payload(data, settings.LANGFUSE_EXPORT_CONTENT)
    except Exception as exc:
        _warn_once("mask", exc)
        return None


def _mask_otel_spans(*, params: Any, **kwargs: Any) -> Any:
    from langfuse.types import MaskOtelSpansResult, OtelSpanPatch

    try:
        patches = {}
        for identifier, span_data in params.spans.items():
            deletes, sets = policy.otel_patch(dict(span_data.attributes or {}), settings.LANGFUSE_EXPORT_CONTENT)
            if deletes or sets:
                patches[identifier] = OtelSpanPatch(set_attributes=sets, delete_attributes=tuple(deletes))
        return MaskOtelSpansResult(span_patches=patches) if patches else None
    except Exception as exc:
        # Fail closed: if the policy itself breaks, export spans with no attributes at all.
        _warn_once("mask_otel_spans", exc)
        return MaskOtelSpansResult(
            span_patches={
                identifier: OtelSpanPatch(
                    set_attributes={}, delete_attributes=tuple((span_data.attributes or {}).keys())
                )
                for identifier, span_data in params.spans.items()
            }
        )


def init(*, span_exporter: Any = None) -> None:
    """Enable Langfuse tracing when configured. Never raises. The SDK imports live here,
    inside try/except, so a stale prod image without them degrades to disabled."""
    global _client
    if _client is not None or not (settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY):
        return
    if not settings.OBSERVABILITY_ID_SALT:
        logger.error(
            "observability disabled: OBSERVABILITY_ID_SALT is required when Langfuse keys are set",
            extra={"fields": {"service": "observability", "event": "missing_salt"}},
        )
        return
    try:
        from langfuse import Langfuse
        from openinference.instrumentation import TraceConfig
        from openinference.instrumentation.google_genai import GoogleGenAIInstrumentor
        from openinference.instrumentation.langchain import LangChainInstrumentor
        from opentelemetry.sdk.trace import TracerProvider
    except ImportError as exc:
        _warn_once("import", exc)
        return
    try:
        # Our own provider, shared by Langfuse and both instrumentors: nothing global is touched.
        provider = TracerProvider()
        client = Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            base_url=settings.LANGFUSE_BASE_URL,
            environment=settings.LANGFUSE_ENVIRONMENT,
            sample_rate=settings.LANGFUSE_SAMPLE_RATE,
            timeout=settings.LANGFUSE_TIMEOUT,
            tracer_provider=provider,
            mask=_mask,
            mask_otel_spans=_mask_otel_spans,
            span_exporter=span_exporter,
        )
        hide = not settings.LANGFUSE_EXPORT_CONTENT
        trace_config = TraceConfig(
            hide_inputs=hide,
            hide_outputs=hide,
            hide_input_messages=hide,
            hide_output_messages=hide,
            hide_input_text=hide,
            hide_output_text=hide,
            hide_llm_invocation_parameters=hide,
            hide_llm_tools=hide,
            hide_prompts=hide,
            hide_choices=hide,
            hide_embeddings_text=hide,
            hide_embeddings_vectors=hide,
        )
        # Plan Gen/Gear/Nutrition call google.genai directly; the chat agent (sub-project 2)
        # runs on LangGraph -- both instrumentors share this provider, so every feature's
        # spans land in the same masked Langfuse pipeline regardless of which SDK it uses.
        GoogleGenAIInstrumentor().instrument(tracer_provider=provider, config=trace_config)
        LangChainInstrumentor().instrument(tracer_provider=provider, config=trace_config)
        _client = client
        logger.info("observability enabled", extra={"fields": {"service": "observability", "event": "enabled"}})
    except Exception as exc:
        _warn_once("init", exc)


def _close(stack: contextlib.ExitStack) -> None:
    try:
        stack.close()
    except Exception as exc:
        _warn_once("span_end", exc)


@contextlib.contextmanager
def _observed(open_contexts: Any, event: str) -> Iterator[Observation]:
    """Enter the Langfuse context managers produced by open_contexts(stack), yield an
    Observation, and never let observability failures reach the caller -- while the
    caller's own exceptions always propagate. Spans are closed without exception info
    so exception messages (which can carry content) are never recorded on our spans;
    the error class goes into allowlisted metadata instead."""
    observation = _NOOP
    stack = contextlib.ExitStack()
    if _client is not None:
        try:
            observation = Observation(open_contexts(stack))
        except Exception as exc:
            _close(stack)
            stack = contextlib.ExitStack()
            _warn_once(event, exc)
    try:
        yield observation
    except BaseException as body_exc:
        observation.set(status="error", error_type=type(body_exc).__name__)
        raise
    finally:
        _close(stack)


@contextlib.contextmanager
def trace(
    name: str,
    *,
    feature: str,
    user_id: int | None = None,
    thread_id: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> Iterator[Observation]:
    def open_contexts(stack: contextlib.ExitStack) -> Any:
        from langfuse import propagate_attributes

        stack.enter_context(
            propagate_attributes(
                user_id=pseudonym(user_id) if user_id is not None else None,
                session_id=pseudonym(thread_id) if thread_id is not None else None,
                trace_name=name,
            )
        )
        label = feature if feature in FEATURES else "other"
        return stack.enter_context(
            _client.start_as_current_observation(
                as_type="span", name=name, metadata=policy.filter_metadata({**(metadata or {}), "feature": label})
            )
        )

    with _observed(open_contexts, "trace_start") as observation:
        yield observation


@contextlib.contextmanager
def span(name: str, *, metadata: dict[str, Any] | None = None) -> Iterator[Observation]:
    def open_contexts(stack: contextlib.ExitStack) -> Any:
        return stack.enter_context(
            _client.start_as_current_observation(as_type="span", name=name, metadata=policy.filter_metadata(metadata))
        )

    with _observed(open_contexts, "span_start") as observation:
        yield observation


def record_generation(
    *,
    feature: str,
    model: str,
    usage: Usage,
    latency_s: float,
    streaming: bool = False,
    status: str = "ok",
) -> float | None:
    """Record one Gemini call in the Prometheus llm_* series and return its USD cost
    (None when unpriced). Always records, whether or not Langfuse is enabled.

    `streaming` states a fact about the call. It changes nothing today: the pinned
    OpenInference instrumentor auto-traces streamed and non-streamed calls alike
    (see INSTRUMENTOR_TRACES_STREAMS)."""
    label = feature if feature in FEATURES else "other"
    cost: float | None = None
    try:
        llm_calls_total.labels(feature=label, model=model, status=status).inc()
        for kind, count in (
            ("input", usage.input_tokens),
            ("output", usage.output_tokens),
            ("thinking", usage.thinking_tokens),
            ("cached", usage.cached_tokens),
        ):
            if count:
                llm_tokens_total.labels(feature=label, model=model, kind=kind).inc(count)
        llm_latency_seconds.labels(feature=label, model=model).observe(latency_s)
        cost = cost_usd(model, usage)
        if cost is None:
            llm_unpriced_calls_total.labels(model=model).inc()
        elif cost:
            llm_cost_usd_total.labels(feature=label, model=model).inc(cost)
    except Exception as exc:
        _warn_once("record_generation", exc)
    if _client is not None:
        try:
            _client.update_current_span(
                metadata=policy.filter_metadata(
                    {
                        "model": model,
                        "status": status,
                        "input_tokens": usage.input_tokens,
                        "output_tokens": usage.output_tokens,
                        "thinking_tokens": usage.thinking_tokens,
                        "cached_tokens": usage.cached_tokens,
                        "cost_usd": cost,
                        "latency_ms": round(latency_s * 1000),
                    }
                )
            )
        except Exception as exc:
            _warn_once("record_generation_trace", exc)
    return cost


def score(*, trace_id: str, name: str, value: float, category: str | None = None) -> None:
    if _client is None:
        return
    try:
        _client.create_score(
            trace_id=trace_id,
            name=name,
            value=value,
            data_type="NUMERIC",
            metadata={"category": category} if category and len(category) <= 64 else None,
        )
    except Exception as exc:
        _warn_once("score", exc)


def current_trace_id() -> str | None:
    if _client is None:
        return None
    try:
        return _client.get_current_trace_id()
    except Exception as exc:
        _warn_once("current_trace_id", exc)
        return None


def flush() -> None:
    if _client is None:
        return
    try:
        _client.flush()
    except Exception as exc:
        _warn_once("flush", exc)
