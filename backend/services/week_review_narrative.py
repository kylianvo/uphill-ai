"""Narrative generation for the weekly training review.

Gemini is grounded strictly on the pre-computed get_week_review() numbers,
passed as structured JSON -- the prompt instructs the model to reference
nothing outside them, same grounding discipline as gear/nutrition/scheduler
(see CLAUDE.md's KB lifecycle section). If GEMINI_API_KEY is absent, the call
fails, or the response is malformed, a deterministic rule-based narrative is
returned instead: the week-review endpoint must never fail because the LLM
did.
"""

import json
from typing import Any

from google import genai
from google.genai import types
from pydantic import BaseModel

from config import settings
from log_utils import get_logger

logger = get_logger(__name__)


class WeekNarrative(BaseModel):
    summary: str
    highlights: list[str]
    watch: list[str]


def _rule_based_narrative(review: dict[str, Any]) -> dict[str, Any]:
    """Deterministic fallback: completion below 80%, vert more than 25% under
    target, a missed long run, or unplanned volume exceeding planned."""
    planned = review["planned"]
    actual = review["actual"]
    completion_pct = review["completion_pct"]

    highlights: list[str] = []
    watch: list[str] = []

    if completion_pct >= 80:
        highlights.append(f"Completed {completion_pct}% of planned training minutes this week.")
    else:
        watch.append(f"Only {completion_pct}% of planned training minutes were recorded this week.")

    planned_vert = planned["elevation_gain_m"]
    actual_vert = actual["total_actual_vert_m"]
    if planned_vert > 0:
        vert_pct = actual_vert / planned_vert * 100
        if vert_pct < 75:
            watch.append(
                f"Vert gain was {actual_vert:.0f}m vs a planned {planned_vert:.0f}m "
                f"({vert_pct:.0f}%), more than 25% under target."
            )
        else:
            highlights.append(f"Vert target met: {actual_vert:.0f}m recorded against {planned_vert:.0f}m planned.")

    long_run_missed = any(
        "long" in (w.get("type") or "").lower() or "long" in (w.get("title") or "").lower() for w in review["missed"]
    )
    if long_run_missed:
        watch.append("The scheduled long run this week was missed.")

    if planned["distance_km"] > 0 and actual["unplanned_km"] > planned["distance_km"]:
        watch.append(
            f"Unplanned volume ({actual['unplanned_km']:.1f}km) exceeded the planned "
            f"distance ({planned['distance_km']:.1f}km)."
        )

    if planned["distance_km"] > 0 and actual["matched_km"] >= planned["distance_km"] * 0.9:
        highlights.append(
            f"Distance on track: {actual['matched_km']:.1f}km recorded against "
            f"{planned['distance_km']:.1f}km planned."
        )

    if not highlights:
        highlights.append(
            f"{actual['total_actual_km']:.1f}km recorded across {actual['total_activities_count']} activities this week."
        )
    if not watch:
        watch.append("No specific concerns this week -- keep up the current routine.")

    summary = (
        f"Week {review['week_number']}: {completion_pct}% of planned training minutes recorded "
        f"({actual['total_actual_km']:.1f}km actual vs {planned['distance_km']:.1f}km planned)."
    )

    return {"summary": summary, "highlights": highlights[:3], "watch": watch[:3]}


def generate_week_narrative(review: dict[str, Any]) -> dict[str, Any]:
    """Returns {summary, highlights[], watch[]} for a get_week_review() payload.
    Tries Gemini first, grounded ONLY on the review's own numbers; falls back
    to deterministic rule-based bullets on a missing key or any failure."""
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return _rule_based_narrative(review)

    grounding = {
        "week_number": review["week_number"],
        "planned": review["planned"],
        "actual": review["actual"],
        "completion_pct": review["completion_pct"],
        "checkbox_completion_pct": review["checkbox_completion_pct"],
        "coverage": review["coverage"],
        "missed_workouts": [
            {"day_of_week": w.get("day_of_week"), "title": w.get("title"), "type": w.get("type")}
            for w in review["missed"]
        ],
        "unplanned_activities": [
            {
                "distance_km": a.get("distance_km"),
                "duration_seconds": a.get("duration_seconds"),
                "activity_type": a.get("activity_type"),
            }
            for a in review["unplanned"]
        ],
    }

    prompt = f"""You are Coach Uphill, an AI running coach writing a short weekly training review.

Below is structured JSON with this athlete's computed training numbers for ONE week. Reference ONLY the numbers in this JSON -- never invent a figure, a workout, or a fact that isn't present here.

{json.dumps(grounding, indent=2, default=str)}

Write:
- "summary": one sentence overview of the week.
- "highlights": 2-3 short bullets on what went well, each citing a real figure from the JSON above.
- "watch": 2-3 short bullets on areas to watch, each citing a real figure from the JSON above.
"""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=WeekNarrative,
                temperature=0.2,
                thinking_config=types.ThinkingConfig(thinking_level=settings.GEMINI_THINKING_LEVEL),
            ),
        )
        parsed = json.loads(response.text)
        if not parsed.get("highlights") or not parsed.get("watch"):
            raise ValueError("Gemini returned an incomplete narrative")
        return {
            "summary": parsed.get("summary", ""),
            "highlights": parsed["highlights"][:3],
            "watch": parsed["watch"][:3],
        }
    except Exception as e:
        logger.error(
            "week-review gemini narrative failed, falling back to rule-based",
            extra={
                "fields": {"service": "week_review_narrative", "engine": "gemini", "event": "error", "error": str(e)}
            },
            exc_info=True,
        )
        return _rule_based_narrative(review)
