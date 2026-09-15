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
    """Handle yielded by trace()/span(). set() attaches allowlisted metadata."""

    def set(self, **metadata: Any) -> None:
        return None


_NOOP = Observation()


def init() -> None:
    return None


def enabled() -> bool:
    return False


@contextlib.contextmanager
def trace(
    name: str,
    *,
    feature: str,
    user_id: int | None = None,
    thread_id: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> Iterator[Observation]:
    yield _NOOP


@contextlib.contextmanager
def span(name: str, *, metadata: dict[str, Any] | None = None) -> Iterator[Observation]:
    yield _NOOP


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
    return cost


def score(*, trace_id: str, name: str, value: float, category: str | None = None) -> None:
    return None


def current_trace_id() -> str | None:
    return None


def flush() -> None:
    return None
