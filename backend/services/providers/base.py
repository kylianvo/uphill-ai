"""Provider-agnostic shapes every device adapter normalises into.

Nothing above this layer knows which vendor the data came from. That is what
lets the matching engine, physiology sync and readiness scoring be written once,
and what lets Garmin drop in if their developer programme reopens.

The field set mirrors what parsers/fit_parser.py already produces, so a manually
uploaded FIT file and a COROS sync converge on the same representation.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


@dataclass(frozen=True)
class CanonicalActivity:
    external_id: str
    provider: str
    activity_type: str
    start_time: datetime
    duration_seconds: float
    end_time: datetime | None = None
    distance_km: float | None = None
    elevation_gain_m: float | None = None
    elevation_loss_m: float | None = None
    avg_hr: int | None = None
    max_hr: int | None = None
    avg_pace_sec_per_km: float | None = None
    adjusted_pace_sec_per_km: float | None = None
    calories: int | None = None
    training_load: float | None = None
    aerobic_te: float | None = None
    anaerobic_te: float | None = None
    sets: int | None = None
    device_model: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CanonicalDailyMetric:
    metric_date: date
    provider: str
    resting_hr: int | None = None
    hrv_ms: float | None = None
    hrv_baseline_ms: float | None = None
    hrv_status: str | None = None
    training_load_short: float | None = None
    training_load_long: float | None = None
    load_ratio: float | None = None
    recovery_percent: int | None = None
