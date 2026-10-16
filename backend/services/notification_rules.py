"""Pure notification selection. All dates are athlete-local; all instants are aware."""

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from services.workout_calendar import plan_start_monday, workout_date


def is_done(workout):
    matched = workout.get("matched_activity_id") is not None or (workout.get("matched_distance_km") or 0) > 0
    return workout.get("is_completed") == 1 or (workout.get("is_completed") != 0 and matched)


def local_due(day, wall_time, timezone):
    zone = ZoneInfo(timezone)
    wall = datetime.combine(day, wall_time)
    # At a DST gap, advance to the first valid local minute, not by the size of the gap.
    for _ in range(24 * 60 + 1):
        valid = []
        for fold in (0, 1):
            instant = wall.replace(tzinfo=zone, fold=fold).astimezone(UTC)
            if instant.astimezone(zone).replace(tzinfo=None) == wall:
                valid.append(instant)
        if valid:
            return min(valid)
        wall += timedelta(minutes=1)
    raise ValueError("Local calendar date is unavailable")


def delivery_window(due, prefs, expires_at):
    zone = ZoneInfo(prefs["timezone"])
    local = due.astimezone(zone)
    start, end = (time.fromisoformat(prefs[k]) for k in ("quiet_start", "quiet_end"))
    wall = local.time().replace(tzinfo=None)
    quiet = start <= wall < end if start < end else wall >= start or wall < end
    if quiet:
        day = local.date() + timedelta(days=int(start > end and wall >= start))
        due = local_due(day, end, prefs["timezone"])
    expiry = min(due + timedelta(hours=1), expires_at)
    return (due, expiry) if due < expiry else None


def dated_workouts(context):
    plan = context.get("plan")
    if not plan or not context.get("workouts"):
        return []
    try:
        race = date.fromisoformat(str(plan["race_date"])[:10])
        monday = plan_start_monday(plan.get("start_date"), context["workouts"], race)
        return [(w, workout_date(monday, w["week_number"], w["day_of_week"])) for w in context["workouts"]]
    except (ValueError, KeyError, TypeError):
        return []


def actionable(workout):
    return (
        bool(workout.get("approved_at"))
        and workout.get("type", "").lower() != "rest"
        and (workout.get("duration_minutes") or 0) > 0
    )


def candidate(context, now, kind, key, destination, priority, source=None):
    p = context["preferences"]
    today = now.astimezone(ZoneInfo(p["timezone"])).date()
    workouts_today = any(
        day == today and actionable(w) and not is_done(w) and not w.get("is_missed")
        for w, day in dated_workouts(context)
    )
    due = local_due(today, time.fromisoformat(p["workout_time" if workouts_today else "coaching_time"]), p["timezone"])
    tomorrow = local_due(today + timedelta(days=1), time.min, p["timezone"])
    window = delivery_window(due, p, tomorrow)
    if not window:
        return None
    return dict(
        event_key=f"{kind}:{key}",
        kind=kind,
        destination=destination,
        priority=priority,
        source=source or {},
        due_at=window[0],
        expires_at=window[1],
    )


def workout_candidate(context, now):
    if not context["preferences"].get("workouts_enabled"):
        return None
    today = now.astimezone(ZoneInfo(context["preferences"]["timezone"])).date()
    rows = [
        w
        for w, d in dated_workouts(context)
        if d == today and actionable(w) and not is_done(w) and not w.get("is_missed")
    ]
    if not rows:
        return None
    w = min(rows, key=lambda w: (not w.get("is_priority"), str(w.get("session_slot") or "AM"), w["id"]))
    return candidate(
        context,
        now,
        "workout",
        f"{w['id']}:{today}",
        dict(kind="workout", plan_id=context["plan"]["id"], workout_id=w["id"]),
        4,
        {"workout_id": w["id"]},
    )


def choose_candidate(values, now):
    eligible = [c for c in values if c and c["due_at"] <= now < c["expires_at"]]
    return min(eligible, key=lambda c: (c["priority"], c["event_key"]), default=None)


def candidates(context, now):
    p = context["preferences"]
    if not p.get("timezone") or (p.get("paused_until") and p["paused_until"] > now):
        return []
    values = [workout_candidate(context, now)]
    return [c for c in values if c and c["due_at"] <= now < c["expires_at"]]
