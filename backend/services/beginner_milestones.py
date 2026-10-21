"""First 5K / First 10K milestone ladder for start_running plans.

Pure and deterministic: the LLM never decides whether a milestone is reached. The only impure
part is `refresh_milestones`, which reads DB state and records new achievements.
Spec: docs/superpowers/specs/2026-10-20-beginner-milestones-design.md
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any, Literal

from log_utils import get_logger
from services.coros_workouts import workout_kind

logger = get_logger(__name__)

Target = Literal["5k", "10k"]


@dataclass(frozen=True)
class Milestone:
    key: str
    kind: Literal["sessions", "jog_min", "distance_km"]
    threshold: float
    stage: Literal["A", "B"]
    typical_weeks: tuple[int, int]


LADDER: tuple[Milestone, ...] = (
    Milestone("first_session", "sessions", 1, "A", (1, 1)),
    Milestone("jog_5", "jog_min", 5, "A", (3, 5)),
    Milestone("jog_10", "jog_min", 10, "A", (4, 6)),
    Milestone("jog_20", "jog_min", 20, "A", (5, 8)),
    Milestone("jog_30", "jog_min", 30, "A", (7, 10)),
    Milestone("first_5k", "distance_km", 5, "A", (9, 12)),
    Milestone("jog_45", "jog_min", 45, "B", (13, 17)),
    Milestone("jog_60", "jog_min", 60, "B", (16, 21)),
    Milestone("first_10k", "distance_km", 10, "B", (18, 24)),
)

# English wording the plan prompt, week brief and coach use; clients own their own en/vi labels.
MILESTONE_PROMPT_LABELS = {
    "first_session": "your first run/walk session",
    "jog_5": "5 minutes of unbroken jogging",
    "jog_10": "10 minutes of unbroken jogging",
    "jog_20": "20 minutes of unbroken jogging",
    "jog_30": "30 minutes of non-stop running",
    "first_5k": "your first 5 km",
    "jog_45": "45 minutes of non-stop running",
    "jog_60": "60 minutes of non-stop running",
    "first_10k": "your first 10 km",
}

_DEFAULT_WEEKS = {"5k": 12, "10k": 22}
_BASE_MIN_WEEKS = {"5k": 9, "10k": 17}


@dataclass(frozen=True)
class NewAchievement:
    key: str
    achieved_at: datetime
    workout_id: int | None = None
    activity_id: int | None = None


def ladder_for(target: Target) -> tuple[Milestone, ...]:
    end = "first_5k" if target == "5k" else "first_10k"
    keys = [m.key for m in LADDER]
    return LADDER[: keys.index(end) + 1]


def baseline_keys(target: Target, current_jog_min: int | None) -> list[str]:
    """Jog milestones the athlete can already do, from the longest unbroken jog they report."""
    if not current_jog_min:
        return []
    return [m.key for m in ladder_for(target) if m.kind == "jog_min" and m.threshold <= current_jog_min]


def jog_credit_minutes(workout: dict[str, Any]) -> float | None:
    """Unbroken jog minutes a completed workout shows, or None for non-runs and distance-based reps."""
    if workout_kind(workout) != "run":
        return None
    if workout.get("walk_interval_value"):
        value, unit = workout.get("interval_rep_value"), (workout.get("interval_rep_unit") or "min").lower()
        if not value:
            return None
        if unit == "min":
            return float(value)
        if unit == "s":
            return float(value) / 60
        return None  # reps measured in m/km: we cannot tell how long the jog was
    return float(workout.get("duration_minutes") or 0) or None


def _as_date(v: Any) -> date:
    return v.date() if isinstance(v, datetime) else date.fromisoformat(str(v)[:10])


def evaluate(
    target: Target,
    plan_start: date,
    completed_workouts: list[dict[str, Any]],
    run_activities: list[dict[str, Any]],
    existing_keys: set[str],
    now: datetime | None = None,
) -> list[NewAchievement]:
    """Milestones newly earned. A key with any existing row (revoked included) is never emitted."""
    now = now or datetime.now(UTC)
    runs = sorted(
        (w for w in completed_workouts if workout_kind(w) == "run"),
        key=lambda w: (w.get("week_number") or 0, w.get("id") or 0),
    )
    acts = sorted(
        (a for a in run_activities if a.get("start_time") and _as_date(a["start_time"]) >= plan_start),
        key=lambda a: a["start_time"],
    )
    out: list[NewAchievement] = []
    for m in ladder_for(target):
        if m.key in existing_keys:
            continue
        if m.kind == "sessions" and runs:
            out.append(NewAchievement(m.key, now, workout_id=runs[0].get("id")))
        elif m.kind == "jog_min":
            hit = next((w for w in runs if (jog_credit_minutes(w) or 0) >= m.threshold), None)
            if hit:
                out.append(NewAchievement(m.key, now, workout_id=hit.get("id")))
        elif m.kind == "distance_km":
            hit = next((a for a in acts if (a.get("distance_km") or 0) >= m.threshold), None)
            if hit:
                start = hit["start_time"]
                at = start if isinstance(start, datetime) else now
                out.append(NewAchievement(m.key, at, activity_id=hit.get("id")))
    return out


def default_weeks(target: Target) -> int:
    return _DEFAULT_WEEKS[target]


def minimum_weeks(target: Target, current_jog_min: int | None) -> int:
    """Shortest sensible plan to the target. Shrinks with a baseline, by the weeks it skips past."""
    base = _BASE_MIN_WEEKS[target]
    done = set(baseline_keys(target, current_jog_min))
    if not done:
        return base
    first_open = next(m for m in ladder_for(target) if m.key not in done and m.kind != "sessions")
    return max(3, base - (first_open.typical_weeks[0] - 1))


def serialize(target: Target, has_event: bool, rows: list[dict[str, Any]]) -> dict[str, Any]:
    """The `beginner_milestones` object on the plan payload. Keys only: clients own the labels."""
    by_key = {r["milestone_key"]: r for r in rows}
    items = []
    for m in ladder_for(target):
        r = by_key.get(m.key)
        at = r["achieved_at"] if r and r.get("source") != "revoked" else None
        items.append(
            {
                "key": m.key,
                "kind": m.kind,
                "threshold": m.threshold,
                "stage": m.stage,
                "typical_weeks": list(m.typical_weeks),
                "achieved_at": at.isoformat() if at else None,
                "source": r["source"] if r else None,
            }
        )
    next_key = next((i["key"] for i in items if not i["achieved_at"]), None)
    return {"target": target, "has_event": bool(has_event), "items": items, "next_key": next_key}


def refresh_milestones(user_id: int) -> list[str]:
    """Re-evaluate the active beginner plan from DB state and record new achievements.

    Idempotent: every hook that can earn credit calls this and existing rows are never touched.
    A jog milestone also raises users.max_continuous_jog_min, which the beginner rules read.
    """
    import db

    plan = db.get_active_plan(user_id)
    if not plan or plan.get("goal_type") != "start_running" or not plan.get("milestone_target"):
        return []
    target: Target = plan["milestone_target"]
    start = plan.get("start_date")
    plan_start = date.fromisoformat(str(start)[:10]) if start else date.today()
    existing = {r["milestone_key"] for r in db.get_plan_milestone_rows(plan["id"])}
    found = evaluate(
        target,
        plan_start,
        db.get_completed_run_workouts(plan["id"]),
        db.get_run_activities_since(user_id, plan_start),
        existing,
    )
    new_keys: list[str] = []
    by_key = {m.key: m for m in LADDER}
    for a in found:
        if not db.insert_milestone_if_absent(
            plan["id"], a.key, "auto", a.achieved_at, activity_id=a.activity_id, workout_id=a.workout_id
        ):
            continue
        new_keys.append(a.key)
        if by_key[a.key].kind == "jog_min":
            db.set_max_continuous_jog_min(user_id, int(by_key[a.key].threshold))
    return new_keys


def safe_refresh_milestones(user_id: int) -> None:
    """The form every hook uses: a milestone problem must never fail the request it rides on."""
    try:
        refresh_milestones(user_id)
    except Exception:
        logger.warning("beginner milestone refresh failed", exc_info=True, extra={"fields": {"user_id": user_id}})


@dataclass(frozen=True)
class PlanShape:
    race_name: str
    race_date: str
    total_weeks: int
    has_event: bool
    warning: dict[str, Any] | None


def plan_shape(
    target: Target,
    start: date,
    today: date,
    current_jog_min: int | None,
    event_name: str | None,
    event_date: str | None,
) -> PlanShape:
    """Name, end date and length of a beginner plan. An event sets the end date; a too-soon one only warns."""
    label = f"First {target.upper()}"
    if not event_date:
        weeks = default_weeks(target)
        return PlanShape(label, (start + timedelta(weeks=weeks - 1)).isoformat(), weeks, False, None)
    event = date.fromisoformat(event_date)
    if event <= today:
        raise ValueError("event_date must be in the future")
    monday_start = start - timedelta(days=start.weekday())
    monday_event = event - timedelta(days=event.weekday())
    weeks = max(3, (monday_event - monday_start).days // 7 + 1)
    minimum = minimum_weeks(target, current_jog_min)
    warning = {"code": "event_too_soon", "minimum_weeks": minimum} if weeks < minimum else None
    return PlanShape(event_name or label, event_date, weeks, True, warning)


def apply_creation(user_id: int, plan_id: int, target: Target, current_jog_min: int | None) -> None:
    """Record what the athlete can already do: raise the jog ceiling and mark the baseline milestones."""
    import db

    if not current_jog_min:
        return
    db.set_max_continuous_jog_min(user_id, int(current_jog_min))
    now = datetime.now(UTC)
    for key in baseline_keys(target, current_jog_min):
        db.insert_milestone_if_absent(plan_id, key, "baseline", now)


def prompt_context(plan_id: int) -> dict[str, Any] | None:
    """The plan's serialized milestones plus its event, for prompts. None for plans without a target."""
    import db

    plan = db.get_plan_by_id(plan_id)
    if not plan or not plan.get("milestone_target"):
        return None
    ctx = serialize(plan["milestone_target"], bool(plan.get("has_target_event")), db.get_plan_milestone_rows(plan_id))
    ctx["event"] = {"name": plan.get("race_name"), "date": str(plan.get("race_date"))} if ctx["has_event"] else None
    return ctx


def goal_description(ctx: dict[str, Any] | None) -> str | None:
    """The plan prompt's goal line for a start_running plan with a target."""
    if not ctx:
        return None
    by_key = {m.key: m for m in LADDER}
    text = f"Goal: First {ctx['target'].upper()} — a beginner building from walk/run toward it."
    if ctx.get("event"):
        text += f" The athlete's event is '{ctx['event']['name']}' on {ctx['event']['date']}."
    if ctx.get("next_key"):
        lo, hi = by_key[ctx["next_key"]].typical_weeks
        text += (
            f" Next milestone: {MILESTONE_PROMPT_LABELS[ctx['next_key']]}, usually around weeks {lo}-{hi}."
            " Walk breaks are part of the plan."
        )
    text += " Do NOT assign high-intensity threshold or anaerobic intervals. Volume starts low and rises slowly."
    if ctx.get("event"):
        text += " Make the event week light with the event as its last session; run/walk is fine on the day. No taper block."
    return text


def stage_b_clause(ctx: dict[str, Any] | None) -> str | None:
    """Rules for a 10K-target beginner who can already run 30 minutes non-stop: run/walk is behind them."""
    if not ctx or ctx.get("target") != "10k":
        return None
    if not any(i["key"] == "jog_30" and i["achieved_at"] for i in ctx["items"]):
        return None
    from services.plan_lint import MAX_LONG_RUN_GROWTH

    return (
        "STAGE B — the athlete can run 30 minutes non-stop, so run/walk intervals are finished. Where rules 2-5 below "
        "describe run/walk intervals, STAGE B overrides them: write continuous easy runs. Keep one long run a week that grows gradually, by at most about "
        f"{MAX_LONG_RUN_GROWTH * 100:.0f}% over the longest run of the last two weeks, toward 60 minutes and then 10 km. "
        "Everything stays Zone 1-2: no tempo, threshold, intervals or hill sprints.\n"
    )


def safe_prompt_context(plan_id: int) -> dict[str, Any] | None:
    """prompt_context that degrades to None: plan generation must not fail on a milestone lookup."""
    try:
        return prompt_context(plan_id)
    except Exception:
        logger.warning(
            "beginner milestone prompt context failed", exc_info=True, extra={"fields": {"plan_id": plan_id}}
        )
        return None


def brief_fact(ctx: dict[str, Any] | None, max_jog_min: int | None) -> str | None:
    """One decision-log line for the week brief: where the athlete is on the ladder."""
    if not ctx:
        return None
    by_key = {m.key: m for m in LADDER}
    reached = sum(1 for i in ctx["items"] if i["achieved_at"])
    parts = []
    if ctx.get("next_key"):
        lo, hi = by_key[ctx["next_key"]].typical_weeks
        parts.append(f"next = {MILESTONE_PROMPT_LABELS[ctx['next_key']]} (usually around weeks {lo}-{hi})")
    if max_jog_min:
        parts.append(f"best unbroken jog so far = {max_jog_min} min")
    parts.append(f"{reached} of {len(ctx['items'])} reached")
    return "Milestone: " + "; ".join(parts)


def coach_context_block(ctx: dict[str, Any] | None) -> dict[str, Any] | None:
    """Compact milestone state for Coach Uphill chat."""
    if not ctx:
        return None
    return {
        "target": ctx["target"],
        "reached": [i["key"] for i in ctx["items"] if i["achieved_at"]],
        "next_key": ctx["next_key"],
        "event": ctx.get("event"),
    }


def just_reached(rows: list[dict[str, Any]], now: datetime, days: int = 7) -> list[str]:
    """Keys earned (auto or by hand, not from the onboarding baseline) in the last `days` days."""
    cutoff = now - timedelta(days=days)
    return [
        r["milestone_key"]
        for r in rows
        if r.get("source") in ("auto", "manual") and r.get("achieved_at") and r["achieved_at"] >= cutoff
    ]
