"""Synthetic next-block context tests, with persistence/model I/O isolated."""

import asyncio
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

import main


@pytest.fixture
def next_block(monkeypatch):
    plan = {"id": 712, "total_weeks": 8, "start_date": "2026-10-05", "athlete_tier": "recreational"}
    monkeypatch.setattr(main, "plan_jobs", {})
    monkeypatch.setattr(main, "get_recent_plans", lambda *a, **k: [plan])
    monkeypatch.setattr(main, "get_user_by_id", lambda *a: {"id": 713, "lang": "en"})
    monkeypatch.setattr(main, "get_block_reviews", lambda *a: [])
    monkeypatch.setattr(main, "get_week_planned_volume", lambda *a: {"distance_km": 42, "duration_minutes": 252})
    monkeypatch.setattr(main, "get_block_actual_volume", lambda **k: {"total_activities_count": 0})
    monkeypatch.setattr(main, "evaluate_block_performance", lambda *a: {})
    monkeypatch.setattr(main, "_resolve_course_match", lambda *a: (None, None, None))
    monkeypatch.setattr(main, "get_recent_readiness_summary", lambda *a, **k: None)
    monkeypatch.setattr(main, "get_user_activity_ceiling", lambda *a: None)
    monkeypatch.setattr(main, "_plan_snapshot", AsyncMock(return_value=None))
    monkeypatch.setattr(main, "_store_plan_snapshot", lambda *a: None)
    monkeypatch.setattr(main, "save_workouts", lambda *a: None)
    monkeypatch.setattr(main, "set_plan_athlete_tier", lambda *a: None)
    monkeypatch.setattr(main.PlanGenerator, "generate_week_narrative", AsyncMock(return_value=(None, None)))

    async def run(status="unknown", override=True, unlocked=False, note=None, start_date="2026-10-05"):
        plan["start_date"] = start_date
        wo = {
            "week_number": 1,
            "day_of_week": "Tuesday",
            "type": "Easy",
            "title": "Easy Run",
            "duration_minutes": 48,
            "distance_km": 8,
            "is_completed": int(status == "completed"),
            "is_missed": int(status == "missed"),
        }
        monkeypatch.setattr(main, "get_plan_workouts", lambda *a: [wo])
        monkeypatch.setattr(main, "get_block_completion", lambda *a: {"unlocked": unlocked, "completion_pct": 0})
        if note:
            monkeypatch.setattr(main, "get_block_reviews", lambda *a: [{"block_number": 1, "notes": note}])
        captured = {}

        async def generate(*args, **kwargs):
            captured.update(kwargs)
            return [], "recreational"

        monkeypatch.setattr(main.PlanGenerator, "generate_plan_workouts", generate)
        result = await main._generate_next_block_for_athlete(
            main.GenerateNextBlockRequest(plan_id=712, block_number=2, override_gate=override), 713, 713
        )
        for _ in range(10):
            await asyncio.sleep(0)
            if main.plan_jobs[result["job_id"]]["status"] != "generating":
                break
        assert main.plan_jobs[result["job_id"]]["status"] == "done"
        return captured["block_context"]

    return run


@pytest.mark.asyncio
async def test_unlogged_volume_is_not_confirmed_zero_activity(next_block):
    context = await next_block()
    assert "Known logged volume 0.0km/0.0h" in context
    assert "Actual 0.0km" not in context
    assert "Unknown sessions: 1" in context
    assert "not evidence of zero training" in context


@pytest.mark.asyncio
async def test_completed_and_missed_evidence_stay_distinct(next_block):
    completed = await next_block(status="completed", unlocked=True, override=False)
    assert "Known logged volume 8.0km/0.8h" in completed
    assert "Confirmed missed sessions: 0" in completed
    missed = await next_block(status="missed")
    assert "Confirmed missed sessions: 1" in missed
    assert "Unknown sessions: 0" in missed


@pytest.mark.asyncio
async def test_override_preserves_fatigue_feedback(next_block):
    context = await next_block(note="Synthetic runner reports fatigue and poor sleep.")
    assert "fatigue and poor sleep" in context
    assert "override grants access, not completed training or readiness" in context


@pytest.mark.asyncio
async def test_locked_block_still_requires_override(next_block):
    with pytest.raises(HTTPException) as error:
        await next_block(override=False)
    assert error.value.status_code == 403


@pytest.mark.asyncio
async def test_calendar_coverage_is_independent_of_logging(next_block):
    full = await next_block()
    assert "Calendar coverage W1: 7/7 days" in full
    partial = await next_block(start_date="2026-10-10")
    assert "Calendar coverage W1: 2/7 days" in partial
    assert "Unknown sessions: 1" in partial


@pytest.mark.asyncio
async def test_watch_volume_remains_known_evidence(next_block, monkeypatch):
    monkeypatch.setattr(
        main,
        "get_block_actual_volume",
        lambda **k: {
            "total_activities_count": 2,
            "total_actual_km": 17,
            "total_actual_minutes": 102,
            "total_actual_vert_m": 170,
            "unplanned_count": 1,
            "unplanned_km": 4,
        },
    )
    context = await next_block()
    assert "Known logged volume 17.0km/1.7h (+170m D+)" in context
    assert "1 unplanned watch activity: 4.0km" in context
    assert "Unknown sessions: 1" in context
