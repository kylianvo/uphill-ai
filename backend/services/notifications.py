"""Durable, opt-in notification worker. Delivery is off until explicitly configured."""

from datetime import UTC, datetime, timedelta

from prometheus_client import Counter, Gauge
from sqlalchemy import text

import db
from config import settings
from log_utils import get_logger
from services import apns
from services import notification_rules as rules
from services import notification_store as store
from services.notification_copy import render_notification

logger = get_logger(__name__)
LOCK_ID = 174620163
OUTCOMES = Counter("uphill_notification_outcomes_total", "Notification transport outcomes", ["outcome"])
HEARTBEAT = Gauge("uphill_notification_worker_last_tick_seconds", "Last successful notification worker tick")
PENDING_AGE = Gauge("uphill_notification_pending_age_seconds", "Age of oldest pending notification")


def load_context(user_id, now):
    plan = db.get_active_plan(user_id)
    with db.engine.connect() as conn:

        def rows(sql, params=None):
            return [dict(r) for r in conn.execute(text(sql), params or {"id": user_id}).mappings()]

        prefs = store.get_preferences(user_id)
        return dict(
            user=db.get_user_by_id(user_id),
            preferences=prefs,
            plan=plan,
            workouts=db.get_plan_workouts_with_match(plan["id"]) if plan else [],
            history=rows("SELECT * FROM notification_events WHERE user_id=:id"),
            cards=rows(
                "SELECT * FROM knowledge_cards WHERE notification_reviewed=true AND lang=:lang",
                {"lang": prefs["language"]},
            ),
            opens=rows("SELECT * FROM notification_knowledge_opens WHERE user_id=:id"),
            requests=rows("SELECT * FROM notification_generation_requests WHERE user_id=:id"),
            connections=rows("SELECT * FROM athlete_connections WHERE user_id=:id"),
            race_claims=rows("SELECT * FROM race_profile_claims WHERE user_id=:id"),
            checklist=[],
        )


def still_eligible(event, context, now):
    if event["kind"] == "plan_ready":
        return any(
            str(r["id"]) == event["source"].get("request_id") and r["status"] == "done" for r in context["requests"]
        )
    context = {**context, "history": [e for e in context["history"] if str(e.get("id")) != str(event["id"])]}
    return any(c["event_key"] == event["event_key"] for c in rules.candidates(context, now))


def run_once(now):
    if not settings.NOTIFICATION_WORKER_ENABLED or not settings.NOTIFICATION_DELIVERY_ENABLED:
        return 0
    allowed = {int(v) for v in settings.NOTIFICATION_ALLOWLIST.split(",") if v.strip().isdigit()}
    if not allowed:
        return 0
    sent = 0
    with db.engine.connect() as lock:
        if not lock.execute(text("SELECT pg_try_advisory_lock(:key)"), {"key": LOCK_ID}).scalar():
            return 0
        try:
            with db.engine.begin() as conn:
                conn.execute(
                    text(
                        "UPDATE notification_events SET status='unknown',result_code='worker_interrupted' WHERE status='sending'"
                    )
                )
                conn.execute(
                    text("UPDATE notification_events SET status='expired' WHERE status='pending' AND expires_at<=:now"),
                    {"now": now},
                )
                users = list(
                    conn.execute(
                        text("""SELECT user_id FROM notification_preferences WHERE next_evaluation_at<=:now AND user_id=ANY(:allowed)
                    AND (workouts_enabled OR coaching_enabled OR results_enabled) ORDER BY next_evaluation_at,user_id LIMIT 100"""),
                        {"now": now, "allowed": list(allowed)},
                    ).scalars()
                )
            for user_id in users:
                # Empty allowlist deliberately means no recipients during rollout.
                if user_id not in allowed:
                    continue
                context = load_context(user_id, now)
                choices = rules.candidates(context, now)
                with db.engine.begin() as conn:
                    pending = [
                        dict(r)
                        for r in conn.execute(
                            text(
                                "SELECT * FROM notification_events WHERE user_id=:id AND status='pending' AND due_at<=:now AND expires_at>:now"
                            ),
                            {"id": user_id, "now": now},
                        ).mappings()
                    ]
                    conn.execute(
                        text("UPDATE notification_preferences SET next_evaluation_at=:next WHERE user_id=:id"),
                        {"next": now + timedelta(minutes=1), "id": user_id},
                    )
                choices.extend(dict(e, priority=-1) for e in pending if still_eligible(e, context, now))
                for choice in sorted(choices, key=lambda c: (c["priority"], c["event_key"])):
                    event = store.claim_event(user_id, choice, now)
                    if not event:
                        continue
                    fresh = load_context(user_id, datetime.now(UTC))
                    with db.engine.connect() as conn:
                        device = (
                            conn.execute(
                                text("""SELECT * FROM notification_installations WHERE id=:id AND user_id=:user
                            AND registration_revision=:revision AND disabled_at IS NULL AND permission IN ('authorized','provisional')"""),
                                {
                                    "id": event["installation_id"],
                                    "user": user_id,
                                    "revision": event["registration_revision"],
                                },
                            )
                            .mappings()
                            .first()
                        )
                    p = fresh["preferences"]
                    category = (
                        "results_enabled"
                        if event["kind"] == "plan_ready"
                        else "workouts_enabled"
                        if event["kind"] == "workout"
                        else "coaching_enabled"
                    )
                    if (
                        not device
                        or not p[category]
                        or (p["paused_until"] and p["paused_until"] > now)
                        or not still_eligible(event, fresh, now)
                    ):
                        with db.engine.begin() as conn:
                            conn.execute(
                                text(
                                    "UPDATE notification_events SET status='suppressed',suppression_reason='state_changed' WHERE id=:id"
                                ),
                                {"id": event["id"]},
                            )
                        continue
                    title, body = render_notification(event, fresh)
                    result = apns.send_notification(dict(device), event, title, body)
                    store.record_delivery(str(event["id"]), result, now)
                    OUTCOMES.labels(outcome=result["outcome"]).inc()
                    if result["outcome"] == "configuration_error":
                        logger.error("Notification transport configuration failure")
                        return sent
                    sent += int(result["outcome"] == "accepted")
            store.prune_history(now)
            HEARTBEAT.set(now.timestamp())
            with db.engine.connect() as conn:
                oldest = conn.execute(
                    text("SELECT MIN(due_at) FROM notification_events WHERE status='pending'")
                ).scalar()
                PENDING_AGE.set(max(0, (now - oldest).total_seconds()) if oldest else 0)
            return sent
        finally:
            lock.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": LOCK_ID})


def run_worker(stop_event):
    while not stop_event.is_set():
        try:
            run_once(datetime.now(UTC))
        except Exception:
            # SQL/transport exceptions can contain sensitive values; omit exception text.
            logger.error("Notification worker tick failed")
        stop_event.wait(60)
