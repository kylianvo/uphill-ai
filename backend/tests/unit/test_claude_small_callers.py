"""The small Gemini callers on their Claude flag: server key, Claude call, Gemini untouched."""

import asyncio
import json
from unittest.mock import patch

import pytest

from config import settings
from tests.unit.test_claude_llm import fake_message


@pytest.fixture
def claude(monkeypatch):
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "anthropic-key")

    def on(flag):
        monkeypatch.setattr(settings, flag, "claude")

    with patch("google.genai.Client", side_effect=AssertionError("gemini must not run")):
        yield on


def test_week_brief_on_claude_needs_no_user_gemini_key(claude):
    from services.week_brief import generate_week_brief

    claude("WEEK_BRIEF_LLM_PROVIDER")
    answer = '{"why": "Because.", "benefits": ["Long Run: durability"], "watch": null}'
    with patch("services.claude_llm.generate", return_value=fake_message(answer)) as generate:
        out = asyncio.run(
            generate_week_brief(
                race_info={},
                block_context="",
                week_number=2,
                workouts=[],
                prev_workouts=[],
                decision_log=["Week 1 was 87% complete."],
                api_key=None,
            )
        )
    assert out["why"] == "Because."
    assert "87% complete" in generate.call_args.args[0]
    assert generate.call_args.kwargs["thinking"] is False


def test_coach_nudge_on_claude_is_worded_by_the_model(claude):
    from services import coach_nudge

    claude("COACH_NUDGE_LLM_PROVIDER")
    f = {"week": 2, "done_pct": 100}
    answer = json.dumps({"messages": ["Great week.", "Legs week.", "Keep Friday easy."], "nail": "Sat: Long Run."})
    with (
        patch.object(coach_nudge, "tone_for", return_value="encourage"),
        patch.object(coach_nudge, "grounded", return_value=True),
        patch("services.claude_llm.generate", return_value=fake_message(answer)) as generate,
    ):
        out = asyncio.run(coach_nudge.nudge(f, "en", api_key=None))
    assert out["source"] == "model"
    assert out["messages"] == ["Great week.", "Legs week.", "Keep Friday easy."] and out["nail"] == "Sat: Long Run."
    assert out["text"] == "Great week. Legs week. Keep Friday easy."
    assert "thinking" not in generate.call_args.kwargs  # thinking off lost a grounded nudge (8/8 -> 7/8)


def test_llm_judge_on_claude_uses_structured_scores(claude):
    from services import llm_judge

    claude("LLM_JUDGE_PROVIDER")
    scores = {"grounded": 1.0, "safe": 1.0, "actionable": 0.5, "language": 1.0}
    with patch("services.claude_llm.generate", return_value=fake_message(json.dumps(scores))) as generate:
        out = asyncio.run(llm_judge.judge_reply(question="q", reply="r", evidence=None, lang="en", api_key=""))
    assert out == scores
    assert generate.call_args.kwargs["schema"] is llm_judge.JudgeScores
    assert generate.call_args.kwargs["thinking"] is False


def test_kb_distill_structured_follows_the_provider_it_is_given(claude):
    from pydantic import BaseModel

    from services import kb_distiller

    class Item(BaseModel):
        name: str

    with patch("services.claude_llm.generate", return_value=fake_message('{"name": "X"}')) as generate:
        out = asyncio.run(kb_distiller._gemini_structured("", "prompt", Item, provider="claude"))
    assert out == {"name": "X"}
    assert generate.call_args.kwargs["schema"] is Item


def test_card_translation_on_claude(claude):
    from services.knowledge_extractor import translate_cards_to_vi_with_gemini

    claude("KNOWLEDGE_LLM_PROVIDER")
    card = {
        "chapter_title": "T",
        "summary": "S",
        "key_points": [],
        "tags": ["a"],
        "topic": "Training",
        "source_label": "u",
    }
    vi = {**card, "chapter_title": "Tiêu đề"}
    with patch("services.claude_llm.generate", return_value=fake_message(json.dumps(vi, ensure_ascii=False))):
        [out] = asyncio.run(translate_cards_to_vi_with_gemini(None, [card]))
    assert out["chapter_title"] == "Tiêu đề"


def test_coach_copilot_on_claude_sends_the_conversation(claude):
    import main

    claude("COACH_COPILOT_LLM_PROVIDER")
    request = main.CoachChatRequest(
        messages=[main.ChatMessage(role="user", content="How is she doing?")]  # type: ignore[attr-defined]
    )
    with (
        patch.object(main, "get_user_by_id", return_value={"id": 2}),
        patch.object(main, "_build_athlete_context_block", return_value="ctx"),
        patch("services.claude_llm.generate", return_value=fake_message("On track.")) as generate,
    ):
        out = asyncio.run(main.coach_chat_copilot(2, request, coach={"id": 1}))
    assert out == {"role": "assistant", "content": "On track."}
    assert generate.call_args.args[0] == [{"role": "user", "content": "How is she doing?"}]
    assert "ctx" in generate.call_args.kwargs["system"]
