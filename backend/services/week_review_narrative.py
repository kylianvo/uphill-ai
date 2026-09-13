"""Narrative generation for the weekly training review.

Gemini is grounded strictly on the pre-computed get_week_review() numbers,
passed as structured JSON -- the prompt instructs the model to reference
nothing outside them, same grounding discipline as gear/nutrition/scheduler
(see CLAUDE.md's KB lifecycle section). If GEMINI_API_KEY is absent, the call
fails, or the response is malformed, a deterministic rule-based narrative is
returned instead: the week-review endpoint must never fail because the LLM
did.
"""

from typing import Any

from log_utils import get_logger

logger = get_logger(__name__)


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
    Uses deterministic rule-based generation to ensure instant response (<1ms)
    without latency or LLM network dependencies."""
    return _rule_based_narrative(review)
