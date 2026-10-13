"""Apple Health recovery metrics: sleep column, HRV baseline, single-provider readiness."""

import datetime
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

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
