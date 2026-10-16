from datetime import UTC, datetime, timedelta

from sqlalchemy import text

from db import engine


def test_pruning_preserves_deduplication(auth_headers):
    from services.notification_store import insert_event, prune_history

    now = datetime.now(UTC)
    c = dict(
        event_key="old",
        kind="recovery",
        destination={"kind": "workout", "workout_id": 1},
        source={"workout_id": 1},
        due_at=now - timedelta(days=92),
        expires_at=now - timedelta(days=91),
    )
    with engine.begin() as conn:
        event = insert_event(conn, auth_headers["user_id"], c)
        conn.execute(text("UPDATE notification_events SET status='accepted' WHERE id=:id"), {"id": event})
    prune_history(now)
    with engine.begin() as conn:
        assert insert_event(conn, auth_headers["user_id"], c) == event
        r = conn.execute(text("SELECT * FROM notification_events WHERE id=:id"), {"id": event}).mappings().one()
        assert r["status"] == "accepted" and r["destination"] == {}
