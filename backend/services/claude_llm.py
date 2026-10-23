"""One-shot Claude text generation for the features that moved off Gemini behind a `<FEATURE>_LLM_PROVIDER` flag.

Plan generation keeps its own streamed call (`plan_generator._claude_generate`); coach chat has its own model class.
"""

from typing import Any

from pydantic import BaseModel

from config import settings
from services import observability


def is_claude(provider: str) -> bool:
    return provider == "claude"


def key_for(provider: str, gemini_key: str | None) -> str | None:
    """Claude always bills the server key; per-user Gemini keys only ever pay for Gemini."""
    return settings.ANTHROPIC_API_KEY if is_claude(provider) else gemini_key


def model_for(provider: str) -> str:
    return settings.CLAUDE_TEXT_MODEL if is_claude(provider) else settings.GEMINI_MODEL


def prompt_label(provider: str) -> str | None:
    """Claude prompts live under their own Langfuse labels; with none there, load_prompt serves the in-code text."""
    return f"claude-{settings.COACH_CHAT_PROMPT_LABEL}" if is_claude(provider) else None


def generate(
    prompt: str | list[dict[str, str]],
    *,
    schema: type[BaseModel] | None = None,
    system: str | None = None,
    model: str | None = None,
    max_tokens: int = 16000,
) -> Any:
    """One blocking Messages call on the server key. Haiku 5.5 rejects temperature and prefill, so JSON shape comes
    from structured outputs (`schema`) and effort is the only knob."""
    import anthropic

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    kwargs: dict[str, Any] = {
        "model": model or settings.CLAUDE_TEXT_MODEL,
        "max_tokens": max_tokens,
        "output_config": {"effort": settings.CLAUDE_TEXT_EFFORT},
        # A list is a whole conversation of {role, content} turns.
        "messages": prompt if isinstance(prompt, list) else [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system
    if schema is not None:
        return client.messages.parse(output_format=schema, **kwargs)
    return client.messages.create(**kwargs)


def text(message: Any) -> str:
    """The answer text. A refusal or a reply cut off at max_tokens raises, like any failed model call."""
    if message.stop_reason in ("refusal", "max_tokens"):
        raise RuntimeError(f"claude stop_reason={message.stop_reason}")
    return "".join(block.text for block in message.content if block.type == "text")


def call(prompt: str, generation: Any, **kwargs: Any) -> str:
    """generate + usage on the open generation span + text."""
    message = generate(prompt, **kwargs)
    generation.set_usage(observability.Usage.from_anthropic(message.usage))
    return text(message)
