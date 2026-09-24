"""Week rebuild (Coach Chat Sub-project 4b).

Regenerates the rest of one plan week. Two callers share everything here:
the Scheduler's adapt-week (writes directly -- the form submit is the
confirmation) and the chat tool propose_rebuild_week (drafts in the
background, the athlete taps Apply). The pure rules come first: which days
are kept (past days, completed, GPS-matched), the diff and the warnings."""

import asyncio
import datetime as dt
import threading
from collections.abc import Callable, Coroutine
from dataclasses import asdict, dataclass
from typing import Any

import db
from config import settings
from services import calendar_ops
from services.calendar_rules import (
    DAYS,
    FINGERPRINT_FIELDS,
    VOLUME_SHIFT_THRESHOLD,
    GuardViolation,
    _is_hard,
    _is_long_run,
    current_week,
    start_monday,
)
from services.coach_tools.base import json_safe
from services.course_match import resolve_course_match
from services.plan_generator import PlanGenerator

# Whole-week staleness: 4a's placement fields plus the content an edit changes.
REBUILD_FINGERPRINT_FIELDS = FINGERPRINT_FIELDS + ("title", "type", "duration_minutes", "session_slot")


@dataclass(frozen=True)
class RebuildRange:
    week: int
    from_day: str
    kept_ids: tuple[int, ...]
    replaceable_ids: tuple[int, ...]
    kept_slots: frozenset[tuple[str, str]]


def _day_idx(day: Any) -> int:
    return DAYS.index(day) if day in DAYS else len(DAYS)


def _slot(row: dict[str, Any]) -> str:
    return row.get("session_slot") or "main"


def _is_history(row: dict[str, Any]) -> bool:
    return row.get("matched_activity_id") is not None or int(row.get("is_completed") or 0) == 1


def rebuild_range(plan: dict[str, Any], workouts: list[dict[str, Any]], week: int, today: dt.date) -> RebuildRange:
    """Which workouts of `week` a rebuild may replace. A plan without a
    start_date has no calendar, so it rebuilds from Monday keeping only
    history (the chat caller refuses G7 before getting here)."""
    total_weeks = int(plan.get("total_weeks") or 0)
    generated = max((int(w["week_number"]) for w in workouts), default=0)
    if not 1 <= week <= total_weeks or week > generated:
        raise GuardViolation("G5_out_of_plan", {"week": week})
    from_idx = 0
    monday = start_monday(plan.get("start_date"))
    if monday is not None:
        cur = current_week(monday, today)
        if week < cur:
            raise GuardViolation("G3_past_target", {"week": week})
        if week == cur:
            from_idx = today.weekday()
    rows = [w for w in workouts if int(w["week_number"]) == week]
    kept = [w for w in rows if _day_idx(w["day_of_week"]) < from_idx or _is_history(w)]
    kept_ids = {w["id"] for w in kept}
    replaceable = [w for w in rows if w["id"] not in kept_ids]
    kept_days = {w["day_of_week"] for w in kept}
    if not replaceable and all(d in kept_days for d in DAYS[from_idx:]):
        raise GuardViolation("NOTHING_to_rebuild", {"week": week})
    return RebuildRange(
        week=week,
        from_day=DAYS[from_idx],
        kept_ids=tuple(sorted(kept_ids)),
        replaceable_ids=tuple(sorted(w["id"] for w in replaceable)),
        kept_slots=frozenset((w["day_of_week"], _slot(w)) for w in kept),
    )


def week_fingerprints(workouts: list[dict[str, Any]], week: int) -> dict[str, dict[str, Any]]:
    return {
        str(w["id"]): {f: json_safe(w.get(f)) for f in REBUILD_FINGERPRINT_FIELDS}
        for w in workouts
        if int(w["week_number"]) == week
    }


def filter_draft(draft: list[dict[str, Any]], rng: RebuildRange) -> list[dict[str, Any]]:
    """Generated workouts that may be written: the target week only, from
    `from_day` on, never onto a kept (day, slot)."""
    from_idx = DAYS.index(rng.from_day)
    out = []
    for wo in draft:
        if int(wo.get("week_number") or 0) != rng.week or _day_idx(wo.get("day_of_week")) < from_idx:
            continue
        if _day_idx(wo.get("day_of_week")) >= len(DAYS):
            continue
        if (wo["day_of_week"], _slot(wo)) in rng.kept_slots:
            continue
        out.append({**wo, "week_number": rng.week})
    return out


def _brief(row: dict[str, Any]) -> dict[str, Any]:
    return json_safe(
        {
            "id": row.get("id"),
            "title": row.get("title"),
            "type": row.get("type"),
            "duration_minutes": row.get("duration_minutes"),
            "distance_km": row.get("distance_km"),
            "elevation_gain_m": row.get("elevation_gain_m"),
            "session_slot": _slot(row),
            "target_zone": row.get("target_zone"),
        }
    )


def _totals(rows: list[dict[str, Any]]) -> dict[str, float]:
    return {
        "min": round(sum(float(r.get("duration_minutes") or 0) for r in rows)),
        "km": round(sum(float(r.get("distance_km") or 0) for r in rows), 1),
        "vert": round(sum(float(r.get("elevation_gain_m") or 0) for r in rows)),
    }


def _week_after(workouts: list[dict[str, Any]], rng: RebuildRange, draft: list[dict[str, Any]]) -> list[dict[str, Any]]:
    kept = [w for w in workouts if w["id"] in set(rng.kept_ids)]
    return kept + draft


def build_diff(workouts: list[dict[str, Any]], rng: RebuildRange, draft: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [w for w in workouts if int(w["week_number"]) == rng.week]
    kept, replaceable = set(rng.kept_ids), set(rng.replaceable_ids)
    days = [
        {
            "day": d,
            "kept": [_brief(w) for w in rows if w["id"] in kept and w["day_of_week"] == d],
            "before": [_brief(w) for w in rows if w["id"] in replaceable and w["day_of_week"] == d],
            "after": [json_safe(wo) for wo in draft if wo["day_of_week"] == d],
        }
        for d in DAYS
    ]
    return {
        "week": rng.week,
        "from_day": rng.from_day,
        "days": days,
        "totals": {"before": _totals(rows), "after": _totals(_week_after(rows, rng, draft))},
    }


def rebuild_warnings(
    workouts: list[dict[str, Any]], rng: RebuildRange, draft: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """W1 on the rebuilt days (and the kept day just before them); W2 on the
    week total. No W3: rebuilt workouts are inserted approved."""
    rows = [w for w in workouts if int(w["week_number"]) == rng.week]
    after = _week_after(rows, rng, draft)
    by_idx = {i: [r for r in after if _day_idx(r["day_of_week"]) == i] for i in range(len(DAYS))}
    warnings: list[dict[str, Any]] = []
    from_idx = DAYS.index(rng.from_day)
    for i in range(max(0, from_idx - 1), len(DAYS)):
        if i >= from_idx and sum(1 for r in by_idx[i] if _is_hard(r)) >= 2:
            warnings.append(
                {"code": "W1_hard_stacking", "params": {"kind": "same_day", "week": rng.week, "day": DAYS[i]}}
            )
        if i + 1 < len(DAYS) and any(_is_hard(r) for r in by_idx[i]) and any(_is_long_run(r) for r in by_idx[i + 1]):
            warnings.append(
                {"code": "W1_hard_stacking", "params": {"kind": "before_long_run", "week": rng.week, "day": DAYS[i]}}
            )
    was = sum(float(r.get("duration_minutes") or 0) for r in rows)
    now = sum(float(r.get("duration_minutes") or 0) for r in after)
    if was > 0 and abs(now - was) / was > VOLUME_SHIFT_THRESHOLD:
        warnings.append(
            {
                "code": "W2_volume_shift",
                "params": {"week": rng.week, "before_minutes": round(was), "after_minutes": round(now)},
            }
        )
    return warnings


@dataclass
class RebuildRequest:
    """Per-week inputs -- the same fields and meanings as main.AdaptWeekRequest
    (minus plan_id / max_continuous_jog_min / client_today)."""

    week_number: int
    overall_rpe: int | None = None
    fatigue_level: str | None = None
    fatigue_notes: str | None = None
    athlete_notes: str | None = None
    coach_notes: str | None = None
    preferred_days: list[str] | None = None
    long_run_day: str | None = None
    days_per_week: int | None = None
    double_session_days: list[str] | None = None
    has_gym_access: bool | None = None
    use_treadmill: bool | None = None
    training_environment: str | None = None
    lang: str | None = None


@dataclass
class RebuildInputs:
    plan_id: int
    week: int
    user: dict[str, Any]
    race_info: dict[str, Any]
    total_weeks: int
    block_context: str
    api_key: str | None
    block_number: int


@dataclass
class WeekDraft:
    workouts: list[dict[str, Any]]
    resolved_tier: str | None


def load_plan_rows(plan_id: int) -> list[dict[str, Any]]:
    with db.engine.connect() as conn:
        return db.get_plan_workouts_for_placement(conn, plan_id, lock=False)


def build_rebuild_inputs(
    athlete_id: int,
    plan: dict[str, Any],
    all_workouts: list[dict[str, Any]],
    rng: RebuildRange,
    request: RebuildRequest,
) -> RebuildInputs:
    """The adapt-week prompt builder, moved from main._adapt_week_for_athlete
    unchanged except for the partial-week additions marked `4b:`."""
    fresh_user = db.get_user_by_id(athlete_id) or {}

    # Map fatigue_level (5 feelings: very_light/light/moderate/hard/max_effort) and overall_rpe coherently
    fatigue_level = request.fatigue_level
    overall_rpe = request.overall_rpe
    level_to_rpe = {
        "very_light": 2,
        "very light": 2,
        "easy": 3,
        "light": 4,
        "medium": 6,
        "moderate": 6,
        "hard": 8,
        "exhausted": 10,
        "max_effort": 10,
        "max effort": 10,
    }
    if fatigue_level and overall_rpe is None:
        overall_rpe = level_to_rpe.get(fatigue_level.lower(), 6)
    elif overall_rpe is not None and not fatigue_level:
        if overall_rpe <= 2:
            fatigue_level = "very_light"
        elif overall_rpe <= 4:
            fatigue_level = "light"
        elif overall_rpe <= 6:
            fatigue_level = "moderate"
        elif overall_rpe <= 8:
            fatigue_level = "hard"
        else:
            fatigue_level = "max_effort"

    context_lines: list[str] = [
        f"ADAPTATION & REGENERATION FOR WEEK {request.week_number}:",
    ]
    # The beginner progression metric, surfaced so the model can move it deliberately
    # rather than inferring progress from weekly kilometres.
    _jog_min = fresh_user.get("max_continuous_jog_min")
    if _jog_min:
        context_lines.append(
            f"  Longest Unbroken Jog: {_jog_min} minutes. For a new runner this is THE progress "
            f"metric -- move it or hold it deliberately, and name it in the workout descriptions."
        )
    if fatigue_level:
        norm_fl = fatigue_level.lower().replace(" ", "_")
        fl_display_map = {
            "very_light": "VERY LIGHT",
            "light": "LIGHT",
            "moderate": "MODERATE",
            "hard": "HARD",
            "max_effort": "MAX EFFORT",
            "easy": "LIGHT",
            "medium": "MODERATE",
            "exhausted": "MAX EFFORT",
        }
        display_feeling = fl_display_map.get(norm_fl, fatigue_level.upper())
        context_lines.append(f"  Current Athlete Feeling: {display_feeling} (equivalent RPE ~{overall_rpe or 6}/10)")
        if norm_fl in ("very_light",):
            context_lines.append(
                "  Feeling Very Light: Athlete is effortless and underloaded. "
                "IMPORTANT: Increase training stimulus by adding 5-10% weekly volume or progressing key quality sessions (intervals/tempo) while respecting recovery."
            )
        elif norm_fl in ("light", "easy"):
            context_lines.append(
                "  Feeling Light / Fresh: Athlete is well recovered and ready to absorb more load. "
                "IMPORTANT: Do NOT reduce weekly training volume. Match or slightly increase the planned week's total duration and distance. "
                "Keep all key quality sessions (intervals, tempo, long run) intact. "
                "You may optionally add 5% more volume to the easy/base runs to capitalise on the athlete's freshness."
            )
        elif norm_fl in ("moderate", "medium"):
            context_lines.append(
                "  Feeling Moderate: Normal training fatigue, manageable and sustainable. Keep balanced volume with steady progression."
            )
        elif norm_fl in ("hard",):
            context_lines.append(
                "  Feeling Hard / Tired: Elevated fatigue or heavy legs. Ease off high-intensity sessions and trim volume by 10-15%."
            )
        elif norm_fl in ("max_effort", "exhausted"):
            context_lines.append(
                "  Feeling Max Effort / Exhausted: High fatigue or overreaching. Prescribe an active recovery/deload week with 20-30% reduced volume and no high-intensity work."
            )
    elif overall_rpe is not None:
        context_lines.append(f"  Current Athlete Exertion / Fatigue RPE: {overall_rpe}/10")

    if request.fatigue_notes:
        context_lines.append(f'  Fatigue & Adaptation reason: "{request.fatigue_notes}"')
    if request.athlete_notes:
        context_lines.append(f'  Athlete notes: "{request.athlete_notes}"')
    if request.coach_notes:
        context_lines.append(f'  Coach instructions: "{request.coach_notes}"')

    # Double session preferences in single-week adaptation prompt
    target_double_sessions = (
        request.double_session_days if request.double_session_days is not None else plan.get("double_session_days")
    )
    if target_double_sessions:
        if isinstance(target_double_sessions, str):
            try:
                import json

                ds_list = json.loads(target_double_sessions)
            except Exception:
                ds_list = [d.strip() for d in target_double_sessions.split(",") if d.strip()]
        else:
            ds_list = list(target_double_sessions)
        if ds_list:
            context_lines.append(
                f"  Double Session Preference: Athlete requested 2 sessions on: {', '.join(ds_list)} "
                "(e.g., Morning run + Afternoon run/strength/mobility, or Easy AM + Quality PM). Schedule TWO workouts on these days."
            )

    prev_wk = request.week_number - 1
    # Week 1 has no prior week; the volume bounds below still read prev_wos.
    prev_wos = []
    if prev_wk >= 1:
        prev_wos = [w for w in all_workouts if w.get("week_number") == prev_wk and w.get("type") != "Rest"]
        completed_prev = [w for w in prev_wos if w.get("is_completed") == 1]
        actual_vol = db.get_block_actual_volume(
            user_id=athlete_id,
            plan_id=plan["id"],
            wk_start=prev_wk,
            wk_end=prev_wk,
            plan_start_date=plan.get("start_date"),
        )
        if actual_vol.get("total_activities_count", 0) > 0:
            actual_km = actual_vol["total_actual_km"]
            actual_min = actual_vol["total_actual_minutes"]
            actual_vert = actual_vol["total_actual_vert_m"]
        else:
            actual_km = sum(w.get("distance_km") or 0 for w in completed_prev)
            actual_min = sum(w.get("duration_minutes") or 0 for w in completed_prev)
            actual_vert = sum(w.get("elevation_gain_m") or 0 for w in completed_prev)
        planned_km = sum(w.get("distance_km") or 0 for w in prev_wos)
        planned_min = sum(w.get("duration_minutes") or 0 for w in prev_wos)
        context_lines.append(
            f"  Prior Week ({prev_wk}) Volume: Actual {actual_km:.1f}km / {actual_min/60:.1f}h"
            + (f" (+{actual_vert:.0f}m D+)" if actual_vert > 0 else "")
            + f" vs Planned {planned_km:.1f}km / {planned_min/60:.1f}h"
        )
        # Check if athlete missed an ME session in previous week (Scott Johnston Rule 7)
        missed_me = [
            w
            for w in prev_wos
            if (
                "ME" in (w.get("type") or "").upper()
                or "MUSCULAR ENDURANCE" in (w.get("title") or "").upper()
                or "CIRCUIT" in (w.get("title") or "").upper()
            )
            and w.get("is_completed") != 1
        ]
        if missed_me:
            context_lines.append(
                "  ME Progression Adjustment (Scott Johnston Rule 7): Athlete missed a scheduled Muscular Endurance (ME) session in the prior week. "
                "Drop the ME progression back by 2 workouts (reduce rounds, reps, or pack weight) to allow safe tendon and joint re-adaptation."
            )

    # Note any workouts already completed/matched in the target week
    curr_completed = [
        w for w in all_workouts if w.get("week_number") == request.week_number and w.get("is_completed") == 1
    ]
    if curr_completed:
        context_lines.append(
            f"  Note: Workouts already completed/matched in Week {request.week_number} will be PRESERVED:"
        )
        for cw in curr_completed:
            context_lines.append(
                f"    - {cw.get('day_of_week')}: {cw.get('title')} ({cw.get('duration_minutes', 0):.0f}min, {cw.get('distance_km', 0):.1f}km)"
            )

    # 4b: in the current week the days before from_day already happened -- the
    # model must not fill them or pile their missed volume onto the rest.
    if rng.from_day != "Monday":
        fixed_end = DAYS[DAYS.index(rng.from_day) - 1]
        context_lines.append(
            f"  Days Monday-{fixed_end} are fixed and already happened; schedule sessions only from "
            f"{rng.from_day} to Sunday."
        )
        context_lines.append("  Do NOT make up missed sessions from earlier in the week.")

    # Volume bounds for the target week.
    #
    # Two deliberate choices here, both fixing production bugs:
    #
    # 1. BOUNDS ARE IN MINUTES, not km. post_process_workouts discards whatever
    #    distance the model returns and recomputes distance_km = duration / zone2_pace,
    #    so distance is a pure function of duration. A km bound was therefore a
    #    disguised minutes bound, converted at a pace the athlete may not run -- for a
    #    walk-run beginner whose real pace is far slower than her Zone 2 setting, the
    #    conversion inflated every figure. Minutes are what the athlete actually
    #    controls and what the model actually sets.
    #
    # 2. THE ANCHOR IS PLANNED VOLUME, not completed volume. Anchoring on completed
    #    volume meant that adapting a week *because you were busy* -- the single most
    #    common reason to adapt -- shrank the next week in proportion to what you
    #    missed, while the prompt still described it as a 2-8% increase. Under-
    #    completion is now reported as its own adherence signal with its own
    #    instruction, so the model can coach the missed week instead of silently
    #    rebaselining onto it.
    target_wos = [w for w in all_workouts if w.get("week_number") == request.week_number and w.get("type") != "Rest"]
    if target_wos:
        completed_target = [w for w in target_wos if w.get("is_completed") == 1]
        completed_min = sum(w.get("duration_minutes") or 0 for w in completed_target)
        uncompleted_count = max(1, len(target_wos) - len(completed_target))

        target_planned_min = sum(w.get("duration_minutes") or 0 for w in target_wos)
        # current_weekly_km -> minutes needs a pace; 6 min/km is the same rough
        # conversion the rule-based fallback uses for its own volume estimate.
        user_weekly_min = float(fresh_user.get("current_weekly_km") or 0.0) * 6.0

        prior_planned_min = planned_min if prev_wos else 0.0
        prior_ref_min = (
            prior_planned_min
            or (target_planned_min if target_planned_min > 0 else 0.0)
            or (user_weekly_min if user_weekly_min > 0 else 180.0)
        )

        # Adherence is a coaching input, never a smaller baseline.
        adherence_note = ""
        if prev_wos and prior_planned_min > 0:
            adherence = (actual_min or 0.0) / prior_planned_min
            if adherence < 0.8:
                adherence_note = (
                    f"  Prior-Week Adherence: the athlete completed {adherence * 100:.0f}% of Week {prev_wk}'s "
                    f"planned time ({actual_min:.0f} of {prior_planned_min:.0f} min).\n"
                    f"  IMPORTANT: do NOT progress volume on top of a week that was not completed, and do NOT "
                    f"shrink the plan as a punishment either. HOLD this week at roughly the same planned volume "
                    f"as Week {prev_wk} so the athlete gets a second chance at the same stimulus. Say so plainly "
                    f"in the workout descriptions -- name it as a repeat, not a setback.\n"
                )
                # Repeat the week rather than progress off an incomplete one.
                floor_mult, ceil_mult = 0.95, 1.02
            else:
                floor_mult, ceil_mult = None, None
        else:
            floor_mult, ceil_mult = None, None

        if floor_mult is None:
            fatigue_normalized = (fatigue_level or "moderate").lower().replace(" ", "_")
            if fatigue_normalized in ("very_light", "light", "easy"):
                floor_mult, ceil_mult = 1.02, 1.08
            elif fatigue_normalized in ("moderate", "medium"):
                floor_mult, ceil_mult = 0.98, 1.05
            elif fatigue_normalized in ("hard", "heavy"):
                floor_mult, ceil_mult = 0.85, 0.90
            else:  # max_effort, exhausted
                floor_mult, ceil_mult = 0.70, 0.80

        target_floor_min = prior_ref_min * floor_mult
        target_ceil_min = prior_ref_min * ceil_mult

        rem_floor_min = max(0.0, target_floor_min - completed_min)
        rem_ceil_min = max(rem_floor_min + 15.0, target_ceil_min - completed_min)

        # 4b: a partial week only has its replaceable days left -- cap the
        # remaining budget at what those days were planned for.
        if rng.from_day != "Monday":
            replaceable = set(rng.replaceable_ids)
            replaceable_min = sum(float(w.get("duration_minutes") or 0) for w in target_wos if w["id"] in replaceable)
            if replaceable_min > 0:
                rem_ceil_min = min(rem_ceil_min, replaceable_min * ceil_mult)
                rem_floor_min = min(rem_floor_min, rem_ceil_min)

        # Precedence. Without this the 5-tier RPE table above ("Very Light ... increase
        # stimulus") sat as prose above a "MUST ... DO NOT exceed" numeric ceiling with
        # nothing saying which wins, so the number always won and an athlete asking for
        # more work while reporting very light effort got less. The request does not
        # remove the cap -- it decides where inside the band the week lands.
        precedence_note = (
            "  Bound Precedence: these bounds are a safety cap, not a target. When the athlete reports "
            "LIGHT or VERY LIGHT effort AND asks for more work, place the week at the TOP of the range "
            "(and prefer adding time to easy/base runs rather than adding intensity). When they report "
            "HARD or MAX EFFORT, place it at the BOTTOM. Never return a week below the floor because a "
            "previous week was missed -- see the adherence note above if present.\n"
        )

        volume_guidance = (
            f"  Week {request.week_number} Volume Bounds (in MINUTES of training time -- "
            f"distance is derived from duration, so time is the quantity to set):\n"
            f"    - Reference: Week {prev_wk} planned {prior_ref_min:.0f} min\n"
            f"    - Target Full Week Total: {target_floor_min:.0f}-{target_ceil_min:.0f} min\n"
            f"    - Completed So Far: {completed_min:.0f} min ({len(completed_target)} sessions)\n"
            f"    - Remaining {uncompleted_count} Sessions: total between {rem_floor_min:.0f} and "
            f"{rem_ceil_min:.0f} min.\n"
            f"{adherence_note}"
            f"{precedence_note}"
            f"  Weekday Session Durations: standard weekday runs (Mon-Fri) are typically 45-75 minutes, "
            f"but NEVER stretch a session beyond what this athlete's current ability supports -- a "
            f"beginner's weekday run may be 20-30 minutes and that is correct. Do NOT schedule "
            f"90-120+ min long runs on weekdays."
        )
        context_lines.append(volume_guidance)

    block_context = "\n".join(context_lines)

    _, _, course_context = resolve_course_match(
        plan.get("race_name"), plan.get("course_distance_km"), plan.get("course_elevation_gain_m")
    )

    readiness_summary = db.get_recent_readiness_summary(athlete_id, days=7)
    historical_ceiling = db.get_user_activity_ceiling(athlete_id)

    # Week-specific preference overrides (without mutating plan DB defaults)
    preferred_days = request.preferred_days if request.preferred_days is not None else plan.get("preferred_run_days")
    long_run_day = request.long_run_day if request.long_run_day is not None else plan.get("long_run_day")
    days_per_week = request.days_per_week if request.days_per_week is not None else plan.get("days_per_week")
    double_session_days = (
        request.double_session_days if request.double_session_days is not None else plan.get("double_session_days")
    )
    has_gym_access = request.has_gym_access if request.has_gym_access is not None else plan.get("has_gym_access", False)
    use_treadmill = request.use_treadmill if request.use_treadmill is not None else plan.get("use_treadmill", False)
    training_environment = (
        request.training_environment
        if request.training_environment is not None
        else (plan.get("training_environment") or "flat")
    )

    race_info = {
        "name": plan.get("race_name", "Training Plan"),
        "date": plan.get("race_date"),
        "terrain": fresh_user.get("terrain", "trail"),
        "goal_type": plan.get("goal_type"),
        "target_time_hours": plan.get("target_time_hours"),
        "course_distance_km": plan.get("course_distance_km"),
        "course_elevation_gain_m": plan.get("course_elevation_gain_m"),
        "course_context": course_context,
        "preferred_days": preferred_days,
        "long_run_day": long_run_day,
        "days_per_week": days_per_week,
        "double_session_days": double_session_days,
        "has_gym_access": has_gym_access,
        "use_treadmill": use_treadmill,
        "training_environment": training_environment,
        "plan_start_date": plan.get("start_date"),
        "athlete_notes": request.athlete_notes or plan.get("athlete_notes") or fresh_user.get("athlete_notes"),
        "historical_ceiling": historical_ceiling,
        # Explicit per-plan tier override; None means the generator derives it.
        "athlete_tier": plan.get("athlete_tier"),
        "readiness_summary": readiness_summary,
        "lang": (
            "vi"
            if (request.lang and request.lang.lower().startswith("vi"))
            or (fresh_user.get("lang") and fresh_user.get("lang").lower().startswith("vi"))
            or any(
                c in "àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ"
                for c in str(request.fatigue_notes or "")
                + str(request.athlete_notes or "")
                + str(request.coach_notes or "")
            )
            else (request.lang or fresh_user.get("lang", "en"))
        ),
        "coach_notes": request.coach_notes,
    }

    model_api_key = fresh_user.get("gemini_api_key") or settings.GEMINI_API_KEY
    block_num = db.block_number_for_week(request.week_number)

    return RebuildInputs(
        plan_id=plan["id"],
        week=request.week_number,
        user=fresh_user,
        race_info=race_info,
        total_weeks=plan.get("total_weeks", 12),
        block_context=block_context,
        api_key=model_api_key,
        block_number=block_num,
    )


async def generate_week_draft(inputs: RebuildInputs, rng: RebuildRange) -> WeekDraft:
    workouts, resolved_tier = await PlanGenerator.generate_plan_workouts(
        inputs.plan_id,
        inputs.user,
        inputs.race_info,
        inputs.total_weeks,
        api_key=inputs.api_key,
        block_number=inputs.block_number,
        weeks_per_block=settings.WEEKS_PER_BLOCK,
        block_context=inputs.block_context,
        target_week=inputs.week,
    )
    return WeekDraft(workouts=filter_draft(workouts, rng), resolved_tier=resolved_tier)


def write_draft(plan: dict[str, Any], week: int, today: dt.date, draft: WeekDraft) -> None:
    """Scheduler adapt-week's direct write. The range is recomputed under row
    locks, so a workout completed or matched during generation is kept."""
    with db.engine.begin() as conn:
        rows = db.get_plan_workouts_for_placement(conn, plan["id"], lock=True)
        rng = rebuild_range(plan, rows, week, today)
        filtered = filter_draft(draft.workouts, rng)
        if not filtered:
            # Writing an empty draft would delete every replaceable workout.
            raise ValueError("Generated week was empty; nothing was changed.")
        db.replace_week_workouts(conn, plan["id"], rng.replaceable_ids, filtered)
    db.set_plan_athlete_tier(plan["id"], draft.resolved_tier)


REBUILD_TIMEOUT_SECONDS = 180


def _spawn_thread(factory: Callable[[], Coroutine[Any, Any, None]]) -> None:
    # Tool executors may run off the event loop thread, so the job gets its own
    # loop on a daemon thread. A restart kills it; the orphan rule
    # (db.expire_orphaned_rebuilds) turns the row `failed` on the next read.
    threading.Thread(target=lambda: asyncio.run(factory()), daemon=True, name="chat-rebuild").start()


spawn: Callable[[Callable[[], Coroutine[Any, Any, None]]], None] = _spawn_thread


async def _run_rebuild(proposal_id: int, inputs: RebuildInputs, rng: RebuildRange, rows: list[dict[str, Any]]) -> None:
    try:
        draft = await asyncio.wait_for(generate_week_draft(inputs, rng), REBUILD_TIMEOUT_SECONDS)
    except TimeoutError:
        db.fail_rebuild_proposal(proposal_id, "generation_timeout")
        return
    except Exception as ex:  # noqa: BLE001 -- any generator failure is a failed draft, never a crash
        print(f"[ChatRebuild][{proposal_id}] generation failed: {type(ex).__name__}")
        db.fail_rebuild_proposal(proposal_id, "generation_error")
        return
    if not draft.workouts:
        # Applying an empty draft would delete every replaceable workout.
        db.fail_rebuild_proposal(proposal_id, "generation_empty")
        return
    db.finish_rebuild_proposal(
        proposal_id,
        draft={"workouts": json_safe(draft.workouts), "resolved_tier": draft.resolved_tier},
        diff=build_diff(rows, rng, draft.workouts),
        warnings=rebuild_warnings(rows, rng, draft.workouts),
    )


def request_rebuild(
    *,
    user_id: int,
    thread_id: int,
    plan_id: int,
    today: dt.date,
    request: RebuildRequest,
    rationale: str,
) -> dict[str, Any]:
    """Chat path. Validates, records whole-week fingerprints NOW (a change
    during generation makes the draft stale), inserts the `generating` row and
    consumes one daily-cap slot in one transaction, then starts the job."""
    plan = calendar_ops.check_agent_access(user_id, plan_id)
    monday = start_monday(plan.get("start_date"))
    if monday is None:
        raise GuardViolation("G7_no_dates", {})
    week = request.week_number
    cur = current_week(monday, today)
    if week not in (cur, cur + 1):
        raise GuardViolation("G4_window", {"week": week, "current_week": cur})
    rows = load_plan_rows(plan_id)
    rng = rebuild_range(plan, rows, week, today)
    inputs = build_rebuild_inputs(user_id, plan, rows, rng, request)
    outcome, proposal_id = db.create_rebuild_proposal(
        user_id=user_id,
        thread_id=thread_id,
        plan_id=plan_id,
        week=week,
        operations={
            "week": week,
            "from_day": rng.from_day,
            "replaceable_ids": list(rng.replaceable_ids),
            "request": asdict(request),
        },
        fingerprints=week_fingerprints(rows, week),
        rationale=rationale,
        daily_limit=settings.COACH_CHAT_DAILY_REBUILDS_LIMIT,
        usage_date=calendar_ops.server_today(),
    )
    if outcome == "duplicate":
        raise GuardViolation("DUPLICATE_pending", {"proposal_id": proposal_id, "week": week})
    if outcome == "limit":
        raise GuardViolation("REBUILD_limit", {"limit": settings.COACH_CHAT_DAILY_REBUILDS_LIMIT})
    spawn(lambda: _run_rebuild(proposal_id, inputs, rng, rows))
    return {"proposal_id": proposal_id, "week": week, "from_day": rng.from_day}


def apply_rebuild(user_id: int, proposal: dict[str, Any], today: dt.date, conn) -> dict[str, Any]:
    """Apply a `proposed` rebuild inside the caller's transaction (proposal row
    already locked). Locks the plan's workouts, then refuses -- writing nothing --
    if the day rolled past the draft's first day or anything in the week changed."""
    plan = calendar_ops.check_agent_access(user_id, proposal["plan_id"])
    ops = proposal["operations"]
    rows = db.get_plan_workouts_for_placement(conn, plan["id"], lock=True)
    rng = rebuild_range(plan, rows, int(ops["week"]), today)
    if rng.from_day != ops["from_day"]:
        raise GuardViolation("STALE_rolled_over", {"week": rng.week, "from_day": ops["from_day"]})
    if week_fingerprints(rows, rng.week) != proposal["fingerprints"] or sorted(rng.replaceable_ids) != sorted(
        ops["replaceable_ids"]
    ):
        raise GuardViolation("STALE_changed", {})
    workouts = (proposal.get("draft") or {}).get("workouts") or []
    db.replace_week_workouts(conn, plan["id"], rng.replaceable_ids, workouts)
    return {"week": rng.week, "from_day": rng.from_day, "replaced": len(rng.replaceable_ids), "inserted": len(workouts)}
