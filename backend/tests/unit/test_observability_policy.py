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
