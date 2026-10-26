"""Direct APNs alert transport. Never log tokens, keys, or payloads."""

import hashlib
import json
import time
from pathlib import Path

import httpx
import jwt

from config import settings
from services.notification_store import MUTABLE_KINDS

_cached_token = None
_token_time = 0


def classify_response(status, reason):
    if status == 200:
        return "accepted"
    if status == 410 or reason in ("BadDeviceToken", "DeviceTokenNotForTopic"):
        return "invalid_token"
    if status in (429, 500, 503):
        return "retryable"
    if status == 403 or reason in ("MissingTopic", "BadTopic", "TopicDisallowed"):
        return "configuration_error"
    return "permanent_failure"


def build_payload(event, title, body):
    payload = {
        # "coaching" shows the app's "Less like this" action; workout and plan_ready don't get it.
        "aps": {
            "alert": {"title": title[:100], "body": body},
            "sound": "default",
            "category": "coaching" if event.get("kind") in MUTABLE_KINDS else "plain",
        },
        "v": 1,
        "notification_id": str(event["id"]),
        "destination": event["destination"],
    }
    while len(json.dumps(payload, ensure_ascii=False).encode()) > 4096:
        value = payload["aps"]["alert"]["body"]
        if not value:
            raise ValueError("Notification destination exceeds payload limit")
        payload["aps"]["alert"]["body"] = value[:-100]
    return payload


def provider_token():
    global _cached_token, _token_time
    now = time.time()
    if _cached_token is None or now - _token_time >= 3000:
        _cached_token = jwt.encode(
            {"iss": settings.APNS_TEAM_ID, "iat": int(now)},
            Path(settings.APNS_PRIVATE_KEY_PATH).read_text(),
            algorithm="ES256",
            headers={"kid": settings.APNS_KEY_ID},
        )
        _token_time = now
    return _cached_token


def send_notification(installation, event, title, body):
    if not all((settings.APNS_KEY_ID, settings.APNS_TEAM_ID, settings.APNS_PRIVATE_KEY_PATH, settings.APNS_TOPIC)):
        return {"outcome": "configuration_error", "reason": "missing_credentials"}
    host = {"sandbox": "api.sandbox.push.apple.com", "production": "api.push.apple.com"}.get(
        installation["environment"]
    )
    if not host:
        return {"outcome": "permanent_failure", "reason": "invalid_environment"}
    try:
        headers = {
            "authorization": f"bearer {provider_token()}",
            "apns-topic": settings.APNS_TOPIC,
            "apns-push-type": "alert",
            "apns-priority": "10",
            "apns-id": str(event["id"]),
            "apns-expiration": str(int(event["expires_at"].timestamp())),
            "apns-collapse-id": hashlib.sha256(event["event_key"].encode()).hexdigest(),
        }
        payload = build_payload(event, title, body)
    except (OSError, ValueError, jwt.PyJWTError):
        return {"outcome": "configuration_error", "reason": "invalid_credentials_or_payload"}
    try:
        with httpx.Client(http2=True, timeout=10) as client:
            response = client.post(
                f'https://{host}/3/device/{installation["token"]}',
                headers=headers,
                content=json.dumps(payload, ensure_ascii=False).encode(),
            )
        try:
            reason = response.json().get("reason") if response.content else None
        except (ValueError, AttributeError):
            reason = None
        return {
            "outcome": classify_response(response.status_code, reason),
            "reason": reason,
            "apns_id": response.headers.get("apns-id"),
        }
    except httpx.TransportError:
        # Acceptance may have happened before the connection failed. Do not retry.
        return {"outcome": "unknown", "reason": "transport_uncertain"}
