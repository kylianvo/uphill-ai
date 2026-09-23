"""Unit tests for Langfuse prompt template versioning and local compilation."""

from unittest.mock import MagicMock, patch

from services import observability
from services.coach_prompts import (
    COACH_SYSTEM_INSTRUCTION,
    PromptTemplate,
    compile_coach_prompt,
    get_coach_prompt_template,
)


def test_get_prompt_template_absent_langfuse_keys():
    # When Langfuse client is None (keys absent), returns local fallback
    with patch.object(observability, "_client", None):
        observability.clear_prompt_cache()
        tpl = observability.get_prompt_template(
            name="coach_chat",
            label="production",
            fallback=COACH_SYSTEM_INSTRUCTION,
        )
        assert tpl.source == "local_fallback"
        assert tpl.version == "local"
        assert tpl.template == COACH_SYSTEM_INSTRUCTION


def test_get_prompt_template_success_from_langfuse():
    mock_client = MagicMock()
    mock_lf_prompt = MagicMock()
    mock_lf_prompt.prompt = "Remote coach instruction v2"
    mock_lf_prompt.version = 2
    mock_client.get_prompt.return_value = mock_lf_prompt

    with patch.object(observability, "_client", mock_client):
        observability.clear_prompt_cache()
        tpl = observability.get_prompt_template(
            name="coach_chat",
            label="staging",
            fallback=COACH_SYSTEM_INSTRUCTION,
        )
        assert tpl.source == "langfuse"
        assert tpl.version == "2"
        assert tpl.template == "Remote coach instruction v2"
        mock_client.get_prompt.assert_called_once_with("coach_chat", label="staging", cache_ttl_seconds=300)


def test_get_prompt_template_network_failure_falls_back():
    mock_client = MagicMock()
    mock_client.get_prompt.side_effect = RuntimeError("Network timeout")

    with patch.object(observability, "_client", mock_client):
        observability.clear_prompt_cache()
        tpl = observability.get_prompt_template(
            name="coach_chat",
            label="production",
            fallback=COACH_SYSTEM_INSTRUCTION,
        )
        assert tpl.source == "local_fallback"
        assert tpl.version == "local"
        assert tpl.template == COACH_SYSTEM_INSTRUCTION


def test_get_prompt_template_stale_cache_fallback():
    mock_client = MagicMock()
    mock_lf_prompt = MagicMock()
    mock_lf_prompt.prompt = "Cached remote template"
    mock_lf_prompt.version = 1
    mock_client.get_prompt.return_value = mock_lf_prompt

    with patch.object(observability, "_client", mock_client):
        observability.clear_prompt_cache()
        # 1. Successful fetch into cache
        tpl1 = observability.get_prompt_template("coach_chat", label="prod", fallback="fb", cache_ttl_seconds=1)
        assert tpl1.version == "1"

        # 2. Simulate subsequent failure with expired cache: should return stale cache
        mock_client.get_prompt.side_effect = RuntimeError("Remote outage")
        tpl2 = observability.get_prompt_template("coach_chat", label="prod", fallback="fb", cache_ttl_seconds=0)
        assert tpl2.version == "1"
        assert tpl2.template == "Cached remote template"


def test_compile_coach_prompt_local_compilation():
    tpl = PromptTemplate(
        name="coach_chat",
        version="1",
        template="Base Coach Instruction",
        source="langfuse",
    )
    context = {
        "athlete": {"age": 30, "max_hr": 185, "current_weekly_km": 40.0},
        "workouts": [{"name": "Zone 2 Long Run", "distance_km": 16.0}],
    }
    evidence = [
        {"ref": "ref-1", "title": "Aerobic Base", "content": "Run slow to run fast."},
    ]

    compiled = compile_coach_prompt(
        template=tpl,
        lang="en",
        context=context,
        evidence=evidence,
    )

    # Asserts all context sections are present locally
    assert "Base Coach Instruction" in compiled
    assert "Athlete Profile" in compiled
    assert "Weekly km: 40.0" in compiled
    assert "Zone 2 Long Run" in compiled
    assert "Run slow to run fast" in compiled


def test_compile_coach_prompt_vietnamese_rules():
    tpl = PromptTemplate(name="coach_chat", version="local", template="Base", source="local")
    compiled = compile_coach_prompt(template=tpl, lang="vi")
    assert "VIETNAMESE LOCALIZATION & REGISTER CONTRACT" in compiled
    assert "khối lượng tuần" in compiled


def test_tool_usage_instructs_brief_prose_when_card_renders():
    # The athlete already sees full details in a tool's rendered card, so the
    # compiled prompt must tell the model not to re-list them in text.
    assert "already sees the full details in the card" in COACH_SYSTEM_INSTRUCTION
    assert "do not re-list the workouts, splits, or numbers" in COACH_SYSTEM_INSTRUCTION


def test_tool_usage_instructs_distance_and_elevation_clarify_guidance():
    # The tool can return distance_required (multi-distance race, no
    # distance given -- the app shows the returned options as chips) or
    # elevation_required (no elevation anywhere) -- the prompt must tell
    # the model how to react to each without listing the chip options itself.
    assert "distance_required" in COACH_SYSTEM_INSTRUCTION
    assert "elevation_required" in COACH_SYSTEM_INSTRUCTION


def test_get_coach_prompt_template_defaults():
    with patch.object(observability, "get_prompt_template") as mock_get:
        mock_get.return_value = PromptTemplate("coach_chat", "1", "tpl", "langfuse")
        res = get_coach_prompt_template()
        assert res.name == "coach_chat"
        mock_get.assert_called_once()


def test_prompt_metadata_allowlist():
    from services import observability_policy as policy

    raw_meta = {
        "prompt_name": "coach_chat",
        "prompt_version": "3",
        "prompt_source": "langfuse",
        "prompt_text": "System instruction text",
        "athlete_notes": "Athlete has knee injury",
    }
    filtered = policy.filter_metadata(raw_meta)
    assert filtered.get("prompt_name") == "coach_chat"
    assert filtered.get("prompt_version") == "3"
    assert filtered.get("prompt_source") == "langfuse"
    assert "prompt_text" not in filtered
    assert "athlete_notes" not in filtered


def test_prompt_has_propose_then_apply_rules():
    assert "propose_schedule_change" in COACH_SYSTEM_INSTRUCTION
    assert "Apply" in COACH_SYSTEM_INSTRUCTION
    assert "Never say or imply" in COACH_SYSTEM_INSTRUCTION
