"""Notification persistence. Event inserts share the caller's result transaction."""

import json
from uuid import uuid4

from sqlalchemy import text

from db import engine

SCHEMA = """
CREATE TABLE IF NOT EXISTS notification_preferences (
 user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
 workouts_enabled BOOLEAN NOT NULL DEFAULT false, coaching_enabled BOOLEAN NOT NULL DEFAULT false,
 results_enabled BOOLEAN NOT NULL DEFAULT false, workout_time TEXT NOT NULL DEFAULT '07:00',
 coaching_time TEXT NOT NULL DEFAULT '18:00', quiet_start TEXT NOT NULL DEFAULT '21:00',
 quiet_end TEXT NOT NULL DEFAULT '07:00', timezone TEXT, language TEXT NOT NULL DEFAULT 'en',
 distance_unit TEXT NOT NULL DEFAULT 'km', paused_until TIMESTAMPTZ, checklist_snoozed_until TIMESTAMPTZ,
 last_proactive_at TIMESTAMPTZ, last_proactive_date DATE, result_date DATE, result_count INTEGER NOT NULL DEFAULT 0,
 next_evaluation_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS notification_installations (
 id UUID PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 token TEXT NOT NULL, environment TEXT NOT NULL CHECK (environment IN ('sandbox','production')),
 permission TEXT NOT NULL CHECK (permission IN ('authorized','provisional','denied','notDetermined')),
 last_active_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), disabled_at TIMESTAMPTZ,
 registration_revision INTEGER NOT NULL DEFAULT 1, UNIQUE(token,environment)
);
CREATE TABLE IF NOT EXISTS notification_events (
 id UUID PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 event_key TEXT NOT NULL, kind TEXT NOT NULL, destination JSONB NOT NULL, source JSONB NOT NULL DEFAULT '{}',
 due_at TIMESTAMPTZ NOT NULL, expires_at TIMESTAMPTZ NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('pending','sending','accepted','suppressed','expired','failed','unknown')),
 installation_id UUID REFERENCES notification_installations(id) ON DELETE SET NULL,
 registration_revision INTEGER, attempts INTEGER NOT NULL DEFAULT 0, claimed_at TIMESTAMPTZ,
 next_attempt_at TIMESTAMPTZ, accepted_at TIMESTAMPTZ, opened_at TIMESTAMPTZ,
 result_code TEXT, suppression_reason TEXT, UNIQUE(user_id,event_key)
);
CREATE INDEX IF NOT EXISTS notification_due ON notification_preferences(next_evaluation_at);
CREATE INDEX IF NOT EXISTS notification_pending ON notification_events(status,next_attempt_at);
CREATE INDEX IF NOT EXISTS notification_history ON notification_events(user_id,kind,claimed_at);
CREATE TABLE IF NOT EXISTS notification_knowledge_opens (
 user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, card_id INTEGER NOT NULL,
 lang TEXT NOT NULL, opened_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY(user_id,card_id,lang)
);
CREATE TABLE IF NOT EXISTS notification_generation_requests (
 id UUID PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 plan_id INTEGER NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
 coverage INTEGER, status TEXT NOT NULL CHECK(status IN ('generating','done','error')),
 updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), result JSONB
);
ALTER TABLE workouts ADD COLUMN IF NOT EXISTS missed_origin TEXT;
ALTER TABLE workouts ADD COLUMN IF NOT EXISTS first_completed_at TIMESTAMPTZ;
ALTER TABLE knowledge_cards ADD COLUMN IF NOT EXISTS notification_reviewed BOOLEAN NOT NULL DEFAULT false;
"""


def init_schema(conn):
    conn.execute(text(SCHEMA))


def get_preferences(user_id):
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO notification_preferences(user_id) VALUES(:id) ON CONFLICT DO NOTHING"), {"id": user_id}
        )
        return dict(
            conn.execute(text("SELECT * FROM notification_preferences WHERE user_id=:id"), {"id": user_id})
            .mappings()
            .one()
        )


PREFERENCE_FIELDS = frozenset(
    (
        "workouts_enabled",
        "coaching_enabled",
        "results_enabled",
        "workout_time",
        "coaching_time",
        "quiet_start",
        "quiet_end",
        "timezone",
        "language",
        "distance_unit",
        "paused_until",
        "checklist_snoozed_until",
    )
)


def update_preferences(user_id, values):
    get_preferences(user_id)
    if not set(values) <= PREFERENCE_FIELDS:
        raise ValueError("Unknown preference")
    if values:
        fields = ", ".join(f"{key}=:{key}" for key in values)
        with engine.begin() as conn:
            conn.execute(
                text(f"UPDATE notification_preferences SET {fields}, next_evaluation_at=NOW() WHERE user_id=:id"),
                {**values, "id": user_id},
            )
    return get_preferences(user_id)


def insert_event(conn, user_id, candidate):
    params = {
        **candidate,
        "id": str(uuid4()),
        "user_id": user_id,
        "destination": json.dumps(candidate["destination"]),
        "source": json.dumps(candidate.get("source", {})),
    }
    return str(
        conn.execute(
            text("""INSERT INTO notification_events
        (id,user_id,event_key,kind,destination,source,due_at,expires_at,status)
        VALUES(:id,:user_id,:event_key,:kind,CAST(:destination AS jsonb),CAST(:source AS jsonb),:due_at,:expires_at,'pending')
        ON CONFLICT(user_id,event_key) DO UPDATE SET event_key=EXCLUDED.event_key RETURNING id"""),
            params,
        ).scalar_one()
    )


def upsert_installation(user_id, installation_id, token, environment, permission, now):
    get_preferences(user_id)
    with engine.begin() as conn:
        # Serialize token rebinding as well as installation UUID rebinding.
        conn.execute(text("SELECT pg_advisory_xact_lock(hashtext(:token))"), {"token": token + environment})
        conn.execute(
            text("""UPDATE notification_events SET status='suppressed', suppression_reason='registration_changed'
            WHERE status IN ('pending','sending') AND installation_id IN
            (SELECT id FROM notification_installations WHERE id=:id OR (token=:token AND environment=:environment))"""),
            {"id": installation_id, "token": token, "environment": environment},
        )
        conn.execute(
            text("DELETE FROM notification_installations WHERE token=:token AND environment=:environment AND id<>:id"),
            {"token": token, "environment": environment, "id": installation_id},
        )
        row = conn.execute(
            text("""INSERT INTO notification_installations(id,user_id,token,environment,permission,last_active_at)
            VALUES(:id,:user_id,:token,:environment,:permission,:now) ON CONFLICT(id) DO UPDATE SET
            user_id=EXCLUDED.user_id,token=EXCLUDED.token,environment=EXCLUDED.environment,permission=EXCLUDED.permission,
            last_active_at=EXCLUDED.last_active_at,disabled_at=NULL,
            registration_revision=notification_installations.registration_revision+1 RETURNING id"""),
            dict(
                id=installation_id,
                user_id=user_id,
                token=token,
                environment=environment,
                permission=permission,
                now=now,
            ),
        ).scalar_one()
        conn.execute(
            text("UPDATE notification_preferences SET next_evaluation_at=:now WHERE user_id=:id"),
            {"now": now, "id": user_id},
        )
        return {"id": str(row)}


def remove_installation(user_id, installation_id):
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM notification_installations WHERE id=:id AND user_id=:user"),
            {"id": installation_id, "user": user_id},
        )


def claim_event(user_id, candidate, now):
    from datetime import timedelta
    from zoneinfo import ZoneInfo

    with engine.begin() as conn:
        p = (
            conn.execute(text("SELECT * FROM notification_preferences WHERE user_id=:id FOR UPDATE"), {"id": user_id})
            .mappings()
            .first()
        )
        if not p or not p["timezone"] or (p["paused_until"] and p["paused_until"] > now):
            return None
        category = (
            "results_enabled"
            if candidate["kind"] == "plan_ready"
            else "workouts_enabled"
            if candidate["kind"] == "workout"
            else "coaching_enabled"
        )
        if not p[category] or not candidate["due_at"] <= now < candidate["expires_at"]:
            return None
        device = (
            conn.execute(
                text("""SELECT * FROM notification_installations WHERE user_id=:id
            AND permission IN ('authorized','provisional') AND disabled_at IS NULL ORDER BY last_active_at DESC,id LIMIT 1"""),
                {"id": user_id},
            )
            .mappings()
            .first()
        )
        if not device:
            return None
        previous = (
            conn.execute(
                text("SELECT * FROM notification_events WHERE user_id=:id AND event_key=:key"),
                {"id": user_id, "key": candidate["event_key"]},
            )
            .mappings()
            .first()
        )
        if previous and (
            previous["status"] != "pending" or (previous["next_attempt_at"] and previous["next_attempt_at"] > now)
        ):
            return None
        today = now.astimezone(ZoneInfo(p["timezone"])).date()
        retry = previous and previous["claimed_at"] is not None
        if not retry:
            if category == "results_enabled":
                if p["result_date"] == today and p["result_count"] >= 3:
                    return None
                conn.execute(
                    text("""UPDATE notification_preferences SET result_count=CASE WHEN result_date=:day
                    THEN result_count+1 ELSE 1 END,result_date=:day WHERE user_id=:id"""),
                    {"day": today, "id": user_id},
                )
            else:
                if p["last_proactive_date"] == today or (
                    p["last_proactive_at"] and now - p["last_proactive_at"] < timedelta(hours=20)
                ):
                    return None
                conn.execute(
                    text(
                        "UPDATE notification_preferences SET last_proactive_at=:now,last_proactive_date=:day WHERE user_id=:id"
                    ),
                    {"now": now, "day": today, "id": user_id},
                )
        event_id = insert_event(conn, user_id, candidate)
        row = (
            conn.execute(
                text("""UPDATE notification_events SET status='sending',claimed_at=COALESCE(claimed_at,:now),
            installation_id=:installation,registration_revision=:revision,attempts=attempts+1,next_attempt_at=NULL
            WHERE id=:id RETURNING *"""),
                {"id": event_id, "now": now, "installation": device["id"], "revision": device["registration_revision"]},
            )
            .mappings()
            .one()
        )
        return {**dict(row), "installation": dict(device)}


def record_delivery(event_id, result, now):
    from datetime import timedelta

    with engine.begin() as conn:
        event = (
            conn.execute(text("SELECT * FROM notification_events WHERE id=:id FOR UPDATE"), {"id": event_id})
            .mappings()
            .one()
        )
        # A concurrent logout/rebinding may already have invalidated the claim.
        if event["status"] not in ("sending", "pending"):
            return
        outcome = result["outcome"]
        next_at = None
        status = {"accepted": "accepted", "unknown": "unknown"}.get(outcome, "failed")
        if outcome == "retryable" and event["attempts"] <= 3:
            next_at = now + timedelta(seconds=(60, 300, 900)[max(0, event["attempts"] - 1)])
            if next_at < event["expires_at"]:
                status = "pending"
            else:
                status = "expired"
                next_at = None
        conn.execute(
            text("""UPDATE notification_events SET status=:status,next_attempt_at=:next,
            accepted_at=CASE WHEN :status='accepted' THEN :now ELSE accepted_at END,result_code=:reason WHERE id=:id"""),
            dict(id=event_id, status=status, next=next_at, now=now, reason=(result.get("reason") or outcome)[:100]),
        )
        if outcome == "invalid_token":
            conn.execute(
                text("""UPDATE notification_installations SET disabled_at=:now WHERE id=:id
                AND registration_revision=:revision AND user_id=:user"""),
                dict(
                    now=now, id=event["installation_id"], revision=event["registration_revision"], user=event["user_id"]
                ),
            )
