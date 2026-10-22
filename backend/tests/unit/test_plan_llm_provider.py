"""PLAN_LLM_PROVIDER=claude sends the plan prompt to Claude Haiku; refusals and truncation fall through like an
unparseable Gemini answer (retry, then rules)."""

import asyncio
import json
from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from config import settings
from services import plan_generator
from services.plan_generator import PlanGenerator

START = date(2026, 10, 19)  # a Monday
ROW = {
    "week_number": 1,
    "day_of_week": "Tuesday",
    "phase": "Base",
    "title": "Easy run",
    "type": "Easy",
    "duration_minutes": 60,
    "target_zone": "Zone 2",
    "description": "Easy aerobic run.",
}


class FakeAnthropic:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls: list[dict] = []
        self.messages = self

    def stream(self, **kw):
        self.calls.append(kw)
        reply = self.replies.pop(0)
        stream = MagicMock()
        stream.__enter__.return_value.get_final_message.return_value = reply
        return stream


def _message(text="", stop_reason="end_turn"):
    return SimpleNamespace(
        content=[SimpleNamespace(type="thinking", thinking=""), SimpleNamespace(type="text", text=text)],
        stop_reason=stop_reason,
        usage=SimpleNamespace(input_tokens=1000, output_tokens=200),
    )


@pytest.fixture
def run(monkeypatch):
    monkeypatch.setattr(settings, "PLAN_DEMANDS_ENABLED", True)
    monkeypatch.setattr(settings, "PLAN_LINT_ENABLED", False)
    monkeypatch.setattr(plan_generator, "get_plan_workouts", lambda plan_id: [])
    monkeypatch.setattr("services.kb_retrieval._client", lambda: None)

    def go(fake, api_key="gemini-key"):
        genai = MagicMock()
        genai.models.generate_content.side_effect = RuntimeError("gemini must not be called")
        genai.models.embed_content.return_value = SimpleNamespace(embeddings=[SimpleNamespace(values=[0.1])])
        race_info = {
            "name": "VHT 100K",
            "date": (START + timedelta(weeks=18, days=5)).isoformat(),
            "plan_start_date": START.isoformat(),
            "terrain": "trail",
            "course_distance_km": 104.2,
            "course_elevation_gain_m": 5533,
            "goal_type": "finish",
            "long_run_day": "Saturday",
            "days_per_week": 6,
            "mountain_days": json.dumps(["Saturday"]),
            "training_mountain": "nui_dinh",
            "athlete_tier": "recreational",
        }
        anthropic_ctor = MagicMock(return_value=fake)
        with patch("google.genai.Client", return_value=genai), patch("anthropic.Anthropic", anthropic_ctor):
            workouts, _ = asyncio.run(
                PlanGenerator.generate_plan_workouts(
                    plan_id=0,
                    user_profile={"max_hr": 185, "resting_hr": 55, "current_weekly_km": 65.0},
                    race_info=race_info,
                    total_weeks=20,
                    api_key=api_key,
                    cutoff_time_hours=29,
                    block_number=1,
                    weeks_per_block=1,
                )
            )
        return workouts, genai, anthropic_ctor

    return go


def _claude(monkeypatch, key="anthropic-key"):
    monkeypatch.setattr(settings, "PLAN_LLM_PROVIDER", "claude")
    monkeypatch.setattr(settings, "PLAN_LLM_EFFORT", "low")
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", key)


def test_claude_provider_uses_haiku_with_effort_and_no_sampling(run, monkeypatch):
    _claude(monkeypatch)
    fake = FakeAnthropic([_message(json.dumps([ROW]))])
    workouts, genai, _ = run(fake)
    kw = fake.calls[0]
    assert kw["model"] == "claude-haiku-5-5" and kw["output_config"] == {"effort": "low"}
    assert not {"temperature", "top_p", "top_k", "thinking"} & set(kw)
    assert "MOUNTAIN-DAY ULTRA RULES" in kw["messages"][0]["content"]
    assert len(fake.calls) == 1 and workouts
    genai.models.generate_content.assert_not_called()


def test_refusal_goes_to_claude_retry_then_rules(run, monkeypatch):
    _claude(monkeypatch)
    fake = FakeAnthropic([_message(stop_reason="refusal"), _message(stop_reason="refusal")])
    workouts, _, _ = run(fake)
    assert len(fake.calls) == 2
    assert fake.calls[1]["messages"][0]["content"].startswith("RETRY:")
    assert workouts  # the rule-based schedule


def test_max_tokens_stop_is_unparseable():
    assert plan_generator._claude_text(_message("[{", stop_reason="max_tokens")) is None
    assert plan_generator._claude_text(_message("[]")) == "[]"


def test_claude_without_server_key_falls_to_rules(run, monkeypatch):
    _claude(monkeypatch, key="")
    workouts, genai, anthropic_ctor = run(FakeAnthropic([]))
    anthropic_ctor.assert_not_called()
    genai.models.generate_content.assert_not_called()
    assert workouts


def test_gemini_default_unchanged(run, monkeypatch):
    monkeypatch.setattr(settings, "PLAN_LLM_PROVIDER", "gemini")
    _, genai, anthropic_ctor = run(FakeAnthropic([]))
    assert genai.models.generate_content.call_count == 2  # first attempt + reduced retry, both fail in this test
    anthropic_ctor.assert_not_called()


def test_claude_prompt_draft_keeps_every_variable():
    import re
    from pathlib import Path

    from services.plan_generator import PLAN_GENERATION_PROMPT

    draft = (Path(__file__).resolve().parents[2] / "prompts" / "plan_generation.claude.txt").read_text()
    variables = re.compile(r"{{\s*(\w+)\s*}}")
    assert set(variables.findall(draft)) == set(variables.findall(PLAN_GENERATION_PROMPT))
