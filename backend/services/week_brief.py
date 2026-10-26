"""The week brief: a short, honest "why this week looks like this" shown in the week header.

The reasons are never left to the model's guesswork: callers pass a decision log (the
facts the volume was actually decided on) and a deterministic diff against last week, and
the model only words them. Best-effort, like the block narrative -- a failure here must
never fail the plan or adapt that triggered it."""

import asyncio
import json
from collections import Counter
from typing import Any

from config import settings
from log_utils import get_logger
from services import claude_llm, observability
from services.calendar_rules import _is_long_run
from services.plan_generator import narrative_lang_instruction

_logger = get_logger(__name__)

WEEK_BRIEF_PROMPT = """You are Coach Uphill, an expert trail-running coach. Explain to the athlete, in plain
language, why Week {{week_number}} of their plan looks the way it does.

Use ONLY the facts below. Do not invent reasons, numbers or sessions.

FACTS BEHIND THIS WEEK:
{{decision_log}}

CHANGE VS LAST WEEK:
{{diff}}

THIS WEEK'S SESSIONS:
{{workout_lines}}

Return ONLY a JSON object with exactly these keys:
- "why": 2-3 sentences naming the real reason(s) for this week's volume and structure, using the numbers above. If volume dropped or was held, say why in plain words and frame it as part of the plan, not a setback.
- "benefits": a list of 2-3 short strings, each "Session name: what it builds", for the most important sessions.
- "watch": one short sentence on what to watch out for this week, or null.

{{lang_instruction}}"""


def _active(workouts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [w for w in workouts if w.get("type") != "Rest"]


def week_diff(prev: list[dict[str, Any]], cur: list[dict[str, Any]]) -> list[str]:
    """Plain-English facts on how this week differs from last week's plan (Rest days ignored)."""
    prev, cur = _active(prev), _active(cur)
    if not prev:
        return ["No earlier week to compare with."]
    prev_min = sum(w.get("duration_minutes") or 0 for w in prev)
    cur_min = sum(w.get("duration_minutes") or 0 for w in cur)
    lines = []
    if prev_min:
        pct = round((cur_min - prev_min) / prev_min * 100)
        lines.append(f"Total time: {prev_min:.0f} -> {cur_min:.0f} min ({pct:+d}%).")
    prev_long = sum(w.get("duration_minutes") or 0 for w in prev if _is_long_run(w))
    cur_long = sum(w.get("duration_minutes") or 0 for w in cur if _is_long_run(w))
    if prev_long or cur_long:
        lines.append(f"Long run: {prev_long:.0f} -> {cur_long:.0f} min.")
    before, after = Counter(w.get("type") for w in prev), Counter(w.get("type") for w in cur)
    for t in sorted(set(before) | set(after), key=str):
        if after[t] != before[t]:
            lines.append(f"{t} sessions: {before[t]} -> {after[t]}.")
    return lines or ["Same structure as last week."]


def _clean(parsed: Any) -> dict[str, Any] | None:
    if not isinstance(parsed, dict) or not str(parsed.get("why") or "").strip():
        return None
    benefits = [str(b).strip() for b in (parsed.get("benefits") or []) if str(b).strip()][:3]
    watch = str(parsed.get("watch") or "").strip() or None
    return {"why": str(parsed["why"]).strip(), "benefits": benefits, "watch": watch}


async def _generate_week_brief(
    *,
    race_info: dict[str, Any],
    block_context: str,
    week_number: int,
    workouts: list[dict[str, Any]],
    prev_workouts: list[dict[str, Any]],
    decision_log: list[str],
    api_key: str | None,
) -> dict[str, Any] | None:
    """{why, benefits[], watch} for this week, or None (no key, bad output, any failure)."""
    if not api_key or not decision_log:
        return None
    try:
        from google import genai as _genai
        from google.genai import types as _genai_types

        workout_lines = "\n".join(
            f"- {w.get('day_of_week', '?')}: {w.get('title') or w.get('type', '?')} "
            f"({w.get('duration_minutes', 0)} min, {w.get('target_zone', '')})"
            for w in _active(workouts)
        )
        tpl = observability.load_prompt(
            "week_brief", WEEK_BRIEF_PROMPT, label=claude_llm.prompt_label(settings.WEEK_BRIEF_LLM_PROVIDER)
        )
        prompt = observability.compile_prompt(
            tpl,
            {
                "week_number": str(week_number),
                "decision_log": "\n".join(f"- {line}" for line in decision_log),
                "diff": "\n".join(f"- {line}" for line in week_diff(prev_workouts, workouts)),
                "workout_lines": workout_lines or "(no sessions)",
                "lang_instruction": narrative_lang_instruction(race_info, block_context),
            },
        )
        provider = settings.WEEK_BRIEF_LLM_PROVIDER
        with observability.generation(
            "generation",
            feature="week_brief",
            model=claude_llm.model_for(provider),
            metadata={"tier": "primary"},
            prompt=tpl,
        ) as generation:
            if claude_llm.is_claude(provider):
                answer = await asyncio.to_thread(claude_llm.call, prompt, generation, thinking=False)
            else:
                response = await asyncio.to_thread(
                    _genai.Client(api_key=api_key).models.generate_content,
                    model=settings.GEMINI_MODEL,
                    contents=prompt,
                    config=_genai_types.GenerateContentConfig(
                        thinking_config=_genai_types.ThinkingConfig(thinking_level=settings.GEMINI_THINKING_LEVEL)
                    )
                    if hasattr(_genai_types, "ThinkingConfig")
                    else None,
                )
                generation.set_usage(observability.Usage.from_genai(response.usage_metadata))
                answer = response.text
        text = answer.strip()
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1:
            return None
        return _clean(json.loads(text[start : end + 1]))
    except Exception as ex:  # noqa: BLE001
        _logger.warning(f"[WeekBrief] model FAILED: {type(ex).__name__}: {ex}")
        return None


async def generate_week_brief(
    *,
    race_info: dict[str, Any],
    block_context: str,
    week_number: int,
    workouts: list[dict[str, Any]],
    prev_workouts: list[dict[str, Any]],
    decision_log: list[str],
    api_key: str | None,
) -> dict[str, Any] | None:
    """{why, benefits[], watch} for this week, or None (no key, bad output, any failure)."""
    api_key = claude_llm.key_for(settings.WEEK_BRIEF_LLM_PROVIDER, api_key)
    if not api_key or not decision_log:
        return None
    with observability.trace("week_brief", feature="week_brief"):
        return await _generate_week_brief(
            race_info=race_info,
            block_context=block_context,
            week_number=week_number,
            workouts=workouts,
            prev_workouts=prev_workouts,
            decision_log=decision_log,
            api_key=api_key,
        )
