"""Integration tests for the Kafka publish/fallback wiring in
POST /api/analytics/track_batch -- requires live Postgres (uphill_ai_test), see
tests/integration/conftest.py for the client/_truncate_tables fixtures. Kafka
itself is mocked here (Task 1's producer already has its own unit tests) --
this file only proves the router wires success/failure to the right write path."""

from unittest.mock import patch

import pytest
from sqlalchemy import text

from db import engine


@pytest.mark.integration
def test_track_batch_falls_back_to_postgres_when_kafka_publish_fails(client, _init_test_database):
    unconfirmed = [{"event_name": "page_view", "properties": {"path": "/"}, "url": "/"}]
    with patch("routers.analytics.kafka_producer_service.publish_batch", return_value=unconfirmed):
        resp = client.post(
            "/api/analytics/track_batch",
            json={
                "events": [{"event_name": "page_view", "properties": {"path": "/"}, "url": "/"}],
                "session_id": "test-session-fallback",
            },
        )

    assert resp.status_code == 200
    assert resp.json() == {"status": "success", "recorded": 1}

    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT event_name, session_id FROM analytics_events WHERE session_id = :sid"),
            {"sid": "test-session-fallback"},
        ).fetchone()

    assert row is not None
    assert row.event_name == "page_view"


@pytest.mark.integration
def test_track_batch_skips_postgres_write_when_kafka_publish_succeeds(client, _init_test_database):
    with (
        patch("routers.analytics.kafka_producer_service.publish_batch", return_value=[]),
        patch("routers.analytics.AnalyticsService.track_events") as mock_track_events,
    ):
        resp = client.post(
            "/api/analytics/track_batch",
            json={
                "events": [{"event_name": "page_view", "properties": {}, "url": "/"}],
                "session_id": "test-session-success",
            },
        )

    assert resp.status_code == 200
    mock_track_events.assert_not_called()
