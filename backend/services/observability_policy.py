"""Default-deny privacy policy for LLM trace exports.

Pure functions over plain Python values -- no langfuse/opentelemetry imports -- so the
policy is testable on its own and services/observability.py stays the only module that
touches those SDKs. Coach-chat roadmap decision 5: only metadata and scores leave our
infrastructure. See docs/superpowers/specs/llm-observability-design.md.

Attribute names below are the ones emitted by langfuse 4.15.3 (_client/attributes.py)
and openinference-instrumentation-google-genai 1.4.7. Anything not explicitly allowlisted
is deleted before export. Token count attributes must carry numeric values only (no free-text);
health-sensitive fields in content are redacted; list lengths are capped to prevent volume leaks.
"""

import hashlib
import hmac
import json
import math
import re
from typing import Any

METADATA_KEYS = frozenset(
    {
        "feature",
        "engine",
        "tier",
        "status",
        "error_type",
        "lang",
        "model",
        "input_tokens",
        "output_tokens",
        "thinking_tokens",
        "cached_tokens",
        "cost_usd",
        "latency_ms",
        "retrieval_k",
        "collections",
        "chunk_refs",
        "chunk_scores",
        "grounded",
        "tool_names",
        "tool_arg_keys",
        "turn_index",
        "cap_hit",
        "catalog_entries",
        "cache_hit",
        "workout_count",
        "prompt_name",
        "prompt_version",
        "prompt_source",
    }
)

_METADATA_ATTRIBUTE_PREFIXES = ("langfuse.observation.metadata.", "langfuse.trace.metadata.")
_CONTENT_KEYS = frozenset(
    {
        "input.value",
        "output.value",
        "langfuse.observation.input",
        "langfuse.observation.output",
        "langfuse.trace.input",
        "langfuse.trace.output",
    }
)
_CONTENT_PREFIXES = ("llm.input_messages.", "llm.output_messages.")
_HEALTH_FREE_TEXT_KEYS = frozenset({"injury_history", "athlete_notes", "notes", "feeling"})

_MAX_LIST_ITEMS = 100  # cap list length to prevent volume leaks

_SPAN_NAMES = frozenset(
    {
        "GenerateContent",
        "GenerateContentStream",
        "LangGraph",
        "RunnableLambda",
        "_tools_condition",
        "block_narrative",
        "chat_summary",
        "coach_chat.turn",
        "final_generate",
        "gear_finder",
        "gemini",
        "gemini_retry",
        "generate",
        "generation",
        "get_week",
        "kb_distill",
        "kb_retrieval",
        "kb_search",
        "knowledge_cards",
        "nutrition_lab",
        "pace_strategy",
        "persist",
        "plan_generation",
        "propose_rebuild_week",
        "propose_schedule_change",
        "retrieval",
        "retrieve",
        "rule_based",
        "tools",
        "week_review",
        "workout_ai_create",
    }
)
_FEATURES = frozenset(
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
_STATUS_CODES = frozenset({"UNSET", "OK", "ERROR"})
_SCOPE_NAMES = frozenset(
    {
        "langfuse-sdk",
        "openinference.instrumentation.google_genai",
        "openinference.instrumentation.langchain",
    }
)
_RESOURCE_VALUES = {
    "service.name": frozenset({"uphill-ai-backend"}),
    "deployment.environment.name": frozenset({"development", "staging", "production", "test"}),
}
_SPAN_KINDS = frozenset({"LLM", "CHAIN", "AGENT", "TOOL", "RETRIEVER", "EMBEDDING", "RERANKER"})
_PROVIDERS = frozenset({"google"})
_SYSTEMS = frozenset({"google", "gemini"})
_MODELS = frozenset({"gemini-3.8-flash"})
_ENVIRONMENTS = frozenset({"development", "staging", "production", "test"})
_OBSERVATION_TYPES = frozenset({"span", "generation", "agent", "tool", "chain", "retriever", "evaluator"})
_OBSERVATION_LEVELS = frozenset({"DEFAULT", "DEBUG", "WARNING", "ERROR"})
_TOKEN_ATTRIBUTE_KEYS = frozenset(
    {
        "llm.token_count.prompt",
        "llm.token_count.completion",
        "llm.token_count.total",
        "gen_ai.usage.input_tokens",
        "gen_ai.usage.output_tokens",
    }
)
_USAGE_DETAIL_KEYS = frozenset(
    {
        "input",
        "output",
        "total",
        "cached_input",
        "cache_read_input_tokens",
        "input_tokens",
        "output_tokens",
        "prompt_tokens",
        "completion_tokens",
        "output_reasoning",
    }
)
_COST_DETAIL_KEYS = frozenset({"input", "output", "total", "cached_input", "input_cost", "output_cost", "total_cost"})
_ERROR_TYPES = frozenset(
    {
        "APIError",
        "CancelledError",
        "ClientError",
        "ConnectionError",
        "JSONDecodeError",
        "KeyError",
        "RuntimeError",
        "ServerError",
        "TimeoutError",
        "TypeError",
        "ValidationError",
        "ValueError",
    }
)
_ENGINES = frozenset({"gemini", "gemini_retry", "rule_based", "mock"})
_TIERS = frozenset({"primary", "retry", "fallback"})
_GENERATION_STATUSES = frozenset({"ok", "error", "attempt", "success", "used", "fallback"})
_LANGUAGES = frozenset({"en", "vi"})
_COLLECTIONS = frozenset({"uphill_kb_scheduler", "uphill_kb_nutrition_principles"})
_CHUNK_REF_RE = re.compile(r"^[0-9a-f]{12}$")
_PROMPT_NAMES = frozenset({"coach_chat", "chat_summary"})
_PROMPT_SOURCES = frozenset({"langfuse", "local_fallback"})
_PROMPT_VERSION_RE = re.compile(r"^[A-Za-z0-9_.-]{1,32}$")
_TOOL_NAMES = frozenset({"get_week", "pace_strategy", "week_review", "kb_search"})
_TOOL_ARG_KEY_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_BILLABLE_MODEL_KEYS = frozenset(
    {
        "llm.model_name",
        "gen_ai.request.model",
        "gen_ai.response.model",
        "langfuse.observation.model.name",
    }
)
_BILLABLE_USAGE_COST_KEYS = frozenset(
    {
        "langfuse.observation.usage_details",
        "langfuse.observation.cost_details",
    }
)
_BILLABLE_USAGE_PREFIXES = ("llm.token_count.", "gen_ai.usage.")


def pseudonym(value: int | str, salt: str) -> str:
    return hmac.new(salt.encode(), str(value).encode(), hashlib.sha256).hexdigest()[:32]


def _nonnegative_number(value: Any, *, integer: bool = False) -> bool:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return False
    if integer and not isinstance(value, int):
        return False
    return math.isfinite(value) and value >= 0


def _in_enum(value: Any, allowed: frozenset[str]) -> bool:
    return isinstance(value, str) and value in allowed


def _numeric_json(value: Any, allowed_keys: frozenset[str], *, integer: bool) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return None
    if not isinstance(parsed, dict) or not parsed or not set(parsed).issubset(allowed_keys):
        return None
    if not all(_nonnegative_number(item, integer=integer) for item in parsed.values()):
        return None
    return json.dumps(parsed, separators=(",", ":"), sort_keys=True)


def _sanitize_metadata_value(key: str, value: Any) -> Any | None:
    if key == "feature":
        return value if _in_enum(value, _FEATURES) else None
    if key == "engine":
        return value if _in_enum(value, _ENGINES) else None
    if key == "tier":
        return value if _in_enum(value, _TIERS) else None
    if key == "status":
        return value if _in_enum(value, _GENERATION_STATUSES) else None
    if key == "error_type":
        return value if _in_enum(value, _ERROR_TYPES) else None
    if key == "lang":
        return value if _in_enum(value, _LANGUAGES) else None
    if key == "model":
        return value if _in_enum(value, _MODELS) else None
    if key in {"input_tokens", "output_tokens", "thinking_tokens", "cached_tokens"}:
        return value if _nonnegative_number(value, integer=True) else None
    if key in {"cost_usd", "latency_ms"}:
        return value if _nonnegative_number(value) else None
    if key == "retrieval_k":
        return value if isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 100 else None
    if key == "collections":
        if isinstance(value, list | tuple) and len(value) <= _MAX_LIST_ITEMS and all(v in _COLLECTIONS for v in value):
            return list(value)
        return None
    if key == "chunk_refs":
        if (
            isinstance(value, list | tuple)
            and len(value) <= _MAX_LIST_ITEMS
            and all(isinstance(v, str) and _CHUNK_REF_RE.fullmatch(v) for v in value)
        ):
            return list(value)
        return None
    if key == "chunk_scores":
        if (
            isinstance(value, list | tuple)
            and len(value) <= _MAX_LIST_ITEMS
            and all(_nonnegative_number(v) and v <= 1 for v in value)
        ):
            return list(value)
        return None
    if key in {"grounded", "cap_hit", "cache_hit"}:
        return value if isinstance(value, bool) else None
    if key in {"turn_index", "catalog_entries", "workout_count"}:
        return value if _nonnegative_number(value, integer=True) else None
    if key == "prompt_name":
        return value if _in_enum(value, _PROMPT_NAMES) else None
    if key == "prompt_source":
        return value if _in_enum(value, _PROMPT_SOURCES) else None
    if key == "prompt_version":
        return value if isinstance(value, str) and _PROMPT_VERSION_RE.fullmatch(value) else None
    if key == "tool_names":
        if isinstance(value, list | tuple) and len(value) <= _MAX_LIST_ITEMS and all(v in _TOOL_NAMES for v in value):
            return list(value)
        return None
    if key == "tool_arg_keys":
        if (
            isinstance(value, list | tuple)
            and len(value) <= _MAX_LIST_ITEMS
            and all(isinstance(v, str) and _TOOL_ARG_KEY_RE.fullmatch(v) for v in value)
        ):
            return list(value)
        return None
    return None


def _metadata_attribute(key: str, value: Any) -> Any | None:
    suffix = next(
        (key[len(prefix) :] for prefix in _METADATA_ATTRIBUTE_PREFIXES if key.startswith(prefix)),
        None,
    )
    if suffix is None:
        return None
    parsed = value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError):
            parsed = value
    return value if _sanitize_metadata_value(suffix, parsed) is not None else None


def _sanitize_attribute(key: str, value: Any) -> Any | None:
    if key == "openinference.span.kind" and value in _SPAN_KINDS:
        return value
    if key == "llm.provider" and value in _PROVIDERS:
        return value
    if key in {"llm.system", "gen_ai.system"} and value in _SYSTEMS:
        return value
    if key in {"llm.model_name", "gen_ai.request.model", "gen_ai.response.model", "langfuse.observation.model.name"}:
        return value if value in _MODELS else None
    if key in _TOKEN_ATTRIBUTE_KEYS:
        return value if _nonnegative_number(value) else None
    if key == "langfuse.trace.name":
        return value if value in _SPAN_NAMES else None
    if key == "langfuse.environment":
        return value if value in _ENVIRONMENTS else None
    if key == "langfuse.observation.type":
        return value if value in _OBSERVATION_TYPES else None
    if key == "langfuse.observation.level":
        return value if value in _OBSERVATION_LEVELS else None
    if key in {"langfuse.internal.as_root", "langfuse.internal.is_app_root"}:
        return value if isinstance(value, bool) else None
    if key == "langfuse.observation.usage_details":
        return _numeric_json(value, _USAGE_DETAIL_KEYS, integer=True)
    if key == "langfuse.observation.cost_details":
        return _numeric_json(value, _COST_DETAIL_KEYS, integer=False)
    if key == "exception.type":
        return value if _in_enum(value, _ERROR_TYPES) else None
    if key.startswith(_METADATA_ATTRIBUTE_PREFIXES):
        return _metadata_attribute(key, value)
    return None


def normalize_explicit_invocation_attributes(attributes: dict[str, Any], *, canonical: bool) -> dict[str, Any]:
    """Remove native billable attribution from descendants of an explicit generation."""
    if canonical:
        return attributes
    return {
        key: value
        for key, value in attributes.items()
        if key not in _BILLABLE_MODEL_KEYS
        and key not in _BILLABLE_USAGE_COST_KEYS
        and not key.startswith(_BILLABLE_USAGE_PREFIXES)
    }


def sanitize_span_envelope(envelope: dict[str, Any]) -> dict[str, Any] | None:
    """Return a metadata-only span envelope covering every serialized text surface."""
    try:
        resource = envelope.get("resource") or {}
        resource_attributes = resource.get("attributes") or {}
        safe_resource = {
            key: value
            for key, value in resource_attributes.items()
            if key in _RESOURCE_VALUES and value in _RESOURCE_VALUES[key]
        }
        scope = envelope.get("instrumentation_scope") or {}
        scope_name = scope.get("name")
        status = envelope.get("status") or {}
        status_code = status.get("code")
        safe_attributes = {}
        for key, value in (envelope.get("attributes") or {}).items():
            safe_value = _sanitize_attribute(key, value)
            if safe_value is not None:
                safe_attributes[key] = safe_value
        return {
            "name": envelope.get("name") if envelope.get("name") in _SPAN_NAMES else "operation",
            "attributes": safe_attributes,
            "events": [],
            "status": {"code": status_code if status_code in _STATUS_CODES else "UNSET"},
            "resource": {"attributes": safe_resource, "schema_url": None},
            "links": [{"attributes": {}, "trace_state": ""} for _ in (envelope.get("links") or [])],
            "instrumentation_scope": {
                "name": scope_name if scope_name in _SCOPE_NAMES else "uphill-ai.observability",
                "version": None,
                "schema_url": None,
                "attributes": {},
            },
            "trace_state": "",
        }
    except Exception:
        return None


def filter_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    kept: dict[str, Any] = {}
    for key, value in (metadata or {}).items():
        if key not in METADATA_KEYS:
            continue
        sanitized = _sanitize_metadata_value(key, value)
        if sanitized is not None:
            kept[key] = sanitized
    return kept


def _is_content_key(key: str) -> bool:
    return key in _CONTENT_KEYS or key.startswith(_CONTENT_PREFIXES)


def _allowed(key: str, value: Any, export_content: bool) -> bool:
    return _sanitize_attribute(key, value) is not None or (export_content and _is_content_key(key))


def otel_patch(attributes: dict[str, Any], export_content: bool) -> tuple[list[str], dict[str, Any]]:
    """(attribute keys to delete, attribute values to overwrite) for one exported span."""
    deletes = sorted(key for key, value in attributes.items() if not _allowed(key, value, export_content))
    sets: dict[str, Any] = {}
    for key, value in attributes.items():
        if key in deletes:
            continue
        if export_content and _is_content_key(key) and isinstance(value, str):
            redacted = redact_free_text(value)
            if redacted != value:
                sets[key] = redacted
        elif not _is_content_key(key):
            sanitized = _sanitize_attribute(key, value)
            if sanitized != value:
                sets[key] = sanitized
    return deletes, sets


def _redact(node: Any) -> Any:
    if isinstance(node, dict):
        return {k: "[redacted]" if k in _HEALTH_FREE_TEXT_KEYS else _redact(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_redact(item) for item in node]
    if isinstance(node, str):
        # Try to parse and redact JSON strings (e.g., in list elements)
        try:
            parsed = json.loads(node)
            redacted = _redact(parsed)
            return json.dumps(redacted, ensure_ascii=False)
        except (TypeError, ValueError):
            # Not JSON, return unchanged
            return node
    return node


def redact_free_text(value: str) -> str:
    """Replace health free-text fields inside a JSON payload with "[redacted]".
    Text that isn't JSON is returned unchanged."""
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return value
    return json.dumps(_redact(parsed), ensure_ascii=False)


def mask_payload(data: Any, export_content: bool) -> Any:
    """Body of the Langfuse `mask` hook, which receives each SDK observation's input,
    output and metadata in turn. With content export off, dicts are reduced to
    allowlisted metadata and everything else is dropped."""
    if not export_content:
        return filter_metadata(data) if isinstance(data, dict) else None
    if isinstance(data, str):
        return redact_free_text(data)
    return _redact(data)
