"""Integration test for kafka_consumer_worker -- requires both live Postgres
(uphill_ai_test, via tests/integration/conftest.py) AND a live local Kafka broker
(docker compose up -d kafka) reachable via KAFKA_BOOTSTRAP_SERVERS
(defaults to 127.0.0.1:9092 for a host-run pytest).

The three tests below `test_consumer_writes_produced_message_to_postgres` don't
need a live broker -- they exercise `process_message`/`run_consumer_loop`
directly against a fake Kafka message and/or a mocked consumer. They still live
in tests/integration/ (rather than tests/unit/) because this file's autouse
fixtures (`_init_test_database`/`_truncate_tables`, from
tests/integration/conftest.py) require live Postgres, and `kafka_consumer_worker`
writes to it via `AnalyticsService`.
"""

import json
import os
import uuid
from unittest.mock import MagicMock, patch

import pytest
from confluent_kafka import Consumer, Producer
from sqlalchemy import text

from db import engine
from kafka_consumer_worker import process_message, run_consumer_loop

BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "127.0.0.1:9092")
TOPIC = "clickstream-events"


@pytest.mark.integration
@pytest.mark.kafka
def test_consumer_writes_produced_message_to_postgres(_init_test_database, _truncate_tables):
    # A dedicated, uniquely-named topic per run -- not the shared `TOPIC` the
    # real app uses -- so a fresh consumer group with auto.offset.reset:
    # earliest always starts empty and reads back exactly the message this
    # test just produced. The real (long-lived, dev/prod-shared) topic
    # accumulates backlog across every local/CI run that has ever produced to
    # it; a new group there reads whatever's oldest first, not what this run
    # just sent, so this test previously failed nondeterministically once the
    # topic had any backlog at all. process_message/run_consumer_loop are
    # topic-agnostic (the topic name is only ever used for subscribe/produce,
    # never inspected by the code under test), so this doesn't change what's
    # being verified. Kafka auto-creates topics on first produce by default
    # (confirmed via this broker's config -- auto.create.topics.enable is
    # unset, which defaults to true).
    test_topic = f"clickstream-events-test-{uuid.uuid4()}"
    session_id = f"test-{uuid.uuid4()}"
    producer = Producer({"bootstrap.servers": BOOTSTRAP})
    message = {
        "user_id": None,
        "session_id": session_id,
        "event_name": "page_view",
        "properties": {"path": "/test"},
        "url": "/test",
    }
    producer.produce(test_topic, key=session_id.encode("utf-8"), value=json.dumps(message).encode("utf-8"))
    producer.flush(timeout=5.0)

    consumer = Consumer(
        {
            "bootstrap.servers": BOOTSTRAP,
            "group.id": f"test-consumer-{uuid.uuid4()}",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )
    consumer.subscribe([test_topic])
    try:
        run_consumer_loop(consumer, max_messages=1)
    finally:
        consumer.close()

    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT event_name, session_id FROM analytics_events WHERE session_id = :sid"),
            {"sid": session_id},
        ).fetchone()

    assert row is not None
    assert row.event_name == "page_view"


@pytest.mark.integration
def test_process_message_skips_malformed_json_without_raising(_init_test_database, _truncate_tables):
    process_message(b"not valid json")


@pytest.mark.integration
def test_process_message_skips_message_with_missing_event_name(_init_test_database, _truncate_tables):
    session_id = f"test-{uuid.uuid4()}"
    message = {
        "user_id": None,
        "session_id": session_id,
        "event_name": "",
        "properties": {},
        "url": "/test",
    }

    process_message(json.dumps(message).encode("utf-8"))

    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT event_name FROM analytics_events WHERE session_id = :sid"),
            {"sid": session_id},
        ).fetchone()

    assert row is None


@pytest.mark.integration
def test_run_consumer_loop_retries_same_message_on_db_failure_then_commits(_init_test_database, _truncate_tables):
    message = {
        "user_id": None,
        "session_id": "test-retry-session",
        "event_name": "page_view",
        "properties": {},
        "url": "/test",
    }
    fake_msg = MagicMock()
    fake_msg.error.return_value = None
    fake_msg.value.return_value = json.dumps(message).encode("utf-8")

    fake_consumer = MagicMock()
    fake_consumer.poll.return_value = fake_msg

    with (
        patch("kafka_consumer_worker.time.sleep") as mock_sleep,
        patch(
            "kafka_consumer_worker.AnalyticsService.save_events_from_kafka",
            side_effect=[Exception("db down"), None],
        ) as mock_save,
    ):
        processed = run_consumer_loop(fake_consumer, max_messages=1)

    assert processed == 1
    assert mock_save.call_count == 2
    mock_sleep.assert_called_once()
    fake_consumer.commit.assert_called_once_with(message=fake_msg)
