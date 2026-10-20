"""Week-to-date context for a synced session: how much of the week is done and what the
next key session is. Computed on read, so it is never stale after a later sync, and sent
as numbers so the frontend words it in the athlete's language."""

from typing import Any

import db
from services.calendar_rules import DAYS, _is_hard, _is_long_run
from services.plan_rules import is_me_session


def _is_key(w: dict[str, Any]) -> bool:
    return _is_long_run(w) or _is_hard(w) or is_me_session(w)


def week_context(week_workouts: list[dict[str, Any]], workout: dict[str, Any]) -> dict[str, Any]:
    """{done_min, planned_min, next_key} for the week `workout` belongs to. done_min is the
    planned time of sessions ticked complete (matches the checkbox view and counts watch-less
    sessions); next_key is the next unfinished key session from this one onward, or None."""
    active = [w for w in week_workouts if w.get("type") != "Rest"]
    planned = sum(w.get("duration_minutes") or 0 for w in active)
    done = sum(w.get("duration_minutes") or 0 for w in active if w.get("is_completed") == 1)
    day = DAYS.index(workout["day_of_week"]) if workout.get("day_of_week") in DAYS else 0
    upcoming = sorted(
        (
            w
            for w in active
            if w.get("id") != workout.get("id")
            and w.get("is_completed") != 1
            and w.get("is_missed") != 1
            and w.get("day_of_week") in DAYS
            and DAYS.index(w["day_of_week"]) >= day
            and _is_key(w)
        ),
        key=lambda w: (DAYS.index(w["day_of_week"]), w.get("id") or 0),
    )
    nxt = upcoming[0] if upcoming else None
    return {
        "done_min": round(done),
        "planned_min": round(planned),
        "next_key": {"day_of_week": nxt["day_of_week"], "title": nxt.get("title"), "type": nxt.get("type")}
        if nxt
        else None,
    }


def attach_week_context(activities: list[dict[str, Any]]) -> None:
    """Adds `week_context` in place to every activity matched to a workout."""
    ids = sorted({a["workout_id"] for a in activities if a.get("workout_id")})
    if not ids:
        return
    from sqlalchemy import text

    with db.engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, plan_id, week_number, day_of_week FROM workouts WHERE id = ANY(:ids)"), {"ids": ids}
        ).fetchall()
    meta = {r.id: r for r in rows}
    plans: dict[int, list[dict[str, Any]]] = {}
    for a in activities:
        m = meta.get(a.get("workout_id"))
        if not m:
            continue
        if m.plan_id not in plans:
            plans[m.plan_id] = db.get_plan_workouts(m.plan_id)
        week = [w for w in plans[m.plan_id] if w["week_number"] == m.week_number]
        a["week_context"] = week_context(week, {"id": m.id, "day_of_week": m.day_of_week})
