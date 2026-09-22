"""get_week and week_review tool implementations."""

import datetime
import decimal
import uuid
from typing import Any

import db
from services.coach_tools.base import ToolResult
from services.week_review_narrative import _rule_based_narrative


def _json_safe(value: Any) -> Any:
    """Recursively convert a value (row dict, list, or scalar) into
    something json.dumps can serialize: datetime/date -> isoformat string,
    Decimal -> float, UUID -> str, everything else unchanged.

    Needed because card_data is json.dumps-ed into chat_messages.tool_calls_json
    and the SSE stream, and DB rows can carry datetime/Decimal/UUID values."""
    if isinstance(value, datetime.datetime | datetime.date):
        return value.isoformat()
    if isinstance(value, decimal.Decimal):
        return float(value)
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    return value


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
    card_data["week_label"] = f"{week_label} (Week {target_week})"
    return ToolResult(
        tool_call_id="", name="week_review", status="success", card_type="week_review", card_data=card_data
    )
