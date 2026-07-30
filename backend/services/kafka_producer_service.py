"""Kafka producer for the clickstream analytics pipeline -- publishes track_batch
events to Kafka; callers fall back to a direct Postgres write for whichever events
did not confirm delivery. See docs/superpowers/specs/2026-07-29-kafka-clickstream-design.md
for the full design."""

import json
import logging
from functools import partial
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


def _safe_purge(producer: Producer) -> None:
    """purge() can itself raise; publish_batch must never raise regardless, so
    swallow it here rather than letting a purge failure escape as an unhandled
    exception."""
    try:
        producer.purge(in_queue=True, in_flight=True, blocking=True)
    except KafkaException as exc:
        logger.warning("Kafka purge raised (ignoring): %s", exc)


def publish_batch(
    events: list[dict[str, Any]], user_id: int | None, session_id: str | None, timeout: float = 3.0
) -> list[dict[str, Any]]:
    """Publish each event as a JSON message keyed by session_id. Returns the
    subset of `events` that did NOT confirm delivery within `timeout` seconds --
    an empty list means every event was delivered. Never raises: the caller
    should write only the returned events to Postgres directly, so a Kafka
    outage degrades to fallback for exactly the events that need it, and never
    for events that already succeeded.

    Any event whose delivery is still unconfirmed (explicit failure, or pending
    when the flush timeout is hit) is purged from the producer's internal queue
    so it can never be delivered later out-of-band -- e.g. after the broker
    recovers -- which would otherwise double-write it. This closes the
    broker-outage-then-recovery duplicate specifically; it is not a general
    exactly-once guarantee -- a message that the broker actually persisted but
    whose ack raced past `timeout` will still be written by both this fallback
    and the consumer. See the design doc's Non-goals / Error handling sections."""
    if not events:
        return []

    confirmed: set[int] = set()

    def _on_delivery(err, _msg, idx):
        if err is not None:
            logger.warning("Kafka delivery failed for event %d: %s", idx, err)
        else:
            confirmed.add(idx)

    producer = None
    try:
        producer = _get_producer()
        for idx, event in enumerate(events):
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
                callback=partial(_on_delivery, idx=idx),
            )
        producer.flush(timeout=timeout)
    except (KafkaException, BufferError, TypeError) as exc:
        logger.warning("Kafka publish raised, falling back to Postgres: %s", exc)
        if producer is not None:
            _safe_purge(producer)
        return events

    unconfirmed = [event for idx, event in enumerate(events) if idx not in confirmed]

    if unconfirmed:
        logger.warning(
            "Kafka publish incomplete (%d of %d unconfirmed), purging and falling back",
            len(unconfirmed),
            len(events),
        )
        _safe_purge(producer)

    return unconfirmed
