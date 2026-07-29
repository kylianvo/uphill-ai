"""Unit tests for kafka_producer_service -- all Kafka calls are mocked, no live
broker needed."""

from unittest.mock import MagicMock, patch

from confluent_kafka import KafkaException

from services import kafka_producer_service


def _reset_producer():
    kafka_producer_service._producer = None


def test_publish_batch_returns_true_when_all_delivered():
    _reset_producer()
    fake_producer = MagicMock()
    fake_producer.flush.return_value = 0

    def fake_produce(topic, key=None, value=None, callback=None):
        callback(None, MagicMock())

    fake_producer.produce.side_effect = fake_produce

    with patch("services.kafka_producer_service.Producer", return_value=fake_producer):
        result = kafka_producer_service.publish_batch(
            [{"event_name": "page_view", "properties": {}, "url": "/"}],
            user_id=1,
            session_id="sess-1",
        )

    assert result is True
    fake_producer.produce.assert_called_once()
    call = fake_producer.produce.call_args
    assert call.args[0] == "clickstream-events"
    assert call.kwargs["key"] == b"sess-1"


def test_publish_batch_returns_false_when_delivery_fails():
    _reset_producer()
    fake_producer = MagicMock()
    fake_producer.flush.return_value = 0

    def fake_produce(topic, key=None, value=None, callback=None):
        callback(Exception("broker down"), MagicMock())

    fake_producer.produce.side_effect = fake_produce

    with patch("services.kafka_producer_service.Producer", return_value=fake_producer):
        result = kafka_producer_service.publish_batch(
            [{"event_name": "page_view", "properties": {}, "url": "/"}],
            user_id=1,
            session_id="sess-1",
        )

    assert result is False
    fake_producer.purge.assert_called_once_with(in_queue=True, in_flight=True, blocking=True)


def test_publish_batch_returns_false_when_flush_times_out():
    _reset_producer()
    fake_producer = MagicMock()
    fake_producer.flush.return_value = 1

    with patch("services.kafka_producer_service.Producer", return_value=fake_producer):
        result = kafka_producer_service.publish_batch(
            [{"event_name": "page_view", "properties": {}, "url": "/"}],
            user_id=1,
            session_id="sess-1",
        )

    assert result is False
    fake_producer.purge.assert_called_once_with(in_queue=True, in_flight=True, blocking=True)


def test_publish_batch_purges_queue_when_produce_raises():
    _reset_producer()
    fake_producer = MagicMock()
    fake_producer.flush.return_value = 0
    fake_producer.produce.side_effect = BufferError("queue full")

    with patch("services.kafka_producer_service.Producer", return_value=fake_producer):
        result = kafka_producer_service.publish_batch(
            [{"event_name": "page_view", "properties": {}, "url": "/"}],
            user_id=1,
            session_id="sess-1",
        )

    assert result is False
    fake_producer.purge.assert_called_once_with(in_queue=True, in_flight=True, blocking=True)


def test_publish_batch_empty_list_returns_true():
    _reset_producer()
    result = kafka_producer_service.publish_batch([], user_id=1, session_id="sess-1")
    assert result is True


def test_publish_batch_returns_false_when_producer_construction_raises():
    _reset_producer()

    with patch(
        "services.kafka_producer_service.Producer",
        side_effect=KafkaException("connection refused"),
    ):
        result = kafka_producer_service.publish_batch(
            [{"event_name": "page_view", "properties": {}, "url": "/"}],
            user_id=1,
            session_id="sess-1",
        )

    assert result is False
