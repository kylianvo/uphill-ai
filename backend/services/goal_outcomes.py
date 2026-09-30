"""Ground truth for goal estimation: score each assessment once its race has a result.

When a finished race result lands (manual entry or a profile sync), every unresolved
assessment for that race gets `actual_finish_sec`, and its Langfuse trace gets
`goal_hit` (finish within the ambitious..safe range) and `goal_error`
(|realistic - actual| / actual, capped at 1). Only numbers leave the process.
"""

from typing import Any

import db
from log_utils import get_logger
from services import observability

logger = get_logger(__name__)


def outcome_scores(goals: dict[str, Any], actual_sec: int) -> dict[str, float] | None:
    try:
        a, b, c = (float(goals[k]) * 60 for k in ("a", "b", "c"))
    except (KeyError, TypeError, ValueError):
        return None
    if actual_sec <= 0:
        return None
    return {
        "goal_hit": 1 if a <= actual_sec <= c else 0,
        "goal_error": min(1.0, abs(b - actual_sec) / actual_sec),
    }


def reconcile(user_id: int) -> int:
    """Resolve and score this user's assessments whose race now has a result. Never raises."""
    try:
        matches = db.match_goal_outcomes(user_id)
    except Exception as exc:
        logger.warning(f"goal outcome matching failed: {type(exc).__name__}")
        return 0
    for m in matches:
        db.set_goal_actual_finish(m["id"], m["finish_time_sec"])
        scores = outcome_scores((m.get("output") or {}).get("goals") or {}, m["finish_time_sec"])
        if scores and m.get("trace_id"):
            for name, value in scores.items():
                observability.score(
                    trace_id=m["trace_id"], name=name, value=value, score_id=f"{name}-assessment-{m['id']}"
                )
    return len(matches)


def applied_choice(goals: dict[str, Any], target_mins: float) -> str:
    """Which option the athlete applied: the goal within a minute of the target, else custom."""
    names = {"a": "ambitious", "b": "realistic", "c": "safe"}
    for key, name in names.items():
        try:
            if abs(float(goals[key]) - target_mins) <= 1:
                return name
        except (KeyError, TypeError, ValueError):
            continue
    return "custom"


def score_applied(plan_id: int, target_mins: float) -> None:
    assessment = db.latest_goal_assessment_for_plan(plan_id)
    if not assessment or not assessment.get("trace_id"):
        return
    goals = (assessment.get("output") or {}).get("goals") or {}
    observability.score(
        trace_id=assessment["trace_id"],
        name="goal_applied",
        value=applied_choice(goals, target_mins),
        score_id=f"goal-applied-{assessment['id']}",
    )
