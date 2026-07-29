"""Kafka producer for the clickstream analytics pipeline -- publishes track_batch
events to Kafka; callers fall back to a direct Postgres write on failure. See
docs/superpowers/specs/2026-07-29-kafka-clickstream-design.md for the full design."""

import json
import logging
from typing import Any

from confluent_kafka import KafkaException, Producer

from config import settings

logger = logging.getLogger(__name__)

TOPIC = "clickstream-events"

_producer: Producer | None = None


def _get_producer() -> Producer:
    global _producer
    if _producer is None:
        _producer = Producer({"bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS})
    return _producer


def publish_batch(
    events: list[dict[str, Any]], user_id: int | None, session_id: str | None, timeout: float = 3.0
) -> bool:
    """Publish each event as a JSON message keyed by session_id. Returns True only
    if every event in the batch was delivered successfully within `timeout`
    seconds; returns False (never raises) on any failure so the caller can fall
    back to a direct Postgres write."""
    if not events:
        return True

    delivery_failed = False

    def _on_delivery(err, _msg):
        nonlocal delivery_failed
        if err is not None:
            delivery_failed = True
            logger.warning("Kafka delivery failed: %s", err)

    try:
        producer = _get_producer()
        for event in events:
            message = {
                "user_id": user_id,
                "session_id": session_id,
                "event_name": event.get("event_name"),
                "properties": event.get("properties", {}),
                "url": event.get("url"),
            }
            key = session_id.encode("utf-8") if session_id else None
            producer.produce(
                TOPIC,
                key=key,
                value=json.dumps(message).encode("utf-8"),
                callback=_on_delivery,
            )
        remaining = producer.flush(timeout=timeout)
    except (KafkaException, BufferError, TypeError) as exc:
        logger.warning("Kafka publish raised, falling back to Postgres: %s", exc)
        return False

    if remaining > 0:
        logger.warning("Kafka flush timed out with %d message(s) undelivered", remaining)
        return False

    return not delivery_failed
