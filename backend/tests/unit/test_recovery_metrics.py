"""Apple Health recovery metrics: sleep column, HRV baseline, single-provider readiness."""

import datetime
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest

from db import get_latest_daily_metrics, get_recent_readiness_summary, upsert_daily_metric
from services import recovery_baseline
from services.providers.base import CanonicalDailyMetric


def _row(day, provider, hrv=None, status=None, rhr=None, ratio=None, recov=None, sleep=None):
    return MagicMock(
        metric_date=day,
        source_provider=provider,
        resting_hr=rhr,
        hrv_ms=hrv,
        hrv_status=status,
        load_ratio=ratio,
        recovery_percent=recov,
        sleep_minutes=sleep,
    )


def _readiness(rows):
    with patch("db.engine.connect") as mock_connect:
        conn = MagicMock()
        mock_connect.return_value.__enter__.return_value = conn
        conn.execute.return_value.fetchall.return_value = rows
        return get_recent_readiness_summary(user_id=1, days=7)


D = datetime.date(2026, 10, 13)


def test_upsert_writes_sleep_minutes():
    with patch("db.engine.connect") as mock_connect:
        conn = MagicMock()
        mock_connect.return_value.__enter__.return_value = conn
        conn.execute.return_value.fetchone.return_value = (7,)
        upsert_daily_metric(1, CanonicalDailyMetric(D, "apple_health", sleep_minutes=412))
    sql, params = str(conn.execute.call_args[0][0]), conn.execute.call_args[0][1]
    assert "sleep_minutes = COALESCE(EXCLUDED.sleep_minutes, daily_metrics.sleep_minutes)" in sql
    assert params["sleep_minutes"] == 412


def test_coros_only_keeps_old_output_plus_new_keys():
    r = _readiness([_row(D, "coros", hrv=65.0, status="Balanced", rhr=48, ratio=1.1, recov=85)])
    assert r["source_provider"] == "coros"
    assert r["avg_hrv_ms"] == 65.0
    assert r["readiness_flag"] == "optimal"
    assert r["nights_recorded"] == 0
    assert r["avg_sleep_minutes"] is None


def test_apple_only():
    r = _readiness([_row(D, "apple_health", hrv=80.0, status="normal", rhr=50, sleep=420)])
    assert r["source_provider"] == "apple_health"
    assert r["avg_hrv_ms"] == 80.0
    assert r["avg_sleep_minutes"] == 420
    assert r["nights_recorded"] == 1


def test_apple_newer_drops_coros_rows():
    rows = [
        _row(D, "apple_health", hrv=90.0),
        _row(D - timedelta(days=1), "coros", hrv=40.0),
        _row(D - timedelta(days=1), "apple_health", hrv=100.0),
    ]
    r = _readiness(rows)
    assert r["source_provider"] == "apple_health"
    assert r["avg_hrv_ms"] == 95.0
    assert r["days_recorded"] == 2


def test_same_day_tie_goes_to_coros():
    rows = [_row(D, "apple_health", hrv=90.0), _row(D, "coros", hrv=40.0)]
    r = _readiness(rows)
    assert r["source_provider"] == "coros"
    assert r["avg_hrv_ms"] == 40.0


def test_short_sleep_over_four_nights_is_fatigued():
    rows = [_row(D - timedelta(days=i), "apple_health", status="normal", sleep=330) for i in range(4)]
    assert _readiness(rows)["readiness_flag"] == "fatigued"


def test_short_sleep_over_two_nights_does_not_count():
    rows = [_row(D - timedelta(days=i), "apple_health", status="normal", sleep=300) for i in range(2)]
    assert _readiness(rows)["readiness_flag"] == "optimal"


def test_overreaching_still_wins_over_short_sleep():
    rows = [_row(D - timedelta(days=i), "coros", ratio=1.6, sleep=300) for i in range(4)]
    assert _readiness(rows)["readiness_flag"] == "overreaching"


def test_empty_shape_has_new_keys():
    r = _readiness([])
    assert r["source_provider"] is None
    assert r["nights_recorded"] == 0
    assert r["avg_sleep_minutes"] is None


def test_latest_daily_metrics_orders_coros_first_on_tie():
    with patch("db.engine.connect") as mock_connect:
        conn = MagicMock()
        mock_connect.return_value.__enter__.return_value = conn
        conn.execute.return_value.fetchone.return_value = None
        assert get_latest_daily_metrics(1) is None
    sql = str(conn.execute.call_args[0][0])
    assert "(source_provider = 'coros') DESC" in sql
    assert "sleep_minutes" in sql


# --- baseline ---------------------------------------------------------------


def _steady(n):
    return [60.0 + (3 if i % 2 else -3) for i in range(n)]


def test_thirteen_days_give_no_status():
    assert recovery_baseline.hrv_status_for(_steady(13), [50.0]) == (None, None)


def test_dip_is_low():
    base, status = recovery_baseline.hrv_status_for(_steady(28), [50.0, 52.0, 51.0])
    assert base == 60.0
    assert status == "low"


def test_steady_is_normal():
    assert recovery_baseline.hrv_status_for(_steady(28), [60.0, 61.0, 59.0])[1] == "normal"


def test_statuses_window_excludes_the_day_and_trailing_includes_it():
    start = date(2026, 9, 1)
    values = {start + timedelta(days=i): v for i, v in enumerate(_steady(28))}
    day = start + timedelta(days=28)
    values[day] = 30.0
    [(d, base, status)] = recovery_baseline.statuses(values, [day])
    assert d == day
    assert base == 60.0  # the 30.0 on the day itself is not in its own baseline
    assert status == "low"  # but it drags the 3-day mean down


def test_statuses_skip_days_without_hrv():
    assert recovery_baseline.statuses({}, [date(2026, 9, 1)]) == []


def test_refresh_reads_and_writes_apple_health_only():
    synced = date(2026, 10, 10)
    values = [(synced - timedelta(days=i), 60.0) for i in range(30)]
    with (
        patch("services.recovery_baseline.db.get_daily_hrv", return_value=values) as get,
        patch("services.recovery_baseline.db.set_daily_hrv_status") as put,
    ):
        recovery_baseline.refresh(1, [synced])
    user_id, start, end, provider = get.call_args[0]
    assert provider == "apple_health"
    assert start == synced - timedelta(days=31)
    assert end == synced + timedelta(days=3)
    assert put.call_args[0][1] == "apple_health"
    written = put.call_args[0][2]
    assert [d for d, _, _ in written] == [synced]  # the 3 later days have no row yet
    assert written[0][2] == "normal"


# --- prompts ----------------------------------------------------------------


async def _plan_prompt(summary):
    from services.plan_generator import PlanGenerator

    resp = MagicMock(text="invalid json to trigger fallback")
    client = MagicMock()
    client.models.generate_content.return_value = resp
    race_info = {"name": "Run", "date": "2026-11-01", "goal_type": "finish", "readiness_summary": summary}
    with (
        patch("google.genai.Client", return_value=client),
        patch("services.kb_retrieval.search_scheduler_chunks", return_value=[]),
    ):
        await PlanGenerator.generate_plan_workouts(
            plan_id=3,
            user_profile={"age": 35, "current_weekly_km": 30.0},
            race_info=race_info,
            total_weeks=6,
            api_key="fake-gemini-key",
            block_number=1,
            weeks_per_block=2,
        )
    return client.models.generate_content.call_args.kwargs.get("contents", "")


APPLE_SUMMARY = {
    "source_provider": "apple_health",
    "days_recorded": 6,
    "avg_hrv_ms": 54.0,
    "latest_hrv_status": "low",
    "avg_resting_hr": 52.0,
    "avg_load_ratio": None,
    "latest_load_ratio": None,
    "avg_recovery_percent": None,
    "avg_sleep_minutes": 370,
    "nights_recorded": 6,
    "readiness_flag": "fatigued",
}


@pytest.mark.asyncio
async def test_plan_readiness_block_names_source_and_shows_sleep():
    prompt = await _plan_prompt(APPLE_SUMMARY)
    assert "7-DAY WEARABLE BIOLOGICAL READINESS & LOAD RATIO (Apple Health):" in prompt
    assert "- Sleep: 6h10 avg (6 nights)" in prompt
    assert "FATIGUED (Low HRV / Recovery < 45% / Sleep < 6h avg)" in prompt
    assert "ACWR (Acute:Chronic Load Ratio): N/A" in prompt


@pytest.mark.asyncio
async def test_plan_readiness_block_without_sleep():
    prompt = await _plan_prompt(
        {**APPLE_SUMMARY, "source_provider": "coros", "nights_recorded": 0, "avg_sleep_minutes": None}
    )
    assert "LOAD RATIO (COROS):" in prompt
    assert "- Sleep:" not in prompt


def test_coach_recovery_section():
    from services.coach_prompts import compile_coach_prompt

    prompt = compile_coach_prompt(system_base="BASE", context={"recovery": APPLE_SUMMARY})
    assert "### Recovery (last 7 days, Apple Health)" in prompt
    assert "- HRV 54 ms (status: low) | Resting HR 52 bpm" in prompt
    assert "- Sleep 6h10 avg over 6 nights" in prompt
    assert "- Readiness: FATIGUED" in prompt
    assert "never to diagnose" in prompt


def test_coach_recovery_section_omits_empty_lines():
    from services.coach_prompts import format_recovery

    text = format_recovery({"source_provider": "coros", "readiness_flag": "insufficient_data", "nights_recorded": 0})
    assert text == ""
    text = format_recovery({"source_provider": "coros", "avg_resting_hr": 48.0, "readiness_flag": "optimal"})
    assert "Sleep" not in text and "HRV" not in text
    assert "- Resting HR 48 bpm" in text


def _chat_context(readiness):
    from services.coach_context import build_chat_context

    with (
        patch("db.get_user_by_id", return_value={"id": 1}),
        patch("db.get_active_plan", return_value=None),
        patch("db.get_activities_for_user", return_value=[]),
        patch("db.get_chat_thread_messages", return_value=[]),
        patch("services.race_history.prompt_summary", return_value=""),
        patch("services.fitness_snapshot.chat_summary", return_value={}),
        patch("db.get_recent_readiness_summary", **readiness),
    ):
        return build_chat_context(user_id=1, question="how am I recovering?")


def test_chat_context_carries_recovery():
    assert _chat_context({"return_value": APPLE_SUMMARY})["recovery"] == APPLE_SUMMARY


def test_chat_context_omits_recovery_without_rows_or_on_error():
    assert _chat_context({"return_value": {"days_recorded": 0}})["recovery"] is None
    assert _chat_context({"side_effect": RuntimeError("db down")})["recovery"] is None
