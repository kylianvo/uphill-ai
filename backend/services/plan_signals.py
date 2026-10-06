"""Quality signals for generated training blocks, attached to their Langfuse traces.

On each block generation:
- `plan_checks` (share of deterministic checks passed) goes on the new trace;
- if the same block was generated for this plan in the last 72 h, the earlier trace gets
  `plan_reworked` = 1 (the athlete or coach regenerated it soon after);
- if the plan moved on to a later block, the earlier trace gets `block_compliance`
  (share of that block's sessions the athlete completed).
The new trace id is then stored on the plan. Never raises into plan generation.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import db
from log_utils import get_logger
from services import observability, plan_checks

logger = get_logger(__name__)

REWORK_WINDOW = timedelta(hours=72)


def _as_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def record_generation(
    *,
    plan_id: int,
    user_id: int | None,
    block_number: int,
    workouts: list[dict[str, Any]],
    trace_id: str | None,
    tier: str | None = None,
    measured_weekly_km: float | None = None,
) -> None:
    if not plan_id or not trace_id:
        return
    try:
        # First, so a plan-checks failure below cannot swallow them.
        if tier:
            observability.score(trace_id=trace_id, name="plan_tier", value=tier)
        if measured_weekly_km:
            week2 = sum(float(w.get("distance_km") or 0) for w in workouts if w.get("week_number") == 2)
            if week2 > 0:
                ratio = week2 / measured_weekly_km
                observability.score(trace_id=trace_id, name="plan_volume_fit", value=round(min(ratio, 1 / ratio), 3))
        share = plan_checks.pass_share(plan_checks.run_checks(workouts))
        if share is not None:
            observability.score(trace_id=trace_id, name="plan_checks", value=share)

        previous = db.get_plan_generation_trace(plan_id)
        prev_trace = previous.get("generation_trace_id") if previous else None
        if prev_trace and prev_trace != trace_id:
            prev_block = previous.get("generation_block")
            traced_at = _as_utc(previous.get("generation_traced_at"))
            if prev_block == block_number and traced_at and datetime.now(UTC) - traced_at <= REWORK_WINDOW:
                observability.score(
                    trace_id=prev_trace, name="plan_reworked", value=1, score_id=f"plan-reworked-{prev_trace}"
                )
            elif isinstance(prev_block, int) and prev_block < block_number and user_id:
                from services.matching.block_evaluator import evaluate_block_performance

                evaluation = evaluate_block_performance(user_id, plan_id, prev_block)
                if evaluation.get("sessions_total"):
                    observability.score(
                        trace_id=prev_trace,
                        name="block_compliance",
                        value=evaluation["sessions_completed"] / evaluation["sessions_total"],
                        score_id=f"block-compliance-{plan_id}-{prev_block}",
                    )
        db.set_plan_generation_trace(plan_id, trace_id, block_number)
    except Exception as exc:
        logger.warning(f"plan signals failed: {type(exc).__name__}")
