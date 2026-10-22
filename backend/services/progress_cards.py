"""Which Progress-tab cards have enough data to say something true, and what they show.

Spec: docs/superpowers/specs/2026-10-23-progress-tab-design.md. A card is returned only once it meets
its threshold; otherwise a Pending says how far off it is. Clients render exactly what comes back, so
neither can draw an empty chart. Interpretations are keys plus numbers, worded by the client (EN/VI).
"""

from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from statistics import median
from types import SimpleNamespace
from typing import Any

import db
from services import aerobic_speed, fitness_tracking
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
    # A session marked done with no watch activity counts at its planned distance: athletes without a device log by hand.
    for w in _planned(workouts, current_week):
        if w.get("is_completed") == 1 and not w.get("matched_activity_id"):
            km, climb = actual.setdefault(w["week_number"], [0.0, 0.0])
            actual[w["week_number"]] = [km + (w.get("distance_km") or 0.0), climb + (w.get("elevation_gain_m") or 0.0)]
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


# ─── Health: each function receives ONE provider's rows (HRV methods differ between devices) ───

SLEEP_MIN_NIGHTS = 7
RHR_MIN_DAYS = 7
HRV_MIN_NIGHTS = 14
WINDOW_DAYS = 28
CURRENT_DAYS = 7  # the "now" value is the last week's mean, read against the window's usual range


def usual_range(values: list[float], floor: float) -> tuple[float, float, float]:
    """(low, mid, high): the median with a robust half-width (1.4826 x MAD), never narrower than `floor`."""
    mid = median(values)
    half = max(floor, 1.4826 * median(abs(v - mid) for v in values))
    return mid - half, mid, mid + half


def _present(rows: list[dict], field: str, today: date, window_days: int) -> list[dict]:
    return sorted(
        (r for r in rows if r.get(field) is not None and 0 <= (today - _day(r["metric_date"])).days < window_days),
        key=lambda r: r["metric_date"],
    )


def _current(rows: list[dict], field: str, today: date) -> float:
    recent = [r[field] for r in rows if (today - _day(r["metric_date"])).days < CURRENT_DAYS] or [rows[-1][field]]
    return sum(recent) / len(recent)


def _status(value: float, low: float, high: float) -> str:
    return "below" if value < low else "above" if value > high else "within"


def _metric_card(
    key: str,
    note_prefix: str,
    rows: list[dict],
    field: str,
    unit: str,
    today: date,
    needs: int,
    window_days: int,
    band: tuple[float, float] | None,
    floor: float,
    extra_fields: tuple[str, ...] = (),
) -> tuple[Card | Pending, float | None]:
    present = _present(rows, field, today, max(window_days, WINDOW_DAYS))
    counted = [r for r in present if (today - _day(r["metric_date"])).days < WINDOW_DAYS]
    if len(counted) < needs:
        return Pending(key, needs, len(counted)), None
    low, mid, high = usual_range([r[field] for r in counted], floor)
    if band:
        low, high = band
    current = _current(counted, field, today)
    series = [
        {
            "date": _day(r["metric_date"]).isoformat(),
            "value": r[field],
            **{f: r[f] for f in extra_fields if r.get(f) is not None},
        }
        for r in present
        if (today - _day(r["metric_date"])).days < window_days
    ]
    card = Card(
        key,
        round(current, 1),
        unit,
        series,
        band=(round(low, 1), round(high, 1)),
        note={"key": f"{note_prefix}.{_status(current, low, high)}"},
        as_of=_day(counted[-1]["metric_date"]),
        source=counted[-1].get("source_provider"),
    )
    return card, current - mid


def sleep(metrics: list[dict], today: date, window_days: int = WINDOW_DAYS) -> Card | Pending:
    """Minutes asleep per night (naps included) against the athlete's own usual range. Duration and
    timing only: wearables don't stage sleep reliably."""
    card, _ = _metric_card(
        "sleep",
        "sleep",
        metrics,
        "sleep_minutes",
        "min",
        today,
        SLEEP_MIN_NIGHTS,
        window_days,
        None,
        30,
        ("sleep_start", "sleep_end"),
    )
    return card


def resting_hr(metrics: list[dict], today: date, window_days: int = WINDOW_DAYS) -> Card | Pending:
    card, delta = _metric_card(
        "resting_hr", "rhr", metrics, "resting_hr", "bpm", today, RHR_MIN_DAYS, window_days, None, 2
    )
    if isinstance(card, Card):
        card.note["delta"] = round(delta)
    return card


def hrv(metrics: list[dict], today: date, window_days: int = WINDOW_DAYS) -> Card | Pending:
    """Overnight HRV against the device's own normal range when it reports one (COROS), else the usual range."""
    ranged = [m for m in metrics if m.get("hrv_range_low") is not None and m.get("hrv_range_high") is not None]
    band = None
    if ranged:
        latest = max(ranged, key=lambda m: m["metric_date"])
        band = (latest["hrv_range_low"], latest["hrv_range_high"])
    card, _ = _metric_card("hrv", "hrv", metrics, "hrv_ms", "ms", today, HRV_MIN_NIGHTS, window_days, band, 3)
    return card


def health_summary(cards: list[Card]) -> Card | None:
    """The rule-based Coach's read: which signals sit outside the athlete's usual range."""
    if not cards:
        return None
    off = [c.key for c in cards if not c.note.get("key", "").endswith(".within")]
    return Card(
        "coach_read", None, None, note={"key": "health.off" if off else "health.all_usual", "contributors": off}
    )


# ─── Assembly: the only part that reads the database ───

HISTORY_DAYS = (28, 90)
APPLE_CONNECTED_DAYS = 30
TRAINING_ORDER = ("goal", "aerobic_speed", "consistency", "volume", "durability", "load")
HEALTH_ORDER = ("coach_read", "sleep", "resting_hr", "hrv")


def _single_provider(metrics: list[dict]) -> list[dict]:
    """Newest provider wins, COROS on a tie -- the readiness rule (db._pick_readiness_provider)."""
    if not metrics:
        return []
    rows = sorted(metrics, key=lambda m: m["metric_date"], reverse=True)
    provider = db._pick_readiness_provider([SimpleNamespace(**r) for r in rows])
    return [m for m in metrics if m["source_provider"] == provider]


def _payload(card: Card) -> dict:
    out = asdict(card)
    out["band"] = list(card.band) if card.band else None
    out["as_of"] = card.as_of.isoformat() if card.as_of else None
    return out


def build(user: dict, section: str, today: date | None = None, days: int = 28) -> dict:
    today = today or date.today()
    uid = user["id"]
    plan = db.get_active_plan(uid)
    # Two weeks of slack: a 28-row card must not stay pending because of a few unsynced days.
    metrics = db.get_daily_metrics(uid, today - timedelta(days=max(days, WINDOW_DAYS) + 14))
    coros = db.get_connection(uid, "coros")
    connected = bool(coros and coros.get("status") == "active") or any(
        m["source_provider"] == "apple_health" and (today - _day(m["metric_date"])).days < APPLE_CONNECTED_DAYS
        for m in metrics
    )
    results: list[Card | Pending] = []
    if section == "training":
        since = today - timedelta(days=90)
        if plan:
            monday = aerobic_speed.plan_monday(plan["start_date"])
            since = min(since, monday)
        activities = db.get_activities_for_pace(
            uid,
            datetime.combine(since, datetime.min.time()),
            datetime.combine(today + timedelta(days=1), datetime.min.time()),
        )
        if plan:
            current_week = (today - monday).days // 7 + 1
            workouts = db.get_plan_workouts_with_match(plan["id"])
            path = fitness_tracking.path_payload(fitness_tracking.refresh(plan, db.get_user_by_id(uid), today))
            results += [
                Card("goal", None, None),
                aerobic_speed_card(db.get_fitness_checkpoints(plan["id"]), path),
                consistency(workouts, current_week),
                volume(workouts, [a for a in activities if _day(a["start_time"]) >= monday], monday, current_week),
            ]
        results += [durability(activities), training_load(metrics, days)]
        order = TRAINING_ORDER
    else:
        rows = _single_provider(
            [m for m in metrics if any(m.get(f) is not None for f in ("sleep_minutes", "resting_hr", "hrv_ms"))]
        )
        health = [sleep(rows, today, days), resting_hr(rows, today, days), hrv(rows, today, days)]
        summary = health_summary([c for c in health if isinstance(c, Card)])
        results += ([summary] if summary else []) + health
        order = HEALTH_ORDER
    cards = sorted((r for r in results if isinstance(r, Card)), key=lambda c: order.index(c.key))
    return {
        "section": section,
        "connected": connected,
        "has_plan": plan is not None,
        "plan_id": plan["id"] if plan else None,
        "cards": [_payload(c) for c in cards],
        "pending": [asdict(r) for r in results if isinstance(r, Pending)],
    }
