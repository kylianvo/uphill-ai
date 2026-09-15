"""The default-deny export policy, on plain dicts. Attribute names are the ones
langfuse 4.15.3 and openinference-instrumentation-google-genai 1.4.7 emit."""

import json

from services import observability_policy as policy

CANARY = "CANARY-knee-pain-since-march"


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
        "user.id": "a" * 32,
        "session.id": "b" * 32,
        "langfuse.observation.metadata.retrieval_k": "6",
        "exception.type": "ValueError",
    }


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
