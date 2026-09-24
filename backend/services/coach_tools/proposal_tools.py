"""propose_schedule_change: validates a batch of calendar operations with the
guarded engine and records a `proposed` chat_proposals row. It NEVER writes
workouts -- the athlete applies it with the card's Apply button
(services/schedule_proposals.py)."""

import json
from typing import Any

import db
from services.coach_tools.base import ToolResult
from services.coach_tools.base import json_safe as _json_safe

NAME = "propose_schedule_change"

# Plain-language reasons fed back to the model so it can explain a refusal.
_REASONS = {
    "G1_not_owner": "that workout is not in the athlete's active plan",
    "G2_history": "that workout is already completed or matched to a recorded activity, so it can't move",
    "G3_past_target": "the target day is in the past",
    "G4_window": "moves between weeks are limited to this week and next week",
    "G5_out_of_plan": "the target week is outside the plan",
    "G6_coach_linked": "the athlete has a coach, so schedule changes must go through the coach",
    "G7_no_dates": "this plan has no start date, so only same-week day swaps are possible",
    "NOTHING_to_move": "nothing would change -- those workouts are already on those days (the change may already "
    "have been applied); do not ask the athlete to apply anything",
    "INVALID_operation": "an operation is malformed (check workout ids, week numbers and day names)",
}


def _moves_key(moves: list[dict[str, Any]]) -> list[tuple[Any, Any, Any]]:
    return sorted((m["workout_id"], m["to_week"], m["to_day"]) for m in moves)


def propose_schedule_change_impl(
    *, user_id: int, ctx: Any, operations: list[dict[str, Any]], rationale: str
) -> ToolResult:
    # Imported lazily: services.calendar_rules (and services.calendar_ops, which
    # wraps it) import services.coach_tools.base at module scope, and this module
    # sits inside the services.coach_tools package, so a module-level import here
    # would deadlock the two packages' init order (same pattern as pacing_tools.py).
    from services import calendar_ops
    from services.calendar_rules import GuardViolation

    try:
        changes = calendar_ops.preview(user_id, ctx.plan_id, operations, ctx.today, agent=True)
    except GuardViolation as gv:
        reason = _REASONS.get(gv.code, gv.code)
        return ToolResult(
            tool_call_id="",
            name=NAME,
            status="error",
            error=f"{gv.code}: {reason}. details={json.dumps(gv.params, default=str)}",
        )
    # A typed "yes" can make the model call this again with the same change:
    # never create a second card for a change that is already waiting on Apply.
    key = _moves_key(changes.moves)
    for open_proposal in db.get_open_chat_proposals(ctx.thread_id, ctx.plan_id):
        if _moves_key(open_proposal["diff"]) == key:
            return ToolResult(
                tool_call_id="",
                name=NAME,
                status="error",
                error=f"DUPLICATE_pending: this exact change is already proposed on card #{open_proposal['id']} "
                "and is waiting for the athlete -- do not propose it again; tell them to tap Apply on that card.",
            )
    plan = db.get_active_plan(user_id) or {}
    proposal_id = db.create_chat_proposal(
        user_id=user_id,
        thread_id=ctx.thread_id,
        plan_id=ctx.plan_id,
        operations=operations,
        fingerprints=changes.fingerprints,
        diff=changes.diff,
        warnings=changes.warnings,
        rationale=rationale,
    )
    return ToolResult(
        tool_call_id="",
        name=NAME,
        status="success",
        card_type="schedule_proposal",
        card_data={
            "proposal_id": proposal_id,
            "status": "proposed",
            "operations": operations,
            "diff": changes.diff,
            "warnings": changes.warnings,
            "rationale": rationale,
            "plan_start_date": _json_safe(plan.get("start_date")),
            "race_date": _json_safe(plan.get("race_date")),
        },
    )


REBUILD_NAME = "propose_rebuild_week"

_REBUILD_REASONS = {
    **_REASONS,
    "G3_past_target": "that week is already over",
    "G4_window": "only this week or next week can be rebuilt",
    "G5_out_of_plan": "that week is outside the plan or not generated yet",
    "NOTHING_to_rebuild": "every remaining day of that week is already completed or fixed, so there is nothing "
    "to rebuild",
    "REBUILD_limit": "the daily rebuild limit is reached -- suggest propose_schedule_change for small moves, or "
    "try again tomorrow",
}


def _rebuild_error(code: str, detail: str) -> ToolResult:
    return ToolResult(tool_call_id="", name=REBUILD_NAME, status="error", error=f"{code}: {detail}")


def propose_rebuild_week_impl(
    *,
    user_id: int,
    ctx: Any,
    week: int,
    fatigue_level: str,
    reason: str,
    available_days: list[str] | None = None,
    long_run_day: str | None = None,
    has_gym_access: bool | None = None,
    use_treadmill: bool | None = None,
) -> ToolResult:
    """Starts a background draft of `week` and records a `generating` rebuild
    proposal. Writes no workouts -- the athlete taps Apply on the card."""
    # Lazy for the same package-init-order reason as propose_schedule_change_impl.
    from services import week_rebuild
    from services.calendar_rules import GuardViolation

    days = list(dict.fromkeys(available_days)) if available_days else None
    if long_run_day and days and long_run_day not in days:
        return _rebuild_error("INVALID_operation", "long_run_day must be one of available_days")
    request = week_rebuild.RebuildRequest(
        week_number=week,
        fatigue_level=fatigue_level,
        fatigue_notes=reason,
        preferred_days=days,
        days_per_week=len(days) if days else None,
        long_run_day=long_run_day,
        has_gym_access=has_gym_access,
        use_treadmill=use_treadmill,
    )
    try:
        out = week_rebuild.request_rebuild(
            user_id=user_id,
            thread_id=ctx.thread_id,
            plan_id=ctx.plan_id,
            today=ctx.today,
            request=request,
            rationale=reason,
        )
    except GuardViolation as gv:
        if gv.code == "DUPLICATE_pending":
            return _rebuild_error(
                gv.code,
                f"a rebuild of week {gv.params.get('week')} is already open on card #{gv.params.get('proposal_id')} "
                "-- do not propose it again; tell the athlete to review it there (or discard it first).",
            )
        detail = _REBUILD_REASONS.get(gv.code, gv.code)
        return _rebuild_error(gv.code, f"{detail}. details={json.dumps(gv.params, default=str)}")
    plan = db.get_active_plan(user_id) or {}
    return ToolResult(
        tool_call_id="",
        name=REBUILD_NAME,
        status="success",
        card_type="schedule_rebuild",
        card_data={
            "proposal_id": out["proposal_id"],
            "status": "generating",
            "week": out["week"],
            "from_day": out["from_day"],
            "rationale": reason,
            "plan_start_date": _json_safe(plan.get("start_date")),
            "race_date": _json_safe(plan.get("race_date")),
            "note": f"drafting week {out['week']} from {out['from_day']}; the card shows the draft when ready -- "
            "do not describe new sessions yourself; the athlete must tap Apply.",
        },
    )
