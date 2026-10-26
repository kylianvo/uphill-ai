"""get_week and week_review tool implementations."""

from typing import Any

import db
from services.coach_tools.base import ToolResult
from services.coach_tools.base import json_safe as _json_safe
from services.week_review_narrative import _rule_based_narrative


def get_week_impl(user_id: int, week_number: int | None = None) -> ToolResult:
    plan = db.get_active_plan(user_id)
    if plan is None:
        return ToolResult(tool_call_id="", name="get_week", status="error", error="no_active_plan")

    week = week_number if week_number is not None else plan.get("current_week", 1)
    workouts = db.get_plan_workouts_for_week(plan["id"], week)

    total_distance_km = round(sum(w.get("distance_km") or 0.0 for w in workouts), 1)
    total_elevation_gain_m = round(sum(w.get("elevation_gain_m") or 0.0 for w in workouts))

    card_data: dict[str, Any] = {
        "week_number": week,
        "total_distance_km": total_distance_km,
        "total_elevation_gain_m": total_elevation_gain_m,
        "plan_start_date": plan.get("start_date"),
        "race_date": plan.get("race_date"),
        "workouts": [_json_safe(w) for w in workouts],
    }
    return ToolResult(
        tool_call_id="", name="get_week", status="success", card_type="week_schedule", card_data=card_data
    )


def week_review_impl(user_id: int, weeks_ago: int = 0) -> ToolResult:
    plan = db.get_active_plan(user_id)
    if plan is None:
        return ToolResult(tool_call_id="", name="week_review", status="error", error="no_active_plan")

    current_week = plan.get("current_week", 1)
    target_week = max(1, current_week - weeks_ago)

    review = db.get_week_review(
        user_id=user_id,
        plan_id=plan["id"],
        week_number=target_week,
        plan_start_date=plan.get("start_date"),
    )
    narrative = _rule_based_narrative(review)

    week_label = "Current Week" if weeks_ago == 0 else f"{weeks_ago} Week{'s' if weeks_ago > 1 else ''} Ago"
    card_data = _json_safe(review)
    card_data["narrative"] = narrative
    # week_label kept for backward compatibility (older clients render it
    # verbatim); weeks_ago/target_week let the frontend build a bilingual
    # header from its own translation keys instead of this English string.
    card_data["week_label"] = f"{week_label} (Week {target_week})"
    card_data["weeks_ago"] = weeks_ago
    card_data["target_week"] = target_week
    return ToolResult(
        tool_call_id="", name="week_review", status="success", card_type="week_review", card_data=card_data
    )


def assess_b_race_impl(
    user_id: int,
    race_name: str,
    race_date: str,
    distance_km: float | None = None,
    elevation_gain_m: float | None = None,
    effort: str = "race",
) -> ToolResult:
    """The coach's rules on a tune-up race the athlete mentions. Read-only: adding happens on the plan screen."""
    from services import b_race

    plan = db.get_active_plan(user_id)
    if plan is None:
        return ToolResult(tool_call_id="", name="assess_b_race", status="error", error="no_active_plan")
    if not b_race.is_race_plan(plan):
        return ToolResult(tool_call_id="", name="assess_b_race", status="error", error="not_a_race_plan")
    data = {"race_name": race_name, "race_date": race_date, "distance_km": distance_km,
            "elevation_gain_m": elevation_gain_m, "effort": effort if effort in ("race", "training") else "race"}  # fmt: skip
    try:
        b_race.validate(plan, b_race._date(race_date))
        result = b_race.evaluate(db.get_user_by_id(user_id) or {"id": user_id}, plan, data)
    except ValueError as exc:
        return ToolResult(tool_call_id="", name="assess_b_race", status="error", error=str(exc))
    card = {
        **_json_safe(result),
        "how_to_add": "The athlete adds it on the Plan screen: Next races > Add race. Adding re-plans the weeks around it.",
    }
    return ToolResult(tool_call_id="", name="assess_b_race", status="success", card_data=card)
