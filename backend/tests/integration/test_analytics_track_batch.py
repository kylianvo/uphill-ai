"""POST /api/analytics/track_batch writes events straight to Postgres -- requires live
Postgres (uphill_ai_test), see tests/integration/conftest.py."""

import pytest
from sqlalchemy import text

from db import engine


@pytest.mark.integration
def test_track_batch_writes_events_to_postgres(client, _init_test_database):
    resp = client.post(
        "/api/analytics/track_batch",
        json={
            "events": [{"event_name": "page_view", "properties": {"path": "/"}, "url": "/"}],
            "session_id": "test-session-direct",
        },
    )

    assert resp.status_code == 200
    assert resp.json() == {"status": "success", "recorded": 1}

    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT event_name, session_id FROM analytics_events WHERE session_id = :sid"),
            {"sid": "test-session-direct"},
        ).fetchone()

    assert row is not None
    assert row.event_name == "page_view"
