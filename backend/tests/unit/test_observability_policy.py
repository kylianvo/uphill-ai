"""The default-deny export policy, on plain dicts. Attribute names are the ones
langfuse 4.15.3 and openinference-instrumentation-google-genai 1.4.7 emit."""

import json
import math

from services import observability_policy as policy

CANARY = "CANARY-knee-pain-since-march"


def test_all_text_surfaces_are_closed():
    secret = "CANARY-HEALTH-injury-left-knee"
    envelope = {
        "name": secret,
        "attributes": {"llm.model_name": secret, "gen_ai.usage.input_tokens": secret},
        "events": [{"name": secret, "attributes": {"exception.message": secret}}],
        "status": {"code": "ERROR", "description": secret},
        "resource": {
            "attributes": {"service.name": secret},
            "schema_url": secret,
        },
        "links": [{"attributes": {"note": secret}, "trace_state": secret}],
        "instrumentation_scope": {
            "name": secret,
            "version": secret,
            "schema_url": secret,
            "attributes": {"public_key": secret},
        },
        "trace_state": secret,
    }

    safe = policy.sanitize_span_envelope(envelope)

    assert secret not in json.dumps(safe)


def test_span_attributes_require_permitted_values_and_numeric_usage():
    identifier = "0123456789abcdef0123456789abcdef"
    safe = policy.sanitize_span_envelope(
        {
            "name": "GenerateContent",
            "attributes": {
                "openinference.span.kind": "LLM",
                "llm.provider": "google",
                "llm.model_name": "gemini-3.8-flash",
                "llm.token_count.prompt": 12,
                "gen_ai.usage.input_tokens": 12,
                "user.id": identifier,
                "session.id": identifier,
                "langfuse.trace.name": "coach_chat.turn",
                "langfuse.environment": "development",
                "langfuse.observation.type": "span",
                "langfuse.internal.is_app_root": True,
                "langfuse.observation.metadata.feature": "coach_chat",
                "langfuse.observation.metadata.retrieval_k": "6",
                "langfuse.observation.usage_details": json.dumps({"input": 12, "output": 3, "total": 15}),
                "langfuse.observation.cost_details": json.dumps({"total": 0.002}),
                "exception.type": "ValueError",
            },
            "status": {"code": "OK"},
        }
    )

    assert safe is not None
    assert safe["name"] == "GenerateContent"
    assert safe["attributes"] == {
        "openinference.span.kind": "LLM",
        "llm.provider": "google",
        "llm.model_name": "gemini-3.8-flash",
        "llm.token_count.prompt": 12,
        "gen_ai.usage.input_tokens": 12,
        "langfuse.trace.name": "coach_chat.turn",
        "langfuse.environment": "development",
        "langfuse.observation.type": "span",
        "langfuse.internal.is_app_root": True,
        "langfuse.observation.metadata.feature": "coach_chat",
        "langfuse.observation.metadata.retrieval_k": "6",
        "langfuse.observation.usage_details": '{"input":12,"output":3,"total":15}',
        "langfuse.observation.cost_details": '{"total":0.002}',
        "exception.type": "ValueError",
    }

    rejected = policy.sanitize_span_envelope(
        {
            "name": "secret operation",
            "attributes": {
                "openinference.span.kind": CANARY,
                "llm.provider": CANARY,
                "llm.model_name": CANARY,
                "llm.token_count.prompt": True,
                "llm.token_count.completion": -1,
                "llm.token_count.total": math.inf,
                "gen_ai.usage.input_tokens": math.nan,
                "user.id": CANARY,
                "session.id": "42",
                "langfuse.trace.name": CANARY,
                "langfuse.environment": CANARY,
                "langfuse.observation.type": CANARY,
                "langfuse.internal.is_app_root": CANARY,
                "langfuse.observation.metadata.feature": CANARY,
                "langfuse.observation.metadata.retrieval_k": CANARY,
                "langfuse.observation.usage_details": json.dumps({"input": 1, "note": CANARY}),
                "langfuse.observation.cost_details": json.dumps({"total": True}),
                "exception.type": CANARY,
            },
        }
    )

    assert rejected is not None
    assert rejected["name"] == "operation"
    assert rejected["attributes"] == {}


def test_metadata_keeps_only_allowlisted_short_values():
    kept = policy.filter_metadata(
        {
            "feature": "coach_chat",
            "retrieval_k": 6,
            "grounded": True,
            "chunk_refs": ["44c51538e091", "1547080b33e1"],
            "notes": CANARY,  # not an allowlisted key
            "lang": "x" * 65,  # allowlisted key, value too long
            "status": {"nested": CANARY},  # allowlisted key, non-scalar value
        }
    )

    assert kept == {
        "feature": "coach_chat",
        "retrieval_k": 6,
        "grounded": True,
        "chunk_refs": ["44c51538e091", "1547080b33e1"],
    }


def test_metadata_requires_known_enums_and_typed_numbers():
    assert (
        policy.filter_metadata(
            {
                "feature": CANARY,
                "model": CANARY,
                "lang": CANARY,
                "status": CANARY,
                "input_tokens": True,
                "output_tokens": -1,
                "cost_usd": math.inf,
                "latency_ms": math.nan,
                "retrieval_k": "6",
                "grounded": "true",
                "error_type": CANARY,
            }
        )
        == {}
    )

    assert policy.filter_metadata(
        {
            "feature": "coach_chat",
            "model": "gemini-3.8-flash",
            "lang": "vi",
            "status": "ok",
            "input_tokens": 10,
            "cost_usd": 0.002,
            "latency_ms": 120,
            "retrieval_k": 6,
            "grounded": True,
            "error_type": "ValueError",
        }
    ) == {
        "feature": "coach_chat",
        "model": "gemini-3.8-flash",
        "lang": "vi",
        "status": "ok",
        "input_tokens": 10,
        "cost_usd": 0.002,
        "latency_ms": 120,
        "retrieval_k": 6,
        "grounded": True,
        "error_type": "ValueError",
    }


def test_otel_patch_deletes_every_content_bearing_attribute():
    attributes = {
        "openinference.span.kind": "LLM",
        "llm.model_name": "gemini-3.8-flash",
        "llm.token_count.prompt": 120,
        "llm.token_count.completion": 8,
        "user.id": "a" * 32,
        "session.id": "b" * 32,
        "langfuse.observation.metadata.retrieval_k": "6",
        "input.value": f"My knee: {CANARY}",
        "output.value": "Rest it.",
        "llm.input_messages.0.message.content": CANARY,
        "llm.invocation_parameters": json.dumps({"system_instruction": CANARY}),
        "exception.message": CANARY,
        "exception.type": "ValueError",
        "langfuse.observation.metadata.notes": CANARY,
        "langfuse.observation.metadata.lang": "e" * 600,
        "langfuse.observation.status_message": CANARY,
    }

    deletes, sets = policy.otel_patch(attributes, export_content=False)

    assert sets == {}
    remaining = {k: v for k, v in attributes.items() if k not in deletes}
    assert remaining == {
        "openinference.span.kind": "LLM",
        "llm.model_name": "gemini-3.8-flash",
        "llm.token_count.prompt": 120,
        "llm.token_count.completion": 8,
        "langfuse.observation.metadata.retrieval_k": "6",
        "exception.type": "ValueError",
    }


def test_otel_patch_does_not_trust_exact_keys():
    attributes = {
        "llm.model_name": CANARY,
        "user.id": CANARY,
        "langfuse.trace.name": CANARY,
        "langfuse.observation.metadata.feature": CANARY,
        "llm.token_count.prompt": True,
        "gen_ai.usage.input_tokens": math.nan,
    }

    deletes, sets = policy.otel_patch(attributes, export_content=False)

    assert deletes == sorted(attributes)
    assert sets == {}


def test_content_export_keeps_io_but_redacts_health_free_text():
    payload = json.dumps({"message": "How is my week?", "profile": {"injury_history": CANARY, "age": 34}})

    deletes, sets = policy.otel_patch({"input.value": payload, "exception.message": CANARY}, export_content=True)

    assert deletes == ["exception.message"]
    assert CANARY not in sets["input.value"]
    assert json.loads(sets["input.value"]) == {
        "message": "How is my week?",
        "profile": {"injury_history": "[redacted]", "age": 34},
    }


def test_mask_payload_drops_io_and_filters_metadata_when_content_export_is_off():
    assert policy.mask_payload(f"prompt with {CANARY}", export_content=False) is None
    assert policy.mask_payload(["list", CANARY], export_content=False) is None
    assert policy.mask_payload({"feature": "gear_finder", "notes": CANARY}, export_content=False) == {
        "feature": "gear_finder"
    }


def test_redact_free_text_leaves_non_json_text_unchanged():
    assert policy.redact_free_text("plain words") == "plain words"


def test_pseudonym_is_stable_salted_and_hides_the_raw_id():
    first = policy.pseudonym(42, "salt-one")

    assert first == policy.pseudonym("42", "salt-one")
    assert first != policy.pseudonym(42, "salt-two")
    assert len(first) == 32 and all(c in "0123456789abcdef" for c in first)


# Regression tests for content-leak findings


def test_otel_prefixes_must_validate_numeric_values_not_trust_prefix_alone():
    """Critical: llm.token_count.* and gen_ai.usage.* must reject string values."""
    attrs = {
        "llm.token_count.debug_echo": f"My knee: {CANARY}",
        "gen_ai.usage.raw_prompt_dump": f"full transcript: {CANARY}",
        "llm.token_count.prompt": 120,  # numeric is OK
    }
    deletes, sets = policy.otel_patch(attrs, export_content=False)

    # String values under these prefixes must be deleted
    assert "llm.token_count.debug_echo" in deletes, "string under llm.token_count.* should be deleted"
    assert "gen_ai.usage.raw_prompt_dump" in deletes, "string under gen_ai.usage.* should be deleted"
    assert "llm.token_count.prompt" not in deletes, "numeric token count should be kept"

    # Verify canary never survives
    remaining = {k: v for k, v in attrs.items() if k not in deletes}
    assert CANARY not in str(remaining), f"CANARY leaked in remaining attributes: {remaining}"


def test_filter_metadata_caps_list_length():
    """Critical: lists with many items can leak large volumes of data."""
    # Chunk refs are legitimate, but 5000 items each 60 chars = 300KB is a volume leak
    huge_list = ["a" * 60] * 5000
    kept = policy.filter_metadata({"chunk_refs": huge_list})

    # Either drop the key or cap the list length to a reasonable bound
    # (chunk_refs, tool_names, collections etc. should never legitimately be this long)
    if "chunk_refs" in kept:
        assert len(kept["chunk_refs"]) < 100, f"list length not capped: {len(kept['chunk_refs'])} items"
    # Verify no volume leak
    assert len(str(kept)) < 10000, f"metadata dict too large: {len(str(kept))} chars"


def test_mask_payload_redacts_json_strings_in_lists():
    """Critical: health fields in JSON-encoded list elements must be redacted."""
    # Multi-part message content: list of dicts/strings, some JSON-encoded
    data = [
        json.dumps({"injury_history": CANARY, "age": 34}),
        "plain text segment",
        json.dumps({"athlete_notes": CANARY, "duration": 45}),
    ]

    result = policy.mask_payload(data, export_content=True)

    # Result should be redacted, not leaked
    result_str = json.dumps(result) if isinstance(result, list) else str(result)
    assert CANARY not in result_str, f"CANARY leaked in list redaction: {result_str}"

    # Verify structure is preserved (list of strings)
    assert isinstance(result, list), "should remain a list"

    # Verify health fields are actually redacted
    for item in result:
        if isinstance(item, str):
            try:
                parsed = json.loads(item)
                if isinstance(parsed, dict):
                    assert "injury_history" not in parsed or parsed["injury_history"] == "[redacted]"
                    assert "athlete_notes" not in parsed or parsed["athlete_notes"] == "[redacted]"
            except (json.JSONDecodeError, ValueError):
                # Non-JSON strings pass through unchanged
                pass
