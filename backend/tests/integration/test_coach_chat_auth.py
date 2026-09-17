"""Security tests for POST /api/coach/chat.

The endpoint used to be unauthenticated and took the athlete's identity
(`user_profile.id`), Gemini key and plan context from the request body -- so
anyone could POST another athlete's id and have that athlete's last 14 days of
watch activities, heart rate and quality grades injected into the reply.
Identity, key and plan must now come from the session user only.
"""

from datetime import UTC, datetime, timedelta

import pytest

import db
from config import settings
from services.providers.base import CanonicalActivity


@pytest.fixture(autouse=True)
def _server_gemini_key(monkeypatch):
    # With no key at all the handler skips Gemini, so no prompt is ever
    # assembled and the prompt assertions below would pass vacuously.
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "server-key")


def _system_prompt(fake_client) -> str:
    return fake_client.models.generate_content.call_args.kwargs["config"].system_instruction


def _add_recent_activity(user_id: int, external_id: str, distance_km: float) -> None:
    db.upsert_activity(
        user_id,
        CanonicalActivity(
            external_id=external_id,
            provider="coros",
            activity_type="outdoor_run",
            start_time=datetime.now(UTC) - timedelta(days=2),
            duration_seconds=3600.0,
            distance_km=distance_km,
        ),
    )


def test_unauthenticated_chat_is_rejected(client, mock_gemini):
    resp = client.post("/api/coach/chat", json={"messages": [{"role": "user", "content": "hi"}]})

    assert resp.status_code == 401


def test_body_user_id_cannot_pull_another_athletes_activities(client, auth_headers, mock_gemini):
    _, fake_client = mock_gemini
    victim = client.post("/api/auth/mock-login", json={"email": "victim@uphill.ai"}).json()["user"]
    _add_recent_activity(victim["id"], "victim-run", 37.3)
    _add_recent_activity(auth_headers["user_id"], "my-run", 12.6)

    resp = client.post(
        "/api/coach/chat",
        headers=auth_headers["headers"],
        json={
            "messages": [{"role": "user", "content": "How did my week go?"}],
            "user_profile": {"id": victim["id"]},
        },
    )

    assert resp.status_code == 200
    prompt = _system_prompt(fake_client)
    assert "37.3km" not in prompt
    assert "12.6km" in prompt


def test_stored_gemini_key_is_used_and_body_key_is_ignored(client, auth_headers, mock_gemini):
    mock_cls, fake_client = mock_gemini
    db.update_user_profile(auth_headers["user_id"], {"gemini_api_key": "stored-athlete-key"})

    resp = client.post(
        "/api/coach/chat",
        headers=auth_headers["headers"],
        json={
            "messages": [{"role": "user", "content": "hi"}],
            "user_profile": {"gemini_api_key": "key-from-request-body"},
        },
    )

    assert resp.status_code == 200
    assert mock_cls.call_args.kwargs["api_key"] == "stored-athlete-key"
    assert "key-from-request-body" not in _system_prompt(fake_client)


def test_plan_context_comes_from_the_athletes_active_plan_not_the_body(client, auth_headers, mock_gemini):
    _, fake_client = mock_gemini
    db.create_plan(
        user_id=auth_headers["user_id"],
        race_name="Real Race 50K",
        race_date="2027-05-01",
        goal_type="finish",
        target_time_hours=None,
        total_weeks=8,
    )

    resp = client.post(
        "/api/coach/chat",
        headers=auth_headers["headers"],
        json={
            "messages": [{"role": "user", "content": "What am I training for?"}],
            "context_data": {"race_name": "Spoofed Race 100M"},
        },
    )

    assert resp.status_code == 200
    prompt = _system_prompt(fake_client)
    assert "Real Race 50K" in prompt
    assert "Spoofed Race 100M" not in prompt
