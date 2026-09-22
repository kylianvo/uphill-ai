"""pace_strategy tool: resolves a race name to checkpoints, then delegates
the actual pacing math to main._calculate_pacing_core (the same function
the manual Tools-tab pacing calculator uses).

PacingRequest/_calculate_pacing_core are imported inside the function, not
at module level: main.py imports routers.coach_chat, which (via Task 12)
imports services.coach_chat -> services.coach_tools -> this module. A
module-level `from main import ...` here would close that into a circular
import that fails at process startup. The same local-import pattern is
already used elsewhere in this codebase for the same reason (e.g.
langchain_google_genai inside coach_model.py's _get_chat)."""

from typing import Literal

from services import race_matcher
from services.coach_tools.base import ToolResult
from services.race_estimator import RaceEstimator

_SPLIT_BIAS_BY_STRATEGY: dict[str, float] = {
    "even": 0.0,
    "conservative_start": -0.3,
    "aggressive": 0.3,
}


def pace_strategy_impl(
    user_id: int,
    race_name: str | None = None,
    target_time_hours: float | None = None,
    strategy: Literal["even", "conservative_start", "aggressive"] = "conservative_start",
) -> ToolResult:
    from main import PacingRequest, _calculate_pacing_core

    if not race_name:
        return ToolResult(tool_call_id="", name="pace_strategy", status="error", error="race_name_required")

    matched = race_matcher.match_race(race_name)
    if matched is None:
        return ToolResult(tool_call_id="", name="pace_strategy", status="error", error="race_not_found")

    profile = race_matcher.course_profile(race_name, matched.distance_label)
    if profile is not None:
        checkpoints = profile["checkpoints"]
    elif matched.distance_km and matched.elevation_gain_m is not None:
        checkpoints = RaceEstimator.synthesize_course(matched.distance_km, matched.elevation_gain_m)
    else:
        return ToolResult(tool_call_id="", name="pace_strategy", status="error", error="no_course_data")

    request = PacingRequest(
        checkpoints=checkpoints,
        target_time_mins=(target_time_hours * 60) if target_time_hours else None,
        split_bias=_SPLIT_BIAS_BY_STRATEGY.get(strategy, -0.3),
    )
    if request.target_time_mins is None:
        return ToolResult(tool_call_id="", name="pace_strategy", status="error", error="target_time_required")

    try:
        paced_checkpoints = _calculate_pacing_core(request=request)
    except Exception:
        return ToolResult(tool_call_id="", name="pace_strategy", status="error", error="pacing_calculation_failed")

    total_distance_km = checkpoints[-1]["distance_meters"] / 1000.0 if checkpoints else matched.distance_km
    card_data = {
        "race_name": matched.race_name,
        "distance_label": matched.distance_label,
        "total_distance_km": round(total_distance_km, 1) if total_distance_km else matched.distance_km,
        "total_elevation_m": matched.elevation_gain_m,
        "target_time_formatted": f"{int(target_time_hours)}h {round((target_time_hours % 1) * 60)}m"
        if target_time_hours
        else None,
        "splits": paced_checkpoints,
    }
    return ToolResult(
        tool_call_id="", name="pace_strategy", status="success", card_type="pacing_splits", card_data=card_data
    )
