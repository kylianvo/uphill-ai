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
from typing import Any


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
    return None


def score(*, trace_id: str, name: str, value: float, category: str | None = None) -> None:
    return None


def current_trace_id() -> str | None:
    return None


def flush() -> None:
    return None
