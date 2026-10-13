"""Personal HRV baseline for providers that report raw HRV without a status (Apple Health).

COROS ships its own hrv_status; Apple Health only gives a daily SDNN value. Each
Apple Health day gets a baseline (mean of the previous 28 days' HRV, at least 14
of them present) and a status: "low" when the 3-day mean ending on that day sits
more than one SD below the baseline, "normal" otherwise. "low" is already in the
fatigued vocabulary of db.get_recent_readiness_summary.
"""

from collections.abc import Iterable
from datetime import date, timedelta
from statistics import mean, pstdev

import db

APPLE_HEALTH = "apple_health"
BASELINE_DAYS = 28
MIN_BASELINE_DAYS = 14
TRAILING_DAYS = 3


def hrv_status_for(history: list[float], last3: list[float]) -> tuple[float | None, str | None]:
    """history: the previous 28 days' HRV values (excluding the day). last3: the day and up to
    two days before it. Returns (baseline_ms, status), status "low" | "normal" | None."""
    if len(history) < MIN_BASELINE_DAYS or not last3:
        return None, None
    base, sd = mean(history), pstdev(history)
    return round(base, 1), ("low" if mean(last3) < base - sd else "normal")


def statuses(values: dict[date, float], days: Iterable[date]) -> list[tuple[date, float | None, str | None]]:
    """(day, baseline, status) for each day in `days` that has its own HRV value."""
    out = []
    for day in sorted(set(days)):
        if day not in values:
            continue
        history = [v for d, v in values.items() if day - timedelta(days=BASELINE_DAYS) <= d < day]
        last3 = [v for d, v in values.items() if day - timedelta(days=TRAILING_DAYS - 1) <= d <= day]
        baseline, status = hrv_status_for(history, last3)
        out.append((day, baseline, status))
    return out


def refresh(user_id: int, dates: Iterable[date]) -> None:
    """Recomputes baseline/status for each synced date and the 3 days after it (their
    trailing mean and history include the synced date). Only apple_health rows with HRV."""
    dates = list(dates)
    if not dates:
        return
    affected = {d + timedelta(days=k) for d in dates for k in range(TRAILING_DAYS + 1)}
    start = min(dates) - timedelta(days=BASELINE_DAYS + TRAILING_DAYS)
    end = max(affected)
    values = dict(db.get_daily_hrv(user_id, start, end, APPLE_HEALTH))
    db.set_daily_hrv_status(user_id, APPLE_HEALTH, statuses(values, affected))
