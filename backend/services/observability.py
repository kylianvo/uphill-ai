"""LLM observability (Langfuse traces + Prometheus token/cost) behind one small API.

This is the ONLY module allowed to import langfuse, openinference or opentelemetry --
the services/mcp_client.py containment pattern. Every other module calls the
functions below. See docs/superpowers/specs/llm-observability-design.md.

Without configured keys the API remains a no-op. When enabled, every span passes
through a metadata-only exporter boundary before the configured transport.
"""

import contextlib
import hashlib
import hmac
import os
import re
import secrets
import threading
import time
from collections.abc import Iterator
from contextvars import ContextVar
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
    llm_unknown_usage_calls_total,
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
        "embeddings",
        "evaluation",
    }
)
METRIC_MODELS = frozenset({"gemini-3.8-flash"})
METRIC_STATUSES = frozenset({"ok", "error", "attempt", "success", "used", "fallback"})

_warned: set[str] = set()
_TRACE_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_SCORE_NAMES = frozenset({"thumbs"})
_SCORE_CATEGORIES = frozenset({"helpful", "incorrect", "unsafe", "irrelevant", "other"})


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


def _cost_details_usd(model: str, usage: Usage, on: date | None = None) -> dict[str, float] | None:
    day = on or datetime.now(UTC).date()
    for window in settings.LLM_PRICES_USD_PER_M.get(model, []):
        starts, ends = window.get("from"), window.get("until")
        if starts and day < date.fromisoformat(starts):
            continue
        if ends and day > date.fromisoformat(ends):
            continue
        uncached = max(usage.input_tokens - usage.cached_tokens, 0)
        input_cost = uncached * window["input"] / 1_000_000
        cached_cost = usage.cached_tokens * window["cached_input"] / 1_000_000
        output_cost = (usage.output_tokens + usage.thinking_tokens) * window["output"] / 1_000_000
        return {
            "input": round(input_cost, 6),
            "cached_input": round(cached_cost, 6),
            "output": round(output_cost, 6),
            "total": round(input_cost + cached_cost + output_cost, 6),
        }
    return None


def cost_usd(model: str, usage: Usage, on: date | None = None) -> float | None:
    """USD cost of one call, or None when `model` has no price window covering `on`
    (UTC today by default). prompt_token_count includes cached tokens, so cached
    tokens are subtracted from the input bill and charged at the cached rate."""
    details = _cost_details_usd(model, usage, on=on)
    return details["total"] if details is not None else None


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
_init_failed = False
_MEDIA_UPLOAD_ENV = "LANGFUSE_MEDIA_UPLOAD_ENABLED"
_media_configuration_lock = threading.Lock()
_identifier_proof_key = secrets.token_bytes(32)
_IDENTIFIER_PROOF_ATTRIBUTES = {
    "user.id": "langfuse.trace.metadata._uphill_user_id_proof",
    "session.id": "langfuse.trace.metadata._uphill_session_id_proof",
}
_INVOCATION_ATTRIBUTE = "uphill.internal.invocation_id"
_INVOCATION_PROOF_ATTRIBUTE = "uphill.internal.invocation_id_proof"
_INVOCATION_OWNER_ATTRIBUTE = "uphill.internal.invocation_owner"
_current_invocation_id: ContextVar[str | None] = ContextVar("observability_invocation_id", default=None)


def enabled() -> bool:
    return _client is not None


def pseudonym(value: int | str) -> str:
    return policy.pseudonym(value, settings.OBSERVABILITY_ID_SALT)


def _identifier_proof(attribute: str, identifier: str) -> str:
    return hmac.new(_identifier_proof_key, f"{attribute}:{identifier}".encode(), hashlib.sha256).hexdigest()


def _trusted_identifiers(attributes: dict[str, Any]) -> dict[str, str]:
    trusted = {}
    for attribute, proof_attribute in _IDENTIFIER_PROOF_ATTRIBUTES.items():
        identifier = attributes.get(attribute)
        proof = attributes.get(proof_attribute)
        if (
            isinstance(identifier, str)
            and _TRACE_ID_RE.fullmatch(identifier)
            and isinstance(proof, str)
            and hmac.compare_digest(proof, _identifier_proof(attribute, identifier))
        ):
            trusted[attribute] = identifier
    return trusted


def _trusted_invocation_id(attributes: dict[str, Any]) -> str | None:
    invocation_id = attributes.get(_INVOCATION_ATTRIBUTE)
    proof = attributes.get(_INVOCATION_PROOF_ATTRIBUTE)
    if (
        isinstance(invocation_id, str)
        and _TRACE_ID_RE.fullmatch(invocation_id)
        and isinstance(proof, str)
        and hmac.compare_digest(proof, _identifier_proof(_INVOCATION_ATTRIBUTE, invocation_id))
    ):
        return invocation_id
    return None


@contextlib.contextmanager
def _media_uploads_disabled() -> Iterator[None]:
    """Construct Langfuse with its pinned media manager disabled.

    Langfuse 4.15.3 reads this switch once into both the resource manager and
    media manager. The transform exporter processes media before either masking
    hook, so disabling the manager at construction is the only safe boundary.
    """
    with _media_configuration_lock:
        previous = os.environ.get(_MEDIA_UPLOAD_ENV)
        os.environ[_MEDIA_UPLOAD_ENV] = "false"
        try:
            yield
        finally:
            if previous is None:
                os.environ.pop(_MEDIA_UPLOAD_ENV, None)
            else:
                os.environ[_MEDIA_UPLOAD_ENV] = previous


def _separate_sdk_cleanup_ownership(client: Any, provider: Any) -> None:
    """Keep pinned Langfuse cleanup from recursively shutting down our provider."""
    resources = getattr(client, "_resources", None)
    if resources is not None and getattr(resources, "tracer_provider", None) is provider:
        resources.tracer_provider = None


def _shutdown_with_deadline(*resources: Any) -> None:
    """Attempt every SDK cleanup independently while bounding total caller wait."""
    owned = tuple(resource for resource in resources if resource is not None)
    if not owned:
        return

    unique = []
    seen: set[int] = set()
    for resource in owned:
        if id(resource) not in seen:
            seen.add(id(resource))
            unique.append(resource)

    def shutdown(resource: Any) -> None:
        try:
            resource.shutdown()
        except Exception as exc:
            _warn_once("init_shutdown", exc)

    workers = []
    for index, resource in enumerate(unique):
        worker = threading.Thread(
            target=shutdown,
            args=(resource,),
            name=f"observability-init-cleanup-{index}",
            daemon=True,
        )
        worker.start()
        workers.append(worker)

    deadline = time.monotonic() + max(float(settings.LANGFUSE_TIMEOUT), 0.01)
    for worker in workers:
        remaining = deadline - time.monotonic()
        if remaining > 0:
            try:
                worker.join(timeout=remaining)
            except RuntimeError as exc:
                _warn_once("init_shutdown", exc)
    if any(worker.is_alive() for worker in workers):
        _warn_once("init_shutdown_timeout", TimeoutError())


def _mask(*, data: Any, **kwargs: Any) -> Any:
    try:
        return policy.mask_payload(data, export_content=False)
    except Exception as exc:
        _warn_once("mask", exc)
        return None


def _mask_otel_spans(*, params: Any, **kwargs: Any) -> Any:
    from langfuse.types import MaskOtelSpansResult, OtelSpanPatch

    try:
        patches = {}
        for identifier, span_data in params.spans.items():
            attributes = dict(span_data.attributes or {})
            trusted_identifiers = _trusted_identifiers(attributes)
            preserved = set(trusted_identifiers)
            preserved.update(_IDENTIFIER_PROOF_ATTRIBUTES[key] for key in trusted_identifiers)
            trusted_invocation = _trusted_invocation_id(attributes)
            if trusted_invocation is not None:
                preserved.update({_INVOCATION_ATTRIBUTE, _INVOCATION_PROOF_ATTRIBUTE})
                if attributes.get(_INVOCATION_OWNER_ATTRIBUTE) == trusted_invocation:
                    preserved.add(_INVOCATION_OWNER_ATTRIBUTE)
            deletes, sets = policy.otel_patch(attributes, export_content=False)
            deletes = [key for key in deletes if key not in preserved]
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


def _span_context_without_state(context: Any) -> Any:
    if context is None:
        return None
    from opentelemetry.trace import SpanContext, TraceState

    return SpanContext(
        trace_id=context.trace_id,
        span_id=context.span_id,
        is_remote=context.is_remote,
        trace_flags=context.trace_flags,
        trace_state=TraceState(),
    )


def _sanitized_readable_span(span: Any, resource_attributes: dict[str, str]) -> Any | None:
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import ReadableSpan
    from opentelemetry.sdk.util.instrumentation import InstrumentationScope
    from opentelemetry.trace import Link
    from opentelemetry.trace.status import Status, StatusCode

    scope = span.instrumentation_scope or span.instrumentation_info
    attributes = dict(span.attributes or {})
    trusted_identifiers = _trusted_identifiers(attributes)
    invocation_id = _trusted_invocation_id(attributes)
    invocation_owner = attributes.pop(_INVOCATION_OWNER_ATTRIBUTE, None)
    attributes.pop(_INVOCATION_ATTRIBUTE, None)
    attributes.pop(_INVOCATION_PROOF_ATTRIBUTE, None)
    if invocation_id is not None:
        attributes = policy.normalize_explicit_invocation_attributes(
            attributes,
            canonical=invocation_owner == invocation_id,
        )
    envelope = {
        "name": span.name,
        "attributes": attributes,
        "events": [{"name": event.name, "attributes": dict(event.attributes or {})} for event in (span.events or ())],
        "status": {
            "code": span.status.status_code.name,
            "description": span.status.description,
        },
        "resource": {
            "attributes": dict(resource_attributes),
            "schema_url": getattr(span.resource, "schema_url", None),
        },
        "links": [
            {
                "attributes": dict(link.attributes or {}),
                "trace_state": str(link.context.trace_state),
            }
            for link in (span.links or ())
        ],
        "instrumentation_scope": {
            "name": getattr(scope, "name", None),
            "version": getattr(scope, "version", None),
            "schema_url": getattr(scope, "schema_url", None),
            "attributes": dict(getattr(scope, "attributes", None) or {}),
        },
        "trace_state": str(span.context.trace_state) if span.context else "",
    }
    safe = policy.sanitize_span_envelope(envelope)
    if safe is None:
        return None
    safe["attributes"].update(trusted_identifiers)

    safe_scope = safe["instrumentation_scope"]
    links = tuple(Link(_span_context_without_state(link.context), attributes={}) for link in (span.links or ()))
    status_code = getattr(StatusCode, safe["status"]["code"], StatusCode.UNSET)
    return ReadableSpan(
        name=safe["name"],
        context=_span_context_without_state(span.context),
        parent=_span_context_without_state(span.parent),
        resource=Resource(safe["resource"]["attributes"], schema_url=None),
        attributes=safe["attributes"],
        events=(),
        links=links,
        kind=span.kind,
        instrumentation_info=None,
        status=Status(status_code),
        start_time=span.start_time,
        end_time=span.end_time,
        instrumentation_scope=InstrumentationScope(
            safe_scope["name"],
            version=None,
            schema_url=None,
            attributes={},
        ),
    )


def _final_span_exporter(delegate: Any, *, resource_attributes: dict[str, str]) -> Any:
    """Wrap a transport with the last, metadata-only export boundary."""
    from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

    class FinalSanitizingSpanExporter(SpanExporter):
        def __init__(self) -> None:
            self._shutdown = False
            self._shutdown_lock = threading.Lock()

        def export(self, spans: Any) -> Any:
            sanitized = []
            for span in spans:
                try:
                    safe_span = _sanitized_readable_span(span, resource_attributes)
                except Exception as exc:
                    _warn_once("sanitize_export", exc)
                    continue
                if safe_span is not None:
                    sanitized.append(safe_span)
            if not sanitized:
                return SpanExportResult.SUCCESS
            try:
                return delegate.export(tuple(sanitized))
            except Exception as exc:
                _warn_once("span_export", exc)
                return SpanExportResult.FAILURE

        def force_flush(self, timeout_millis: int = 30000) -> bool:
            try:
                force_flush = getattr(delegate, "force_flush", None)
                return True if force_flush is None else bool(force_flush(timeout_millis=timeout_millis))
            except Exception as exc:
                _warn_once("span_export_flush", exc)
                return False

        def shutdown(self) -> None:
            with self._shutdown_lock:
                if self._shutdown:
                    return
                self._shutdown = True
            try:
                delegate.shutdown()
            except Exception as exc:
                _warn_once("span_export_shutdown", exc)

    return FinalSanitizingSpanExporter()


def _export_resource_attributes() -> dict[str, str]:
    attributes = {"service.name": "uphill-ai-backend"}
    if settings.LANGFUSE_ENVIRONMENT in {"development", "staging", "production", "test"}:
        attributes["deployment.environment.name"] = settings.LANGFUSE_ENVIRONMENT
    return attributes


def _real_otlp_exporter() -> Any:
    import base64
    from importlib.metadata import version

    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

    token = base64.b64encode(f"{settings.LANGFUSE_PUBLIC_KEY}:{settings.LANGFUSE_SECRET_KEY}".encode()).decode("ascii")
    return OTLPSpanExporter(
        endpoint=f"{settings.LANGFUSE_BASE_URL.rstrip('/')}/api/public/otel/v1/traces",
        headers={
            "Authorization": f"Basic {token}",
            "x-langfuse-sdk-name": "python",
            "x-langfuse-sdk-version": version("langfuse"),
            "x-langfuse-public-key": settings.LANGFUSE_PUBLIC_KEY,
        },
        timeout=settings.LANGFUSE_TIMEOUT,
    )


def init(*, span_exporter: Any = None) -> None:
    """Enable Langfuse tracing when configured. Never raises. The SDK imports live here,
    inside try/except, so a stale prod image without them degrades to disabled."""
    global _client, _init_failed
    if _client is not None or not (settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY):
        return
    if _init_failed:
        _shutdown_with_deadline(span_exporter)
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
        from opentelemetry.sdk.trace import SpanProcessor, TracerProvider
        from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
    except ImportError as exc:
        _init_failed = True
        _shutdown_with_deadline(span_exporter)
        _warn_once("import", exc)
        return
    client = None
    provider = None
    final_exporter = None
    google_instrumentor = None
    langchain_instrumentor = None
    google_was_instrumented = False
    langchain_was_instrumented = False
    try:
        # Our own provider, shared by Langfuse and both instrumentors: nothing global is touched.
        provider = TracerProvider(sampler=TraceIdRatioBased(settings.LANGFUSE_SAMPLE_RATE))

        class InvocationContextSpanProcessor(SpanProcessor):
            def on_start(self, span: Any, parent_context: Any = None) -> None:
                invocation_id = _current_invocation_id.get()
                if invocation_id is None:
                    return
                span.set_attribute(_INVOCATION_ATTRIBUTE, invocation_id)
                span.set_attribute(
                    _INVOCATION_PROOF_ATTRIBUTE,
                    _identifier_proof(_INVOCATION_ATTRIBUTE, invocation_id),
                )

        provider.add_span_processor(InvocationContextSpanProcessor())
        transport = span_exporter if span_exporter is not None else _real_otlp_exporter()
        final_exporter = _final_span_exporter(
            transport,
            resource_attributes=_export_resource_attributes(),
        )
        with _media_uploads_disabled():
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
                span_exporter=final_exporter,
            )
        # Metadata-only is the approved production mode. The config flag remains
        # documented for a future product decision, but cannot weaken H1's boundary.
        hide = True
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
        google_instrumentor = GoogleGenAIInstrumentor()
        langchain_instrumentor = LangChainInstrumentor()
        google_was_instrumented = google_instrumentor.is_instrumented_by_opentelemetry
        langchain_was_instrumented = langchain_instrumentor.is_instrumented_by_opentelemetry
        google_instrumentor.instrument(tracer_provider=provider, config=trace_config)
        langchain_instrumentor.instrument(tracer_provider=provider, config=trace_config)
        _client = client
        logger.info("observability enabled", extra={"fields": {"service": "observability", "event": "enabled"}})
    except Exception as exc:
        _init_failed = True
        for instrumentor, was_instrumented in (
            (langchain_instrumentor, langchain_was_instrumented),
            (google_instrumentor, google_was_instrumented),
        ):
            if instrumentor is not None and not was_instrumented and instrumentor.is_instrumented_by_opentelemetry:
                try:
                    instrumentor.uninstrument()
                except Exception as cleanup_exc:
                    _warn_once("init_uninstrument", cleanup_exc)
        _separate_sdk_cleanup_ownership(client, provider)
        _shutdown_with_deadline(client, provider, final_exporter)
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

        user_identifier = pseudonym(user_id) if user_id is not None else None
        session_identifier = pseudonym(thread_id) if thread_id is not None else None
        identifier_proofs = {}
        if user_identifier is not None:
            identifier_proofs["_uphill_user_id_proof"] = _identifier_proof("user.id", user_identifier)
        if session_identifier is not None:
            identifier_proofs["_uphill_session_id_proof"] = _identifier_proof("session.id", session_identifier)

        stack.enter_context(
            propagate_attributes(
                user_id=user_identifier,
                session_id=session_identifier,
                metadata=identifier_proofs or None,
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


def _usage_details(usage: Usage) -> dict[str, int]:
    uncached_input = max(usage.input_tokens - usage.cached_tokens, 0)
    return {
        "input": uncached_input,
        "output": usage.output_tokens,
        "output_reasoning": usage.thinking_tokens,
        "cached_input": usage.cached_tokens,
        "total": uncached_input + usage.cached_tokens + usage.output_tokens + usage.thinking_tokens,
    }


def _valid_usage(usage: Any) -> bool:
    return isinstance(usage, Usage) and all(
        isinstance(value, int) and not isinstance(value, bool) and value >= 0
        for value in (
            usage.input_tokens,
            usage.output_tokens,
            usage.thinking_tokens,
            usage.cached_tokens,
        )
    )


def _record_generation_metrics(
    *,
    feature: str,
    model: str,
    usage: Usage | None,
    usage_known: bool,
    latency_s: float,
    status: str,
) -> tuple[float | None, dict[str, float] | None]:
    label = feature if feature in FEATURES else "other"
    model_label = model if model in METRIC_MODELS else "other"
    status_label = status if isinstance(status, str) and status in METRIC_STATUSES else "other"
    cost_details = None
    if usage_known and usage is not None:
        try:
            cost_details = _cost_details_usd(model, usage)
        except Exception as exc:
            _warn_once("generation_cost", exc)

    try:
        llm_calls_total.labels(feature=label, model=model_label, status=status_label).inc()
        llm_latency_seconds.labels(feature=label, model=model_label).observe(max(latency_s, 0.0))
        if not usage_known or usage is None:
            llm_unknown_usage_calls_total.labels(feature=label, status=status_label).inc()
        else:
            for kind, count in (
                ("input", usage.input_tokens),
                ("output", usage.output_tokens),
                ("thinking", usage.thinking_tokens),
                ("cached", usage.cached_tokens),
            ):
                if count:
                    llm_tokens_total.labels(feature=label, model=model_label, kind=kind).inc(count)
            if cost_details is None:
                llm_unpriced_calls_total.labels(model=model_label).inc()
            elif cost_details["total"]:
                llm_cost_usd_total.labels(feature=label, model=model_label).inc(cost_details["total"])
    except Exception as exc:
        _warn_once("record_generation", exc)
    return (cost_details["total"] if cost_details is not None else None, cost_details)


class GenerationRecorder(Observation):
    """Per-invocation usage accumulator yielded by generation()."""

    def __init__(self, handle: Any, *, feature: str, model: str) -> None:
        super().__init__(handle)
        self._feature = feature
        self._model = model
        self._usage: Usage | None = None
        self._usage_known = False
        self._finished = False

    def set_usage(self, usage: Usage, *, known: bool = True) -> None:
        if not _valid_usage(usage):
            self._usage_known = False
            return
        if self._usage is None:
            self._usage = usage
        else:
            self._usage = Usage(
                input_tokens=max(self._usage.input_tokens, usage.input_tokens),
                output_tokens=max(self._usage.output_tokens, usage.output_tokens),
                thinking_tokens=max(self._usage.thinking_tokens, usage.thinking_tokens),
                cached_tokens=max(self._usage.cached_tokens, usage.cached_tokens),
            )
        self._usage_known = bool(known)

    def _finish(self, *, status: str, latency_s: float) -> None:
        if self._finished:
            return
        self._finished = True
        cost, cost_details = _record_generation_metrics(
            feature=self._feature,
            model=self._model,
            usage=self._usage,
            usage_known=self._usage_known,
            latency_s=latency_s,
            status=status,
        )
        if self._handle is None:
            return
        metadata: dict[str, Any] = {
            "status": status,
            "latency_ms": round(max(latency_s, 0.0) * 1000),
        }
        usage_details = None
        if self._usage_known and self._usage is not None:
            usage_details = _usage_details(self._usage)
            metadata.update(
                {
                    "model": self._model,
                    "input_tokens": self._usage.input_tokens,
                    "output_tokens": self._usage.output_tokens,
                    "thinking_tokens": self._usage.thinking_tokens,
                    "cached_tokens": self._usage.cached_tokens,
                    "cost_usd": cost,
                }
            )
        try:
            self._handle.update(
                model=self._model,
                usage_details=usage_details,
                cost_details=cost_details,
                metadata=policy.filter_metadata(metadata),
                level="ERROR" if status == "error" else None,
            )
        except Exception as exc:
            _warn_once("generation_update", exc)


@contextlib.contextmanager
def generation(
    name: str,
    *,
    feature: str,
    model: str,
    user_id: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> Iterator[GenerationRecorder]:
    """Record one provider invocation with one canonical billing owner."""
    invocation_id = secrets.token_hex(16)
    invocation_token = _current_invocation_id.set(invocation_id)
    started = time.monotonic()
    stack = contextlib.ExitStack()
    handle = None
    if _client is not None:
        try:
            if user_id is not None:
                from langfuse import propagate_attributes

                user_identifier = pseudonym(user_id)
                stack.enter_context(
                    propagate_attributes(
                        user_id=user_identifier,
                        metadata={
                            "_uphill_user_id_proof": _identifier_proof("user.id", user_identifier),
                        },
                    )
                )
            label = feature if feature in FEATURES else "other"
            handle = stack.enter_context(
                _client.start_as_current_observation(
                    as_type="generation",
                    name=name,
                    model=model,
                    metadata=policy.filter_metadata({**(metadata or {}), "feature": label}),
                )
            )
            from opentelemetry.trace import get_current_span

            get_current_span().set_attribute(_INVOCATION_OWNER_ATTRIBUTE, invocation_id)
        except Exception as exc:
            _close(stack)
            stack = contextlib.ExitStack()
            _warn_once("generation_start", exc)

    recorder = GenerationRecorder(handle, feature=feature, model=model)
    status = "ok"
    try:
        yield recorder
    except BaseException as body_exc:
        status = "error"
        recorder.set(status="error", error_type=type(body_exc).__name__)
        raise
    finally:
        recorder._finish(status=status, latency_s=time.monotonic() - started)
        _close(stack)
        _current_invocation_id.reset(invocation_token)


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
    cost, _ = _record_generation_metrics(
        feature=feature,
        model=model,
        usage=usage,
        usage_known=True,
        latency_s=latency_s,
        status=status,
    )
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
    if (
        not isinstance(trace_id, str)
        or not _TRACE_ID_RE.fullmatch(trace_id)
        or not isinstance(name, str)
        or name not in _SCORE_NAMES
        or isinstance(value, bool)
        or not isinstance(value, int | float)
        or value not in (-1, 1)
        or (category is not None and (not isinstance(category, str) or category not in _SCORE_CATEGORIES))
    ):
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
