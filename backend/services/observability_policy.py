"""Default-deny privacy policy for LLM trace exports.

Pure functions over plain Python values -- no langfuse/opentelemetry imports -- so the
policy is testable on its own and services/observability.py stays the only module that
touches those SDKs. Coach-chat roadmap decision 5: only metadata and scores leave our
infrastructure. See docs/superpowers/specs/llm-observability-design.md.

Attribute names below are the ones emitted by langfuse 4.15.3 (_client/attributes.py)
and openinference-instrumentation-google-genai 1.4.7. Anything not listed is deleted
before export; a new SDK attribute is therefore dropped until someone allowlists it.
"""

import hashlib
import hmac
import json
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
    }
)

_OTEL_KEYS = frozenset(
    {
        # OpenInference / OTel GenAI span identity -- names and counts, no content
        "openinference.span.kind",
        "llm.model_name",
        "llm.provider",
        "llm.system",
        "gen_ai.system",
        "gen_ai.request.model",
        "gen_ai.response.model",
        # Langfuse trace and observation identity
        "langfuse.trace.name",
        "user.id",
        "session.id",
        "langfuse.environment",
        "langfuse.release",
        "langfuse.version",
        "langfuse.observation.type",
        "langfuse.observation.level",
        "langfuse.observation.model.name",
        "langfuse.observation.usage_details",
        "langfuse.observation.cost_details",
        "langfuse.internal.as_root",
        "langfuse.internal.is_app_root",
        # Experiment linkage for golden_eval --push-langfuse (ids and names only)
        "langfuse.experiment.id",
        "langfuse.experiment.name",
        "langfuse.experiment.dataset.id",
        "langfuse.experiment.item.id",
        "langfuse.experiment.item.root_observation_id",
        # Error class name only -- never exception.message or a stack trace
        "exception.type",
    }
)
_OTEL_PREFIXES = ("llm.token_count.", "gen_ai.usage.")
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

_MAX_METADATA_STRING = 64
# Metadata values arrive at export JSON-serialised (a list of chunk refs is one string).
_MAX_ATTRIBUTE_STRING = 512


def pseudonym(value: int | str, salt: str) -> str:
    return hmac.new(salt.encode(), str(value).encode(), hashlib.sha256).hexdigest()[:32]


def _is_short_scalar(value: Any, max_len: int) -> bool:
    if isinstance(value, bool | int | float):
        return True
    return isinstance(value, str) and len(value) <= max_len


def filter_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    kept: dict[str, Any] = {}
    for key, value in (metadata or {}).items():
        if key not in METADATA_KEYS:
            continue
        if isinstance(value, list | tuple):
            if all(_is_short_scalar(item, _MAX_METADATA_STRING) for item in value):
                kept[key] = list(value)
        elif _is_short_scalar(value, _MAX_METADATA_STRING):
            kept[key] = value
    return kept


def _is_content_key(key: str) -> bool:
    return key in _CONTENT_KEYS or key.startswith(_CONTENT_PREFIXES)


def _allowed(key: str, value: Any, export_content: bool) -> bool:
    if key in _OTEL_KEYS or key.startswith(_OTEL_PREFIXES):
        return True
    for prefix in _METADATA_ATTRIBUTE_PREFIXES:
        if key.startswith(prefix):
            return key[len(prefix) :] in METADATA_KEYS and _is_short_scalar(value, _MAX_ATTRIBUTE_STRING)
    return export_content and _is_content_key(key)


def otel_patch(attributes: dict[str, Any], export_content: bool) -> tuple[list[str], dict[str, Any]]:
    """(attribute keys to delete, attribute values to overwrite) for one exported span."""
    deletes = sorted(key for key, value in attributes.items() if not _allowed(key, value, export_content))
    sets: dict[str, Any] = {}
    if export_content:
        for key, value in attributes.items():
            if key not in deletes and _is_content_key(key) and isinstance(value, str):
                redacted = redact_free_text(value)
                if redacted != value:
                    sets[key] = redacted
    return deletes, sets


def _redact(node: Any) -> Any:
    if isinstance(node, dict):
        return {k: "[redacted]" if k in _HEALTH_FREE_TEXT_KEYS else _redact(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_redact(item) for item in node]
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
