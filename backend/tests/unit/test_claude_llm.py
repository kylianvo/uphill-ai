from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from config import settings
from services import claude_llm


def fake_message(text: str, stop_reason: str = "end_turn") -> SimpleNamespace:
    return SimpleNamespace(
        stop_reason=stop_reason,
        content=[SimpleNamespace(type="thinking", thinking=""), SimpleNamespace(type="text", text=text)],
        usage=SimpleNamespace(input_tokens=10, output_tokens=5),
    )


def test_text_joins_text_blocks_and_raises_on_cut_off():
    assert claude_llm.text(fake_message('{"a": 1}')) == '{"a": 1}'
    for reason in ("refusal", "max_tokens"):
        with pytest.raises(RuntimeError):
            claude_llm.text(fake_message("{", reason))


def test_generate_uses_structured_output_when_given_a_schema(monkeypatch):
    from pydantic import BaseModel

    class Out(BaseModel):
        a: int

    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "k")
    client = MagicMock()
    with patch("anthropic.Anthropic", return_value=client):
        claude_llm.generate("hi", schema=Out)
        claude_llm.generate("hi", system="sys")
    parse_kwargs = client.messages.parse.call_args.kwargs
    assert parse_kwargs["output_format"] is Out
    assert parse_kwargs["model"] == settings.CLAUDE_TEXT_MODEL
    assert parse_kwargs["output_config"] == {"effort": settings.CLAUDE_TEXT_EFFORT}
    assert "temperature" not in parse_kwargs  # Haiku 5.5 rejects sampling params
    assert client.messages.create.call_args.kwargs["system"] == "sys"


def test_prompt_label_only_for_claude(monkeypatch):
    monkeypatch.setattr(settings, "COACH_CHAT_PROMPT_LABEL", "production")
    assert claude_llm.prompt_label("gemini") is None
    assert claude_llm.prompt_label("claude") == "claude-production"
