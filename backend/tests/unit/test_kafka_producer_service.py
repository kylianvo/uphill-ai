"""Unit tests for kafka_producer_service -- all Kafka calls are mocked, no live
broker needed."""

from unittest.mock import MagicMock, patch

from confluent_kafka import KafkaException

from services import kafka_producer_service


def _reset_producer():
    kafka_producer_service._producer = None


def test_publish_batch_returns_empty_list_when_all_delivered():
    _reset_producer()
    fake_producer = MagicMock()
    fake_producer.flush.return_value = 0

    def fake_produce(topic, key=None, value=None, callback=None):
        callback(None, MagicMock())

    fake_producer.produce.side_effect = fake_produce

    events = [{"event_name": "page_view", "properties": {}, "url": "/"}]
    with patch("services.kafka_producer_service.Producer", return_value=fake_producer):
        result = kafka_producer_service.publish_batch(events, user_id=1, session_id="sess-1")

    assert result == []
    fake_producer.produce.assert_called_once()
    call = fake_producer.produce.call_args
    assert call.args[0] == "clickstream-events"
    assert call.kwargs["key"] == b"sess-1"
    fake_producer.purge.assert_not_called()


def test_publish_batch_returns_all_events_when_delivery_fails():
    _reset_producer()
    fake_producer = MagicMock()
    fake_producer.flush.return_value = 0

    def fake_produce(topic, key=None, value=None, callback=None):
        callback(Exception("broker down"), MagicMock())

    fake_producer.produce.side_effect = fake_produce

    events = [{"event_name": "page_view", "properties": {}, "url": "/"}]
    with patch("services.kafka_producer_service.Producer", return_value=fake_producer):
        result = kafka_producer_service.publish_batch(events, user_id=1, session_id="sess-1")

    assert result == events
    fake_producer.purge.assert_called_once_with(in_queue=True, in_flight=True, blocking=True)


def test_publish_batch_returns_all_events_when_flush_times_out():
    _reset_producer()
    fake_producer = MagicMock()
    fake_producer.flush.return_value = 1

    events = [{"event_name": "page_view", "properties": {}, "url": "/"}]
    with patch("services.kafka_producer_service.Producer", return_value=fake_producer):
        result = kafka_producer_service.publish_batch(events, user_id=1, session_id="sess-1")

    assert result == events
    fake_producer.purge.assert_called_once_with(in_queue=True, in_flight=True, blocking=True)


def test_publish_batch_purges_queue_when_produce_raises():
    _reset_producer()
    fake_producer = MagicMock()
    fake_producer.flush.return_value = 0
    fake_producer.produce.side_effect = BufferError("queue full")

    events = [{"event_name": "page_view", "properties": {}, "url": "/"}]
    with patch("services.kafka_producer_service.Producer", return_value=fake_producer):
        result = kafka_producer_service.publish_batch(events, user_id=1, session_id="sess-1")

    assert result == events
    fake_producer.purge.assert_called_once_with(in_queue=True, in_flight=True, blocking=True)


def test_publish_batch_returns_only_unconfirmed_event_on_partial_failure():
    """Regression test: a 2-event batch where only one event fails delivery must
    return ONLY that event, not the whole batch -- otherwise the caller's
    Postgres fallback double-writes the event that already succeeded."""
    _reset_producer()
    fake_producer = MagicMock()
    fake_producer.flush.return_value = 0

    callbacks = []

    def fake_produce(topic, key=None, value=None, callback=None):
        callbacks.append(callback)

    fake_producer.produce.side_effect = fake_produce

    events = [
        {"event_name": "page_view", "properties": {}, "url": "/one"},
        {"event_name": "page_view", "properties": {}, "url": "/two"},
    ]

    def fake_flush(timeout=None):
        # Trigger delivery callbacks here, mirroring librdkafka firing them
        # during flush(): event 0 succeeds, event 1 fails.
        callbacks[0](None, MagicMock())
        callbacks[1](Exception("broker down"), MagicMock())
        return 0

    fake_producer.flush.side_effect = fake_flush

    with patch("services.kafka_producer_service.Producer", return_value=fake_producer):
        result = kafka_producer_service.publish_batch(events, user_id=1, session_id="sess-1")

    assert result == [events[1]]
    fake_producer.purge.assert_called_once_with(in_queue=True, in_flight=True, blocking=True)


def test_publish_batch_empty_list_returns_empty_list():
    _reset_producer()
    result = kafka_producer_service.publish_batch([], user_id=1, session_id="sess-1")
    assert result == []


def test_publish_batch_returns_all_events_when_producer_construction_raises():
    _reset_producer()
    events = [{"event_name": "page_view", "properties": {}, "url": "/"}]

    with patch(
        "services.kafka_producer_service.Producer",
        side_effect=KafkaException("connection refused"),
    ):
        result = kafka_producer_service.publish_batch(events, user_id=1, session_id="sess-1")

    assert result == events


def test_publish_batch_swallows_purge_failure():
    """purge() itself can raise -- publish_batch must still never raise."""
    _reset_producer()
    fake_producer = MagicMock()
    fake_producer.flush.return_value = 1
    fake_producer.purge.side_effect = KafkaException("purge failed")

    events = [{"event_name": "page_view", "properties": {}, "url": "/"}]
    with patch("services.kafka_producer_service.Producer", return_value=fake_producer):
        result = kafka_producer_service.publish_batch(events, user_id=1, session_id="sess-1")

    assert result == events
