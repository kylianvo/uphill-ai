"""get_week and week_review tool implementations."""

from typing import Any

import db
from services.coach_tools.base import ToolResult
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
        "workouts": [
            {
                "day": w.get("day_of_week"),
                "name": w.get("title"),
                "workout_type": w.get("type"),
                "distance_km": w.get("distance_km"),
                "elevation_gain_m": w.get("elevation_gain_m"),
                "description": w.get("description"),
            }
            for w in workouts
        ],
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
    card_data = {
        "week_label": f"{week_label} (Week {target_week})",
        "completed_km": review["actual"]["matched_km"],
        "planned_km": review["planned"]["distance_km"],
        "compliance_pct": review["completion_pct"],
        "completed_vert_m": review["actual"]["total_actual_vert_m"],
        "planned_vert_m": review["planned"]["elevation_gain_m"],
        "missed_workouts": [w.get("title") for w in review["missed"]],
        "coach_verdict": narrative.get("summary")
        or " ".join(narrative.get("highlights", []) + narrative.get("watch", [])),
    }
    return ToolResult(
        tool_call_id="", name="week_review", status="success", card_type="week_review", card_data=card_data
    )
