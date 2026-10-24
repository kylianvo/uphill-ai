from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, time, timedelta
from uuid import uuid4

from sqlalchemy import text

from db import engine


def test_concurrent_claims_reserve_one_daily_slot(auth_headers):
    from services.notification_store import claim_event, update_preferences, upsert_installation

    user = auth_headers["user_id"]
    now = datetime(2026, 10, 15, 20, tzinfo=UTC)
    update_preferences(user, {"timezone": "Australia/Sydney", "workouts_enabled": True})
    upsert_installation(user, str(uuid4()), "a" * 64, "sandbox", "authorized", now)

    def claim(n):
        return claim_event(
            user,
            dict(
                event_key=f"workout:{n}",
                kind="workout",
                destination={"kind": "workout"},
                due_at=now,
                expires_at=now + timedelta(hours=1),
            ),
            now,
        )

    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(claim, (1, 2)))
    assert sum(r is not None for r in results) == 1
    with engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM notification_events WHERE status='sending'")).scalar() == 1


def test_unknown_outcome_never_retries(auth_headers):
    from services.notification_store import insert_event, record_delivery

    now = datetime.now(UTC)
    with engine.begin() as conn:
        event_id = insert_event(
            conn,
            auth_headers["user_id"],
            dict(event_key="test", kind="workout", destination={}, due_at=now, expires_at=now + timedelta(hours=1)),
        )
    record_delivery(event_id, {"outcome": "unknown", "reason": "timeout"}, now)
    with engine.connect() as conn:
        row = conn.execute(text("SELECT * FROM notification_events WHERE id=:id"), {"id": event_id}).mappings().one()
        assert row["status"] == "unknown" and row["next_attempt_at"] is None


def test_refresh_same_registration_preserves_claim(auth_headers):
    from services.notification_store import claim_event, update_preferences, upsert_installation

    user = auth_headers["user_id"]
    now = datetime.now(UTC)
    install = str(uuid4())
    update_preferences(user, {"timezone": "UTC", "workouts_enabled": True})
    upsert_installation(user, install, "b" * 64, "sandbox", "authorized", now)
    event = claim_event(
        user,
        dict(event_key="same-device", kind="workout", destination={}, due_at=now, expires_at=now + timedelta(hours=1)),
        now,
    )
    upsert_installation(user, install, "b" * 64, "sandbox", "authorized", now + timedelta(seconds=1))
    with engine.connect() as conn:
        status = conn.execute(text("SELECT status FROM notification_events WHERE id=:id"), {"id": event["id"]}).scalar()
    assert status == "sending"


def test_plan_ready_respects_quiet_hours(auth_headers):
    from services.notification_store import claim_event, update_preferences, upsert_installation

    user = auth_headers["user_id"]
    now = datetime(2026, 10, 16, 22, tzinfo=UTC)
    update_preferences(user, {"timezone": "UTC", "results_enabled": True})
    upsert_installation(user, str(uuid4()), "c" * 64, "sandbox", "authorized", now)
    assert (
        claim_event(
            user,
            dict(
                event_key="quiet-result",
                kind="plan_ready",
                destination={},
                due_at=now,
                expires_at=now + timedelta(hours=24),
            ),
            now,
        )
        is None
    )


def test_worker_delivers_current_workout_once(auth_headers, monkeypatch):
    from config import settings
    from db import create_plan, save_workouts
    from services import notifications
    from services.notification_store import update_preferences, upsert_installation

    user = auth_headers["user_id"]
    # No activity history, so the reminder falls back to 07:00 in the athlete's zone (UTC here).
    now = datetime.combine(datetime.now(UTC).date(), time(7), UTC)
    monkeypatch.setattr(settings, "NOTIFICATION_WORKER_ENABLED", True)
    monkeypatch.setattr(settings, "NOTIFICATION_DELIVERY_ENABLED", True)
    monkeypatch.setattr(settings, "NOTIFICATION_ALLOWLIST", str(user))
    monkeypatch.setattr(notifications.apns, "send_notification", lambda *args: {"outcome": "accepted"})
    plan = create_plan(user, "Race", (now + timedelta(days=60)).date().isoformat(), "finish", None, 12)
    monday = now.date() - timedelta(days=now.weekday())
    with engine.begin() as conn:
        conn.execute(text("UPDATE plans SET start_date=:day WHERE id=:id"), {"day": monday.isoformat(), "id": plan})
    save_workouts(
        plan,
        [
            dict(
                week_number=1,
                day_of_week=now.strftime("%A"),
                phase="Base",
                title="Easy",
                type="Easy",
                duration_minutes=45,
                target_zone="Z2",
            )
        ],
    )
    update_preferences(
        user,
        {"timezone": "UTC", "workouts_enabled": True},
    )
    upsert_installation(user, str(uuid4()), "e" * 64, "sandbox", "authorized", now)
    assert notifications.run_once(now + timedelta(seconds=1)) == 1
    assert notifications.run_once(now + timedelta(minutes=1)) == 0


def test_one_failing_account_does_not_stop_the_tick(client, auth_headers, monkeypatch):
    from config import settings
    from services import notifications
    from services.notification_store import update_preferences

    user = auth_headers["user_id"]
    update_preferences(user, {"timezone": "UTC", "workouts_enabled": True})
    other = client.post("/api/auth/mock-login", json={"email": "other-notify@uphill.ai"}).json()["user"]["id"]
    update_preferences(other, {"timezone": "UTC", "workouts_enabled": True})
    monkeypatch.setattr(settings, "NOTIFICATION_WORKER_ENABLED", True)
    monkeypatch.setattr(settings, "NOTIFICATION_DELIVERY_ENABLED", True)
    monkeypatch.setattr(settings, "NOTIFICATION_ALLOWLIST", f"{user},{other}")
    seen = []

    def load_context(user_id, now):
        seen.append(user_id)
        raise RuntimeError("bad account data")

    monkeypatch.setattr(notifications, "load_context", load_context)
    notifications.run_once(datetime.now(UTC) + timedelta(seconds=1))
    assert sorted(seen) == sorted([user, other])
