from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text

from db import engine


def test_preferences_default_off(auth_headers):
    from services.notification_store import get_preferences

    p = get_preferences(auth_headers["user_id"])
    assert not any(p[k] for k in ("workouts_enabled", "coaching_enabled", "results_enabled"))
    assert p["timezone"] is None


def test_event_deduplicates_and_obeys_transaction(auth_headers):
    from services.notification_store import insert_event

    now = datetime.now(UTC)
    candidate = dict(
        event_key="workout:1",
        kind="workout",
        destination={"kind": "workout"},
        source={},
        due_at=now,
        expires_at=now + timedelta(hours=1),
    )
    with engine.begin() as conn:
        first = insert_event(conn, auth_headers["user_id"], candidate)
        assert insert_event(conn, auth_headers["user_id"], candidate) == first
    with pytest.raises(RuntimeError):
        with engine.begin() as conn:
            insert_event(conn, auth_headers["user_id"], dict(candidate, event_key="rollback"))
            raise RuntimeError()
    with engine.connect() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM notification_events")).scalar() == 1
