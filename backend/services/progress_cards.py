"""Which Progress-tab cards have enough data to say something true, and what they show.

Spec: docs/superpowers/specs/2026-10-23-progress-tab-design.md. A card is returned only once it meets
its threshold; otherwise a Pending says how far off it is. Clients render exactly what comes back, so
neither can draw an empty chart. Interpretations are keys plus numbers, worded by the client (EN/VI).
"""

from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime
from statistics import median
from typing import Any

from services.aerobic_speed import _HARD_WORKOUTS, MIN_WEEKS_FOR_PATH

CONSISTENCY_MIN_WEEKS = 2
VOLUME_MIN_WEEKS = 3
DURABILITY_MIN_RUNS = 3
LOAD_MIN_DAYS = 28
LONG_RUN_SECONDS = 5400
LOAD_ABOVE, LOAD_BELOW = 1.3, 0.8
SERIES_WEEKS = 8


@dataclass(frozen=True)
class Card:
    key: str
    value: float | None
    unit: str | None
    series: list[dict] = field(default_factory=list)
    band: tuple[float, float] | None = None
    note: dict = field(default_factory=dict)
    as_of: date | None = None
    source: str | None = None


@dataclass(frozen=True)
class Pending:
    key: str
    needs: int
    have: int


def _day(value: Any) -> date:
    return value.date() if isinstance(value, datetime) else value


def _planned(workouts: list[dict], current_week: int) -> list[dict]:
    return [w for w in workouts if w.get("type") != "Rest" and w["week_number"] < current_week]


def consistency(workouts: list[dict], current_week: int) -> Card | Pending:
    """Sessions done vs planned in completed plan weeks; a watch-matched session counts as done."""
    by_week: dict[int, list[dict]] = {}
    for w in _planned(workouts, current_week):
        by_week.setdefault(w["week_number"], []).append(w)
    if len(by_week) < CONSISTENCY_MIN_WEEKS:
        return Pending("consistency", CONSISTENCY_MIN_WEEKS, len(by_week))
    series = []
    for week in sorted(by_week)[-SERIES_WEEKS:]:
        ws = by_week[week]
        done = sum(1 for w in ws if w.get("is_completed") == 1 or w.get("matched_activity_id"))
        series.append({"week": week, "done": done, "planned": len(ws)})
    pct = round(100 * sum(s["done"] for s in series) / sum(s["planned"] for s in series))
    reasons = Counter(
        w["missed_reason"] for ws in by_week.values() for w in ws if w.get("is_missed") and w.get("missed_reason")
    )
    top = reasons.most_common(1)[0][0] if reasons else None
    return Card(
        "consistency", float(pct), "%", series, note={"key": "consistency", "pct": pct, "top_missed_reason": top}
    )


def volume(workouts: list[dict], activities: list[dict], plan_monday: date, current_week: int) -> Card | Pending:
    """Weekly km and climb, actual (synced or logged activities) against planned, for completed weeks."""
    actual: dict[int, list[float]] = {}
    for a in activities:
        week = (_day(a["start_time"]) - plan_monday).days // 7 + 1
        if 1 <= week < current_week:
            km, climb = actual.setdefault(week, [0.0, 0.0])
            actual[week] = [km + (a.get("distance_km") or 0.0), climb + (a.get("elevation_gain_m") or 0.0)]
    weeks = sorted(w for w, (km, _) in actual.items() if km > 0)
    if len(weeks) < VOLUME_MIN_WEEKS:
        return Pending("volume", VOLUME_MIN_WEEKS, len(weeks))
    planned: dict[int, list[float]] = {}
    for w in _planned(workouts, current_week):
        km, climb = planned.setdefault(w["week_number"], [0.0, 0.0])
        planned[w["week_number"]] = [km + (w.get("distance_km") or 0.0), climb + (w.get("elevation_gain_m") or 0.0)]
    series = [
        {
            "week": w,
            "km": round(actual[w][0], 1),
            "km_planned": round(planned.get(w, [0.0, 0.0])[0], 1),
            "climb_m": round(actual[w][1]),
            "climb_planned": round(planned.get(w, [0.0, 0.0])[1]),
        }
        for w in weeks[-SERIES_WEEKS:]
    ]
    return Card("volume", series[-1]["km"], "km", series, note={"key": "volume"})


def durability(activities: list[dict]) -> Card | Pending:
    """Heart-rate drift on steady long runs; the value is the median of the last three (lower is better)."""
    runs = sorted(
        (
            a
            for a in activities
            if a.get("hr_drift_pct") is not None
            and a["duration_seconds"] >= LONG_RUN_SECONDS
            and a.get("workout_type") not in _HARD_WORKOUTS
        ),
        key=lambda a: a["start_time"],
    )
    if len(runs) < DURABILITY_MIN_RUNS:
        return Pending("durability", DURABILITY_MIN_RUNS, len(runs))
    series = [{"date": _day(a["start_time"]).isoformat(), "pct": a["hr_drift_pct"]} for a in runs[-SERIES_WEEKS:]]
    value = median(a["hr_drift_pct"] for a in runs[-3:])
    return Card("durability", value, "%", series, note={"key": "durability"}, as_of=_day(runs[-1]["start_time"]))


def training_load(metrics: list[dict], window_days: int = 28) -> Card | Pending:
    """Last 7 days against the last 6 weeks, from one provider's rows. Worded as above/within/below the
    athlete's usual -- never as injury risk (the ratio does not predict injury)."""
    rows = sorted((m for m in metrics if m.get("training_load_short") is not None), key=lambda m: m["metric_date"])
    if len(rows) < LOAD_MIN_DAYS:
        return Pending("load", LOAD_MIN_DAYS, len(rows))
    latest = rows[-1]
    ratio = latest.get("load_ratio") or (
        latest["training_load_short"] / latest["training_load_long"] if latest.get("training_load_long") else None
    )
    key = (
        "load.within"
        if ratio is None
        else "load.above"
        if ratio > LOAD_ABOVE
        else "load.below"
        if ratio < LOAD_BELOW
        else "load.within"
    )
    series = [
        {
            "date": _day(m["metric_date"]).isoformat(),
            "short": m["training_load_short"],
            "long": m.get("training_load_long"),
        }
        for m in rows[-window_days:]
    ]
    return Card(
        "load", round(ratio, 2) if ratio else None, None, series, note={"key": key}, as_of=_day(latest["metric_date"])
    )


def aerobic_speed_card(checkpoints: list[dict], path: dict | None) -> Card | Pending:
    """Pace at aerobic-threshold heart rate per week, read against the B/A path (services/aerobic_speed)."""
    if path is None:
        return Pending("aerobic_speed", MIN_WEEKS_FOR_PATH, len(checkpoints))
    series = [
        {"week": c["week_number"], "pace": c["pace_min_km"]}
        for c in sorted(checkpoints, key=lambda c: c["week_number"])
    ]
    note = {"key": "aerobic_speed", "b": path["b"], "a": path["a"], "measured_pct": path["measured_pct"]}
    return Card("aerobic_speed", series[-1]["pace"] if series else None, "min/km", series, note=note)
