"""Coach triage signals: deterministic rules that tell a coach who needs them
and why. Pure functions over facts the overview gathers in batched queries;
no LLM, no DB. Thresholds and codes come from
docs/superpowers/specs/2026-10-23-athletes-tab-coach-workbench-design.md."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from config import settings
from services import plan_lint

SEVERITIES = ("act_now", "review_build", "check_in", "highlight")
ALERT_PHASES = ("peak", "taper", "race")
HARD_RPE = 7  # "hard" and above on the 1-10 feel scale


@dataclass(frozen=True)
class Signal:
    code: str
    severity: str
    params: dict[str, Any]


@dataclass
class AthleteFacts:
    plan_type: str  # "review" | "coached"
    plan: dict[str, Any] | None  # active plan row
    draft_plan_id: int | None
    workouts: list[dict[str, Any]]  # active-plan workouts, each with "date" (and "actual_minutes" when matched)
    current_week: int
    pending_active_count: int
    last_activity_at: datetime | None
    hrv_last3: list[str | None]
    new_result: dict[str, Any] | None
    now: datetime


def _rest(w: dict[str, Any]) -> bool:
    return w.get("type") == "Rest"


def _key(w: dict[str, Any]) -> bool:
    return plan_lint.is_long(w) or plan_lint.is_quality(w)


def _minutes(w: dict[str, Any]) -> float:
    return float(w.get("duration_minutes") or 0)


def _done_minutes(w: dict[str, Any]) -> float:
    return float(w.get("actual_minutes") or _minutes(w)) if w.get("is_completed") else 0.0


def week_stats(workouts: list[dict[str, Any]], week: int) -> dict[str, int]:
    ws = [w for w in workouts if w["week_number"] == week and not _rest(w)]
    return {
        "sessions_planned": len(ws),
        "sessions_done": sum(1 for w in ws if w.get("is_completed")),
        "key_planned": sum(1 for w in ws if _key(w)),
        "key_done": sum(1 for w in ws if _key(w) and w.get("is_completed")),
        "minutes_planned": round(sum(_minutes(w) for w in ws)),
        "minutes_done": round(sum(_done_minutes(w) for w in ws)),
    }


def _recent(f: AthleteFacts, days: int = 7, back: int = 0) -> list[dict[str, Any]]:
    """Workouts dated in the `days`-day window ending `back` days before today."""
    end = f.now.date() - timedelta(days=back)
    return [w for w in f.workouts if end - timedelta(days=days - 1) <= w["date"] <= end]


def _phase(f: AthleteFacts, week: int) -> str | None:
    return next((w.get("phase") for w in f.workouts if w["week_number"] == week and w.get("phase")), None)


def _adherence(ws: list[dict[str, Any]]) -> float | None:
    resolved = [w for w in ws if w.get("is_completed") or w.get("is_missed")]
    return sum(1 for w in resolved if w.get("is_completed")) / len(resolved) if resolved else None


# --- rules, in spec table order ------------------------------------------------


def _reported(f: AthleteFacts) -> list[Signal]:
    out = []
    for reason in ("pain", "sick"):
        hit = [w for w in _recent(f) if w.get("is_missed") and w.get("missed_reason") == reason]
        if hit:
            out.append(
                Signal(f"reported_{reason}", "act_now", {"day": max(hit, key=lambda w: w["date"])["day_of_week"]})
            )
    return out


def _missed_many(f: AthleteFacts) -> list[Signal]:
    n = sum(1 for w in _recent(f) if w.get("is_missed"))
    return [Signal("missed_many", "act_now", {"count": n})] if n >= 3 else []


def _overload(f: AthleteFacts) -> list[Signal]:
    for week in (f.current_week, f.current_week - 1):
        st = week_stats(f.workouts, week)
        if st["minutes_planned"] >= 60 and st["minutes_done"] > 1.3 * st["minutes_planned"]:
            return [
                Signal("overload", "act_now", {"done_min": st["minutes_done"], "planned_min": st["minutes_planned"]})
            ]
    return []


def _generated_block(f: AthleteFacts) -> int:
    top = max((w["week_number"] for w in f.workouts), default=0)
    return (top - 1) // settings.WEEKS_PER_BLOCK + 1 if top else 0


def _plan_to_review(f: AthleteFacts) -> list[Signal]:
    p = f.plan
    if not p or p.get("created_by_user_id") != p.get("user_id"):
        return []
    block = _generated_block(f)
    if block <= (p.get("coach_reviewed_block") or 0):
        return []
    waiting = None
    if block == 1 and p.get("created_at"):
        waiting = int((f.now - p["created_at"]).total_seconds() // 3600)
    week = max(w["week_number"] for w in f.workouts)
    return [Signal("plan_to_review", "review_build", {"week": week, "waiting_hours": waiting})]


def _needs_plan(f: AthleteFacts) -> list[Signal]:
    if f.draft_plan_id is not None:
        return [Signal("draft_unpublished", "review_build", {})]
    if f.plan is None and f.plan_type == "coached":
        return [Signal("needs_plan", "review_build", {})]
    return []


def _next_block_due(f: AthleteFacts) -> list[Signal]:
    if not f.plan or not f.workouts:
        return []
    top = max(w["week_number"] for w in f.workouts)
    if top >= (f.plan.get("total_weeks") or 0):
        return []
    week_end = max(w["date"] for w in f.workouts if w["week_number"] == top)
    week_end += timedelta(days=6 - week_end.weekday())
    days = (week_end - f.now.date()).days
    return [Signal("next_block_due", "review_build", {"days": days})] if 0 <= days <= 7 else []


def _changes(f: AthleteFacts) -> list[Signal]:
    n = f.pending_active_count
    return [Signal("changes_to_approve", "review_build", {"count": n})] if n > 0 else []


def _no_sync(f: AthleteFacts) -> list[Signal]:
    if not f.plan or not f.plan.get("start_date"):
        return []
    if f.last_activity_at is not None:
        days = (f.now.date() - f.last_activity_at.date()).days
    else:
        days = (f.now.date() - date.fromisoformat(str(f.plan["start_date"])[:10])).days
    return [Signal("no_sync", "check_in", {"days": days})] if days >= 5 else []


def _missed_key(f: AthleteFacts) -> list[Signal]:
    hit = [w for w in _recent(f) if w.get("is_missed") and _key(w)]
    if not hit:
        return []
    w = max(hit, key=lambda w: w["date"])
    return [Signal("missed_key", "check_in", {"title": w.get("title"), "day": w["day_of_week"]})]


def _adherence_drop(f: AthleteFacts) -> list[Signal]:
    cur = _adherence(_recent(f, 14))
    if cur is None:
        return []
    prev = _adherence(_recent(f, 14, back=14))
    cur_pct, prev_pct = round(cur * 100), None if prev is None else round(prev * 100)
    if cur_pct < 60 or (prev_pct is not None and prev_pct - cur_pct >= 20):
        return [Signal("adherence_drop", "check_in", {"from_pct": prev_pct, "to_pct": cur_pct})]
    return []


def _hrv_low(f: AthleteFacts) -> list[Signal]:
    n = sum(1 for s in f.hrv_last3[:3] if s == "low")
    return [Signal("hrv_low", "check_in", {"days": n})] if n >= 2 else []


def _hard_easy(f: AthleteFacts) -> list[Signal]:
    n = sum(
        1
        for w in _recent(f)
        if w.get("is_completed") and not _rest(w) and not _key(w) and (w.get("rpe") or 0) >= HARD_RPE
    )
    return [Signal("hard_easy_days", "check_in", {"count": n})] if n >= 2 else []


def _race_soon(f: AthleteFacts) -> list[Signal]:
    if not f.plan or not f.plan.get("race_date"):
        return []
    days = (date.fromisoformat(str(f.plan["race_date"])[:10]) - f.now.date()).days
    return (
        [Signal("race_soon", "highlight", {"race": f.plan.get("race_name"), "days": days})] if 0 <= days <= 14 else []
    )


def _phase_start(f: AthleteFacts) -> list[Signal]:
    for week, when in ((f.current_week, "this_week"), (f.current_week + 1, "next_week")):
        ph = _phase(f, week)
        if ph in ALERT_PHASES and _phase(f, week - 1) != ph:
            return [Signal("phase_start", "highlight", {"phase": ph, "when": when})]
    return []


def _longest_long_run(f: AthleteFacts) -> list[Signal]:
    runs = [w for w in f.workouts if plan_lint.is_long(w) and w.get("is_completed")]
    if len(runs) < 2:
        return []
    best = max(runs, key=_done_minutes)
    recent = _recent(f)
    if not any(w is best for w in recent):
        return []
    return [Signal("longest_long_run", "highlight", {"minutes": round(_done_minutes(best))})]


def _block_done(f: AthleteFacts) -> list[Signal]:
    # A block is one week today, so "finished a block" means finished a phase.
    prev, cur = _phase(f, f.current_week - 1), _phase(f, f.current_week)
    return [Signal("block_done", "highlight", {"phase": prev})] if prev and cur and prev != cur else []


def _new_result(f: AthleteFacts) -> list[Signal]:
    r = f.new_result
    if not r:
        return []
    return [
        Signal("new_result", "highlight", {"race": r.get("race_name"), "finish_time_sec": r.get("finish_time_sec")})
    ]


RULES = (
    _reported,
    _missed_many,
    _overload,
    _plan_to_review,
    _needs_plan,
    _next_block_due,
    _changes,
    _no_sync,
    _missed_key,
    _adherence_drop,
    _hrv_low,
    _hard_easy,
    _race_soon,
    _phase_start,
    _longest_long_run,
    _block_done,
    _new_result,
)


def signals_for(f: AthleteFacts) -> list[Signal]:
    """Every firing signal, most severe first; ties keep rule order."""
    out = [s for rule in RULES for s in rule(f)]
    return sorted(out, key=lambda s: SEVERITIES.index(s.severity))


def status_of(signals: list[Signal]) -> str:
    return next((s.severity for s in signals if s.severity != "highlight"), "on_track")
