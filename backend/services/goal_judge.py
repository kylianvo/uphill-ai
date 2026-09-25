"""LLM goal judge (docs/superpowers/specs/2026-09-26-llm-goal-estimation-design.md).

Gemini weighs the numeric anchors from services/goal_anchors.py against the
athlete's qualitative context and picks A/B/C goals with reasoning. Code then
validates the answer; one reduced-prompt retry, then a deterministic A/B/C
from the anchors -- the same Gemini -> retry -> rules tiers as the Scheduler.
"""

import json
import statistics
from typing import Any, Literal

from pydantic import BaseModel, ValidationError

from config import settings
from log_utils import get_logger
from services import observability
from services.race_estimator import AMBITIOUS_FACTOR, IMPROVEMENT_CAP, IMPROVEMENT_PER_WEEK, SAFE_FACTOR, RaceEstimator

_logger = get_logger(__name__)

ANCHOR_SLACK = 0.15
MAX_SPREAD = {"low": 1.35, "medium": 1.20, "high": 1.20}
WINNER_FLOOR = 0.97
REDUCED_HISTORY = 5


class Goals(BaseModel):
    a: float
    b: float
    c: float


class AnchorWeight(BaseModel):
    id: str
    weight: float


class GoalOutput(BaseModel):
    goals: Goals
    confidence: Literal["high", "medium", "low"]
    reasoning: list[str]
    anchors_weighted: list[AnchorWeight]
    missing: list[str]


_INSTRUCTIONS = {
    "en": "Write every reasoning bullet in English.",
    "vi": (
        "Write every reasoning bullet in Vietnamese, in a natural coaching voice. Keep running terms "
        "athletes use in English (trail, ultra, pace, vert, block, race, UTMB index, VO2max)."
    ),
}


def build_prompt(
    context: dict[str, Any],
    anchors: list[dict[str, Any]],
    lang: str,
    reduced: bool = False,
    previous_error: str | None = None,
) -> str:
    payload = dict(context)
    if reduced:
        payload["history"] = (payload.get("history") or [])[:REDUCED_HISTORY]
        race = dict(payload.get("race") or {})
        race.pop("climate", None)
        race.pop("key_climbs", None)
        payload["race"] = race
    retry_note = f"\nYour previous answer was rejected: {previous_error}. Fix exactly that.\n" if previous_error else ""
    return f"""You are Coach Uphill, a trail and mountain running coach following Scott Johnston's
Training for the Uphill Athlete. Set race-day goals for this athlete on the target race.

ANCHORS are finish-time estimates (minutes) already computed from the athlete's past results
and the race's field data. Weigh them; do NOT invent new arithmetic or numbers not supported
by the anchors or the field curve. Anchors describe current fitness: `weeks_to_race` of
structured training may improve that by up to about 5%. Recent, similar trail results
outweigh old or road results. Training-block execution (`block`) moves the goal less than
race evidence does. With no anchors, stay inside the race's field curve and set confidence low.

Goals, in minutes: a = ambitious (a great day), b = realistic, c = safe (banks margin for
problems). Keep a < b < c. confidence: high only with several recent similar trail results;
low when the estimate rests on priors. reasoning: 3 to 5 short bullets, each citing a specific
input (a result, an anchor, a metric). anchors_weighted: the anchor ids you relied on with
weights summing to about 1. missing: short keys for data that would sharpen this (for example
"recent_trail_result", "watch", "utmb_index").
{_INSTRUCTIONS.get(lang, _INSTRUCTIONS["en"])}
{retry_note}
CONTEXT:
{json.dumps(payload, ensure_ascii=False, default=str)}

ANCHORS:
{json.dumps(anchors, ensure_ascii=False, default=str)}
"""


def _call_gemini(prompt: str, api_key: str) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    with observability.generation("generation", feature="goal_estimate", model=settings.GEMINI_MODEL) as generation:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=GoalOutput,
                temperature=0.0,
                thinking_config=types.ThinkingConfig(thinking_level=settings.GEMINI_THINKING_LEVEL),
            ),
        )
        generation.set_usage(observability.Usage.from_genai(response.usage_metadata))
    return response.text


def validate(
    output: GoalOutput, anchors: list[dict[str, Any]], race: dict[str, Any], cutoff_mins: float | None = None
) -> list[str]:
    """Guardrails on the model's answer; returns the rule violations (empty = accepted)."""
    errors: list[str] = []
    a, b, c = output.goals.a, output.goals.b, output.goals.c
    if not a < b < c:
        errors.append("goals must satisfy a < b < c")
    elif c / a > MAX_SPREAD[output.confidence]:
        errors.append(f"c / a must be <= {MAX_SPREAD[output.confidence]} at {output.confidence} confidence")

    field = race.get("field") or {}
    fastest = field.get("fastest_winner_mins")
    if fastest and a < WINNER_FLOOR * fastest:
        errors.append(f"a is faster than the race's winning time ({fastest:.0f} min)")
    if cutoff_mins and c > cutoff_mins:
        errors.append(f"c exceeds the cutoff ({cutoff_mins:.0f} min)")

    if anchors:
        low = min(x["minutes"] for x in anchors) * (1 - ANCHOR_SLACK)
        high = max(x["minutes"] for x in anchors) * (1 + ANCHOR_SLACK)
        if not low <= b <= high:
            errors.append(f"b must be between {low:.0f} and {high:.0f} min (the anchors' range)")
    elif field.get("curve"):
        low = RaceEstimator.interpolate_percentile(field["curve"], percentile=10.0)
        high = RaceEstimator.interpolate_percentile(field["curve"], percentile=95.0)
        if not low <= b <= high:
            errors.append(f"b must be between {low:.0f} and {high:.0f} min (the field's p10-p95)")
    elif output.confidence != "low":
        errors.append("confidence must be low without anchors or field data")

    if not 3 <= len(output.reasoning) <= 5:
        errors.append("give 3 to 5 reasoning bullets")
    known = {x["id"] for x in anchors}
    unknown = [w.id for w in output.anchors_weighted if w.id not in known]
    if unknown:
        errors.append(f"unknown anchor ids: {', '.join(unknown)}")
    return errors


def improvement_for(weeks_to_race: float | None) -> float:
    return min(IMPROVEMENT_CAP, max(0.0, weeks_to_race or 0.0) * IMPROVEMENT_PER_WEEK)


def deterministic(anchors: list[dict[str, Any]], weeks_to_race: float | None) -> dict[str, Any] | None:
    """Rules tier: the anchors' median with the old time-to-race improvement."""
    if not anchors:
        return None
    realistic = statistics.median(x["minutes"] for x in anchors) * (1 - improvement_for(weeks_to_race))
    result_anchors = [x for x in anchors if x.get("source_result_id") is not None]
    confidence = "high" if len(result_anchors) >= 3 else "medium" if result_anchors else "low"
    return {
        "goals": {
            "a": round(realistic * AMBITIOUS_FACTOR, 1),
            "b": round(realistic, 1),
            "c": round(realistic * SAFE_FACTOR, 1),
        },
        "confidence": confidence,
        "reasoning": [],
        "anchors_weighted": [],
        "missing": [],
        "engine": "rules",
    }


def assess(
    context: dict[str, Any],
    anchors: list[dict[str, Any]],
    *,
    api_key: str | None,
    lang: str = "en",
    cutoff_mins: float | None = None,
    llm_enabled: bool = True,
) -> dict[str, Any] | None:
    """A/B/C goals with reasoning. Returns None only when neither the model nor
    the rules tier can produce a number (no anchors and the model failed)."""
    race = context.get("race") or {}
    if llm_enabled and api_key:
        error: str | None = None
        with observability.trace("goal_estimate", feature="goal_estimate", metadata={"lang": lang}):
            for engine, reduced in (("gemini", False), ("gemini_retry", True)):
                try:
                    with observability.span(engine, metadata={"engine": engine}):
                        raw = _call_gemini(build_prompt(context, anchors, lang, reduced, error), api_key)
                    output = GoalOutput.model_validate_json(raw)
                    errors = validate(output, anchors, race, cutoff_mins)
                except ValidationError as exc:
                    errors = [f"response did not match the schema ({exc.error_count()} errors)"]
                except Exception as exc:  # network, quota, bad JSON
                    _logger.warning("goal judge call failed", extra={"fields": {"engine": engine, "error": str(exc)}})
                    errors = [f"call failed: {type(exc).__name__}"]
                if not errors:
                    result = output.model_dump()
                    result["goals"] = {k: round(v, 1) for k, v in result["goals"].items()}
                    result["engine"] = engine
                    return result
                error = "; ".join(errors)
                _logger.info("goal judge rejected", extra={"fields": {"engine": engine, "errors": error}})
    return deterministic(anchors, context.get("weeks_to_race"))
