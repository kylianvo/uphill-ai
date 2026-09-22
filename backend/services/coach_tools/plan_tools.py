"""get_week and week_review tool implementations."""

from typing import Any

import db
from services.coach_tools.base import ToolResult


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
