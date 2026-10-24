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
        and (workout.get("type") or "").lower() != "rest"
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
    values += planning_candidates(context, now) + content_candidates(context, now) + coaching_candidates(context, now)
    return [c for c in values if c and c["due_at"] <= now < c["expires_at"]]


def instant(value):
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return value


def recent(context, kind, now, days):
    return any(
        e["kind"] == kind and e.get("claimed_at") and now - instant(e["claimed_at"]) < timedelta(days=days)
        for e in context["history"]
    )


def checklist_items(context):
    user = context["user"]
    sources = user.get("profile_field_sources") or user.get("field_sources") or {}
    if isinstance(sources, str):
        import json

        sources = json.loads(sources)

    def entered(key):
        source = (sources.get(key) or {}).get("source")
        return (
            bool(str(user.get(key) or "").strip())
            and source not in ("default", "estimate")
            and (user.get("onboarding_complete", True) or source is not None)
        )

    return [
        ("watch", any(c.get("status") == "active" for c in context.get("connections", []))),
        ("races", bool(context.get("race_claims"))),
        ("hr", entered("aet_hr") and entered("ant_hr")),
        ("pace", entered("zone2_pace_min") or bool(user.get("threshold_pace"))),
        ("injuries", bool(user.get("injury_history") or user.get("athlete_notes"))),
    ]


def select_card(context, words=None):
    import json

    opened = {
        o["card_id"] for o in context.get("opens", []) if o.get("lang") == context["preferences"].get("language", "en")
    }
    for card in sorted(context.get("cards", []), key=lambda c: c["id"]):
        if not card.get("notification_reviewed") or card["id"] in opened:
            continue
        tags = card.get("tags") or []
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except ValueError:
                tags = []
        text = " ".join([card.get("topic") or "", card.get("chapter_title") or "", *tags]).lower()
        if words is None or any(word in text for word in words):
            return card
    return None


def card_destination(card):
    return dict(kind="knowledge", card_id=card["id"], lang=card.get("lang", "en"), namespace="server")


def content_candidates(context, now):
    if not context["preferences"].get("coaching_enabled"):
        return []
    p = context["preferences"]
    day = now.astimezone(ZoneInfo(p["timezone"])).date()
    out = []
    snooze = instant(p.get("checklist_snoozed_until"))
    if not recent(context, "checklist", now, 14) and not (snooze and snooze > now):
        item = next((key for key, done in checklist_items(context) if not done), None)
        if item:
            out.append(
                candidate(
                    context, now, "checklist", str(day), dict(kind="checklist", item_id=item), 6, {"item_id": item}
                )
            )
    history = [e for e in context["history"] if e["kind"] == "knowledge" and e.get("claimed_at")]
    if sum(now - instant(e["claimed_at"]) < timedelta(days=7) for e in history) < 2:
        used = {
            e.get("source", {}).get("card_id") for e in history if now - instant(e["claimed_at"]) < timedelta(days=90)
        }
        # Topic relevance must exist; arbitrary daily content is intentionally excluded.
        dated = dated_workouts(context)
        phase = next(((w.get("phase") or "").lower() for w, d in dated if d >= day), "")
        words = ["taper"] if "taper" in phase else ["training", "aerobic", "recovery"]
        filtered = {**context, "cards": [c for c in context.get("cards", []) if c["id"] not in used]}
        card = select_card(filtered, words)
        if card:
            out.append(
                candidate(
                    context, now, "knowledge", f"{card['id']}:{day}", card_destination(card), 7, {"card_id": card["id"]}
                )
            )
    return out


def planning_candidates(context, now):
    plan = context.get("plan")
    p = context["preferences"]
    if not plan or not p.get("coaching_enabled"):
        return []
    today = now.astimezone(ZoneInfo(p["timezone"])).date()
    if today.weekday() != 6 or date.fromisoformat(str(plan["race_date"])[:10]) <= today:
        return []
    next_week = today + timedelta(days=1)
    if any(d >= next_week for _, d in dated_workouts(context)):
        return []
    if any(
        r["status"] == "generating" and now - instant(r["updated_at"]) < timedelta(minutes=30)
        for r in context.get("requests", [])
    ):
        return []
    return [
        candidate(
            context,
            now,
            "planning",
            f"{plan['id']}:{today}",
            dict(kind="plan", plan_id=plan["id"], intent="planning"),
            1,
        )
    ]


def coaching_candidates(context, now):
    plan = context.get("plan")
    p = context["preferences"]
    out = []
    if not plan or not p.get("coaching_enabled"):
        return out
    today = now.astimezone(ZoneInfo(p["timezone"])).date()
    dated = dated_workouts(context)
    missing = [
        (w, d)
        for w, d in dated
        if today - timedelta(days=7) <= d < today
        and actionable(w)
        and not is_done(w)
        and w.get("missed_origin") != "athlete"
    ]
    sync_failed = any(c.get("status") in ("error", "expired", "revoked") for c in context.get("connections", []))
    if (
        len(missing) >= 2
        and min(d for _, d in missing) <= today - timedelta(days=2)
        and not sync_failed
        and not recent(context, "unlogged", now, 7)
    ):
        out.append(
            candidate(
                context,
                now,
                "unlogged",
                f"{plan['id']}:{today}",
                dict(kind="review", plan_id=plan["id"], week_number=missing[-1][0]["week_number"]),
                2,
            )
        )
    for w, d in dated:
        completed = instant(w.get("first_completed_at"))
        running = (w.get("type") or "").lower() not in ("rest", "strength", "me", "hike", "muscular endurance")
        if (
            w.get("is_priority")
            and running
            and is_done(w)
            and completed
            and now - timedelta(hours=24) <= completed <= now
            and today - timedelta(days=1) <= d <= today
        ):
            event = candidate(
                context,
                now,
                "recovery",
                str(w["id"]),
                dict(kind="workout", plan_id=plan["id"], workout_id=w["id"]),
                5,
                {"workout_id": w["id"]},
            )
            if event:
                event["expires_at"] = min(event["expires_at"], completed + timedelta(hours=24))
                out.append(event)
    days_with_phase = {}
    for w, d in dated:
        days_with_phase[d] = days_with_phase.get(d, False) or "taper" in (w.get("phase") or "").lower()
    starts = []
    previous_taper = False
    for d, is_taper in sorted(days_with_phase.items()):
        if is_taper and not previous_taper:
            starts.append(d)
        previous_taper = is_taper
    card = select_card(context, ["taper"])
    for start in starts:
        if card and start <= today <= start + timedelta(days=1):
            out.append(
                candidate(
                    context, now, "taper", f"{plan['id']}:{start}", card_destination(card), 3, {"card_id": card["id"]}
                )
            )
    race = date.fromisoformat(str(plan["race_date"])[:10])
    days = (race - today).days
    card = select_card(context, ["race", "preparation", "thi đấu"])
    if card and plan.get("goal_type") in ("finish", "time", "optimal") and days in (7, 1):
        out.append(
            candidate(
                context, now, "race", f"{plan['id']}:{race}:{days}", card_destination(card), 0, {"card_id": card["id"]}
            )
        )
    return out
