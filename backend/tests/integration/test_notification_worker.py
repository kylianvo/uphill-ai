from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
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
