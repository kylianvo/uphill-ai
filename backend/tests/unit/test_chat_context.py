"""Unit tests for bounded trusted context assembly and citation resolution."""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from db import CoachChatError
from services.coach_context import (
    build_chat_context,
    resolve_citations,
    trim_context_to_budget,
)


def test_build_chat_context_filters_expired_and_error_messages():
    now = datetime(2026, 9, 20, 12, 0, tzinfo=UTC)

    mock_user = {
        "id": 1,
        "age": 32,
        "max_hr": 185,
        "aet_hr": 140,
        "ant_hr": 168,
        "current_weekly_km": 45.0,
        "athlete_tier": "intermediate",
    }
    mock_plan = {"id": 10, "plan_status": "active"}
    mock_workouts = [
        {"id": 101, "name": "Zone 2 Aerobic Run", "scheduled_date": "2026-09-21", "distance_km": 12.0},
        {"id": 102, "name": "Hill Intervals", "scheduled_date": "2026-09-23", "distance_km": 10.0},
    ]
    mock_activities = [
        {"id": 201, "activity_type": "running", "distance_km": 10.5, "start_time": now - timedelta(days=2)},
        {
            "id": 202,
            "activity_type": "running",
            "distance_km": 15.0,
            "start_time": now - timedelta(days=20),
        },  # >14d, exclude
    ]
    mock_messages = [
        # Ok message 10 days ago (keep)
        {"id": 1, "role": "user", "content": "How are you?", "status": "ok", "created_at": now - timedelta(days=10)},
        {
            "id": 2,
            "role": "assistant",
            "content": "I am great.",
            "status": "ok",
            "created_at": now - timedelta(days=10),
        },
        # Error / interrupted message (exclude)
        {
            "id": 3,
            "role": "assistant",
            "content": "Failed answer",
            "status": "error",
            "created_at": now - timedelta(days=5),
        },
        # Expired message 95 days ago (exclude)
        {"id": 4, "role": "user", "content": "Old question", "status": "ok", "created_at": now - timedelta(days=95)},
    ]

    with (
        patch("db.get_user_by_id", return_value=mock_user),
        patch("db.get_active_plan", return_value=mock_plan),
        patch("db.get_plan_workouts", return_value=mock_workouts),
        patch("db.get_activities_for_user", return_value=mock_activities),
        patch("db.get_chat_thread_messages", return_value=mock_messages),
    ):
        ctx = build_chat_context(
            user_id=1,
            question="What is my next workout?",
            now=now,
        )

        assert ctx["athlete"]["age"] == 32
        assert len(ctx["workouts"]) == 2
        # Only activity within 14 days retained
        assert len(ctx["recent_activities"]) == 1
        assert ctx["recent_activities"][0]["id"] == 201

        # Only 2 valid history messages retained
        assert len(ctx["history"]) == 2
        assert [m["id"] for m in ctx["history"]] == [1, 2]
        assert ctx["question"] == "What is my next workout?"


def test_trim_context_to_budget_trims_history_then_evidence():
    history = [{"id": i, "content": f"Message {i}" * 50} for i in range(10)]
    evidence = [
        {"ref": f"ref-{i}", "title": f"Title {i}", "content": "Evidence text " * 50, "score": 0.5 + i * 0.05}
        for i in range(5)
    ]

    essential = {
        "athlete": {"max_hr": 180},
        "workouts": [{"name": "Long run"}],
        "question": "How do I run downhill safely?",
    }

    # Custom estimator where each item counts for 500 tokens, budget is 2000
    def fake_count(ctx):
        h_tokens = len(ctx.get("history", [])) * 500
        e_tokens = len(ctx.get("evidence", [])) * 500
        return 1000 + h_tokens + e_tokens  # 1000 essential

    trimmed = trim_context_to_budget(
        context={**essential, "history": list(history), "evidence": list(evidence)},
        token_counter=fake_count,
        max_budget=2000,
    )

    # All history trimmed, evidence trimmed to fit under 2000 budget
    assert len(trimmed["history"]) == 0
    assert len(trimmed["evidence"]) <= 2
    assert trimmed["question"] == "How do I run downhill safely?"


def test_trim_context_raises_if_essential_exceeds_budget():
    essential = {
        "athlete": {"max_hr": 180},
        "workouts": [{"name": "Huge workout list"}],
        "question": "Can I run?",
    }

    def fake_count(ctx):
        return 20000  # Exceeds 16,000 budget

    with pytest.raises(CoachChatError) as exc_info:
        trim_context_to_budget(
            context=essential,
            token_counter=fake_count,
            max_budget=16000,
        )
    assert exc_info.value.code == "chat_context_too_large"


def test_resolve_citations():
    evidence = [
        {
            "ref": "abc123def456",
            "title": "Training Principles",
            "source_label": "Training for the Uphill Athlete",
            "url": "https://uphillathlete.com/principles",
        },
        {
            "ref": "789xyz123456",
            "title": "Nutrition Guide",
            "source_label": "Evoke Endurance Nutrition",
            "url": "javascript:alert(1)",  # Invalid scheme
        },
    ]

    # Reference by [ref] or [source_label]
    text = "Follow low heart rate [ref:abc123def456] and eat carbs [ref:789xyz123456] or [ref:unknown]."
    resolved = resolve_citations(text, evidence)

    assert len(resolved) == 2
    # First resolved has valid URL
    assert resolved[0]["ref"] == "abc123def456"
    assert resolved[0]["url"] == "https://uphillathlete.com/principles"

    # Second resolved had invalid URL scheme, so url is sanitized to None
    assert resolved[1]["ref"] == "789xyz123456"
    assert resolved[1]["url"] is None
