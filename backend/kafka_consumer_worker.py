"""Standalone long-running consumer for the clickstream Kafka topic -- run as its
own Docker Compose service (see docker-compose.yml's kafka-consumer service), not
part of the FastAPI process.

    python kafka_consumer_worker.py

See docs/superpowers/specs/2026-07-29-kafka-clickstream-design.md for the full design.
"""

import json
import logging
import time

from confluent_kafka import Consumer

from config import settings
from services.analytics_service import AnalyticsService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOPIC = "clickstream-events"


def process_message(raw_value: bytes) -> None:
    """Decode one Kafka message and write it to Postgres. Raises on a DB failure
    (so the caller retries without advancing); logs and swallows a decode
    failure (so one malformed message does not wedge the consumer)."""
    try:
        event = json.loads(raw_value.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        logger.warning("Skipping malformed Kafka message: %s", exc)
        return

    AnalyticsService.save_events_from_kafka(event)


def run_consumer_loop(consumer: Consumer, max_messages: int | None = None) -> int:
    """Poll loop: commits the offset only after a successful Postgres write. A DB
    failure is retried (with backoff) on the SAME message rather than skipped --
    `max_messages` stops the loop after N successfully processed messages, used
    by tests; production usage (see __main__ below) passes None to run forever."""
    processed = 0
    while max_messages is None or processed < max_messages:
        msg = consumer.poll(timeout=1.0)
        if msg is None:
            continue
        if msg.error():
            logger.warning("Kafka consumer error: %s", msg.error())
            continue

        while True:
            try:
                process_message(msg.value())
            except Exception as exc:
                logger.error("Failed to persist Kafka message, will retry: %s", exc)
                time.sleep(1.0)
                continue
            else:
                break

        consumer.commit(message=msg)
        processed += 1

    return processed


if __name__ == "__main__":
    consumer = Consumer(
        {
            "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "group.id": "clickstream-consumer",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )
    consumer.subscribe([TOPIC])
    logger.info("Kafka consumer started, subscribed to %s", TOPIC)
    try:
        run_consumer_loop(consumer, max_messages=None)
    finally:
        consumer.close()
