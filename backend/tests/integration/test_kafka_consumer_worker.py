"""Integration test for kafka_consumer_worker -- requires both live Postgres
(uphill_ai_test, via tests/integration/conftest.py) AND a live local Kafka broker
(docker compose up -d kafka) reachable via KAFKA_BOOTSTRAP_SERVERS
(defaults to localhost:9092 for a host-run pytest)."""

import json
import os
import uuid

import pytest
from confluent_kafka import Consumer, Producer
from sqlalchemy import text

from db import engine
from kafka_consumer_worker import run_consumer_loop

BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC = "clickstream-events"


@pytest.mark.integration
@pytest.mark.kafka
def test_consumer_writes_produced_message_to_postgres(_init_test_database, _truncate_tables):
    session_id = f"test-{uuid.uuid4()}"
    producer = Producer({"bootstrap.servers": BOOTSTRAP})
    message = {
        "user_id": None,
        "session_id": session_id,
        "event_name": "page_view",
        "properties": {"path": "/test"},
        "url": "/test",
    }
    producer.produce(TOPIC, key=session_id.encode("utf-8"), value=json.dumps(message).encode("utf-8"))
    producer.flush(timeout=5.0)

    consumer = Consumer(
        {
            "bootstrap.servers": BOOTSTRAP,
            "group.id": f"test-consumer-{uuid.uuid4()}",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )
    consumer.subscribe([TOPIC])
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
