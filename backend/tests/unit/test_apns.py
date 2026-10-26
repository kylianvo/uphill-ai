import json

from services.apns import build_payload, classify_response


def test_response_classes():
    assert classify_response(200, None) == "accepted"
    assert classify_response(410, "Unregistered") == "invalid_token"
    assert classify_response(429, "TooManyRequests") == "retryable"
    assert classify_response(403, "InvalidProviderToken") == "configuration_error"
    assert classify_response(400, "BadDeviceToken") == "invalid_token"


def test_unicode_payload_preserves_route_and_limit():
    event = {"id": "abc", "destination": {"kind": "workout", "workout_id": 42}}
    payload = build_payload(event, "Buổi tập", "Chạy nhẹ 🏃" * 2000)
    assert len(json.dumps(payload, ensure_ascii=False).encode()) <= 4096
    assert payload["destination"]["workout_id"] == 42


def test_category_marks_mutable_kinds():
    from services.apns import build_payload

    def payload(kind):
        return build_payload(dict(id="x", kind=kind, destination={}), "t", "b")["aps"]["category"]

    assert payload("week_brief") == "coaching"
    assert payload("workout") == "plain"
    assert payload("plan_ready") == "plain"
