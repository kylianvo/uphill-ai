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
from services import aerobic_speed, calendar_rules, fitness_tracking, plan_lint
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


# ─── Training response: the plan's phase read against the body's HRV / resting-HR trend ───
# The four states follow WHOOP's published HRV training guide (Optimal, functional and non-functional
# overreaching, restorative): HRV down with resting HR up is expected in a load phase and a warning in a
# light one. Unlike a watch, Uphill knows which phase the athlete is in, so the read is judged against it.

RESPONSE_CURRENT_DAYS = 7
RESPONSE_WINDOW_DAYS = 35  # this week plus the four weeks before it as the baseline
RESPONSE_MIN_DAYS = 14
RESPONSE_MIN_CURRENT = 3
SHIFT, LARGE_SHIFT = 0.5, 1.5  # in robust spreads of the baseline days


def _shift(rows: list[dict], field: str, today: date, floor: float) -> dict | None:
    current = [r[field] for r in rows if (today - _day(r["metric_date"])).days < RESPONSE_CURRENT_DAYS]
    base = [r[field] for r in rows if (today - _day(r["metric_date"])).days >= RESPONSE_CURRENT_DAYS]
    if len(current) < RESPONSE_MIN_CURRENT or not base:
        return None
    low, mid, high = usual_range(base, floor)
    now = sum(current) / len(current)
    return {"now": now, "mid": mid, "low": low, "high": high, "z": (now - mid) / ((high - low) / 2)}


def _response_state(hrv: dict, rhr: dict) -> str:
    good = (hrv["z"] >= SHIFT) + (rhr["z"] <= -SHIFT)
    bad = (hrv["z"] <= -SHIFT) + (rhr["z"] >= SHIFT)
    if bad == 2 and (hrv["z"] <= -LARGE_SHIFT or rhr["z"] >= LARGE_SHIFT):
        return "strained"
    if bad and not good:
        return "loading"
    if good and not bad:
        return "adapting"
    return "steady"


def training_response(
    workouts: list[dict], metrics: list[dict], plan_monday: date, today: date
) -> Card | Pending | None:
    """This week's HRV and resting HR against the four weeks before, read against the plan's phase.
    None when the week has no phase or the recent days are missing (stale data is not "pending")."""
    current_week = (today - plan_monday).days // 7 + 1
    phase = next((w["phase"] for w in workouts if w.get("week_number") == current_week and w.get("phase")), None)
    if not phase:
        return None
    hrv_rows = _present(metrics, "hrv_ms", today, RESPONSE_WINDOW_DAYS)
    rhr_rows = _present(metrics, "resting_hr", today, RESPONSE_WINDOW_DAYS)
    have = min(len(hrv_rows), len(rhr_rows))
    if have < RESPONSE_MIN_DAYS:
        return Pending("response", RESPONSE_MIN_DAYS, have)
    hrv, rhr = _shift(hrv_rows, "hrv_ms", today, 3), _shift(rhr_rows, "resting_hr", today, 1)
    if hrv is None or rhr is None:
        return None
    group = "down" if phase in plan_lint.DOWN_PHASES else "load"
    state = _response_state(hrv, rhr)
    phase_of = {
        w["week_number"]: w["phase"] for w in sorted(workouts, key=lambda w: w["week_number"]) if w.get("phase")
    }
    by_day: dict[date, dict] = {}
    for name, source_field, rows in (("hrv", "hrv_ms", hrv_rows), ("rhr", "resting_hr", rhr_rows)):
        for r in rows:
            day = _day(r["metric_date"])
            by_day.setdefault(day, {"date": day.isoformat(), "phase": phase_of.get((day - plan_monday).days // 7 + 1)})
            by_day[day][name] = r[source_field]
    return Card(
        "response",
        None,
        None,
        [by_day[d] for d in sorted(by_day)],
        band=(round(hrv["low"], 1), round(hrv["high"], 1)),
        note={
            "key": f"response.{group}.{state}",
            "phase": phase,
            "week": current_week,
            "hrv_pct": round(100 * (hrv["now"] - hrv["mid"]) / hrv["mid"]),
            "rhr_delta": round(rhr["now"] - rhr["mid"]),
            "hrv_z": round(hrv["z"], 2),
            "rhr_z": round(rhr["z"], 2),
            "rhr_band": [round(rhr["low"], 1), round(rhr["high"], 1)],
        },
        as_of=max(by_day),
        source=hrv_rows[-1].get("source_provider"),
    )


def health_summary(cards: list[Card]) -> Card | None:
    """The rule-based Coach's read: which signals sit outside the athlete's usual range."""
    if not cards:
        return None
    # Only the tiring direction counts: more sleep, lower resting HR or higher HRV than usual is good news.
    off = [c.key for c in cards if c.note.get("key") in ("sleep.below", "rhr.above", "hrv.below")]
    return Card(
        "coach_read", None, None, note={"key": "health.off" if off else "health.all_usual", "contributors": off}
    )


# ─── Today's targets: what to do with the next hard session, and how much to sleep tonight ───

EASY_SWAP_MAX_MIN = 45
ADJUST_WITHIN_DAYS = 1  # today's body only speaks for today's or tomorrow's session
SLEEP_PAYBACK_NIGHTS = 3  # a short week is paid back over a few nights, not one
SLEEP_PAYBACK_CAP_MIN = 60
LONG_RUN_SLEEP_BONUS_MIN = 30


def session_adjustment(
    w: dict, day: date, today_date: date, summary: Card | None, response: Card | Pending | None
) -> dict | None:
    """The next hard session, kept, capped or swapped for easy running. In a loading week where Training
    response reads the dip as expected, the session stays and is capped at its targets."""
    if not plan_lint.is_hard(w) or (day - today_date).days > ADJUST_WITHIN_DAYS:
        return None
    if not summary or summary.note["key"] != "health.off":
        return {"kind": "as_planned"}
    key = response.note["key"] if isinstance(response, Card) else ""
    if key.startswith("response.load.") and key != "response.load.strained":
        return {"kind": "cap"}
    minutes = min(plan_lint._min(w) or EASY_SWAP_MAX_MIN, EASY_SWAP_MAX_MIN)
    return {"kind": "swap_easy", "minutes": int(5 * round(minutes / 5))}


def sleep_target(
    rows: list[dict], today_date: date, workouts: list[dict] = (), plan_monday: date | None = None
) -> dict | None:
    """Tonight's sleep: your usual, plus a share of this week's shortfall, plus extra before a long run."""
    present = _present(rows, "sleep_minutes", today_date, WINDOW_DAYS)
    if len(present) < SLEEP_MIN_NIGHTS:
        return None
    _, usual, _ = usual_range([r["sleep_minutes"] for r in present], 30)
    week = [r["sleep_minutes"] for r in present if (today_date - _day(r["metric_date"])).days < CURRENT_DAYS]
    debt = sum(max(0.0, usual - m) for m in week)
    tomorrow = today_date + timedelta(days=1)
    long_tomorrow = bool(plan_monday) and any(
        plan_lint.is_long(w)
        and not w.get("is_completed")
        and w.get("day_of_week") in calendar_rules.DAYS
        and calendar_rules.workout_date(plan_monday, w["week_number"], w["day_of_week"]) == tomorrow
        for w in workouts
    )
    target = usual + min(debt / SLEEP_PAYBACK_NIGHTS, SLEEP_PAYBACK_CAP_MIN)
    target += LONG_RUN_SLEEP_BONUS_MIN if long_tomorrow else 0
    return {
        "target_min": int(10 * round(target / 10)),
        "usual_min": round(usual),
        "debt_min": round(debt),
        "long_run_tomorrow": long_tomorrow,
    }


def today_card(
    workouts: list[dict],
    plan_monday: date | None,
    today_date: date,
    summary: Card | None,
    response: Card | Pending | None = None,
    tonight: dict | None = None,
) -> Card | None:
    """What to do today: the health read, the next unfinished session with what to do with it, and
    tonight's sleep target."""
    upcoming = []
    if plan_monday:
        for w in workouts:
            if w.get("type") == "Rest" or w.get("is_completed") == 1 or w.get("is_missed"):
                continue
            day = calendar_rules.workout_date(plan_monday, w["week_number"], w["day_of_week"])
            if day >= today_date:
                upcoming.append((day, w))
    nxt = None
    adjust = None
    if upcoming:
        day, w = min(upcoming, key=lambda pair: pair[0])
        nxt = {
            "title": w.get("title"),
            "type": w.get("type"),
            "date": day.isoformat(),
            "duration_minutes": w.get("duration_minutes"),
            "target_pace": w.get("target_pace"),
        }
        adjust = session_adjustment(w, day, today_date, summary, response)
    if nxt is None and summary is None:
        return None
    return Card(
        "today",
        None,
        None,
        note={
            "key": "today",
            "health": summary.note["key"] if summary else None,
            "contributors": summary.note["contributors"] if summary else [],
            "next": nxt,
            "adjust": adjust,
            "tonight": tonight,
        },
    )


# ─── Weekly review: one pattern from last week, from data already stored ───


def _good_days(rows: list[dict], start: date, end: date) -> dict[date, bool]:
    """Per day in [start, end): True when neither HRV nor resting HR reads on the tiring side of the usual
    range of the 28 days before `start`. Days with neither signal are left out."""
    before = [r for r in rows if 0 < (start - _day(r["metric_date"])).days <= WINDOW_DAYS]
    bands = {}
    for name, floor in (("hrv_ms", 3), ("resting_hr", 1)):
        values = [r[name] for r in before if r.get(name) is not None]
        if len(values) >= SLEEP_MIN_NIGHTS:
            bands[name] = usual_range(values, floor)
    out: dict[date, bool] = {}
    for r in rows:
        day = _day(r["metric_date"])
        if not start <= day < end:
            continue
        checks = []
        if "hrv_ms" in bands and r.get("hrv_ms") is not None:
            checks.append(r["hrv_ms"] >= bands["hrv_ms"][0])
        if "resting_hr" in bands and r.get("resting_hr") is not None:
            checks.append(r["resting_hr"] <= bands["resting_hr"][2])
        if checks:
            out[day] = all(checks)
    return out


def week_review(workouts: list[dict], rows: list[dict], plan_monday: date, today_date: date) -> Card | None:
    """Last finished plan week as facts, most telling first: short sleep before long runs, then whether
    hard sessions landed on good days, then sessions done. The client words them."""
    week = (today_date - plan_monday).days // 7  # the last finished week
    ws = [w for w in _planned(workouts, week + 1) if w["week_number"] == week]
    if week < 1 or not ws:
        return None
    start = plan_monday + timedelta(days=7 * (week - 1))
    done = [w for w in ws if w.get("is_completed") == 1 or w.get("matched_activity_id")]
    on_day = {
        id(w): calendar_rules.workout_date(plan_monday, week, w["day_of_week"])
        for w in done
        if w.get("day_of_week") in calendar_rules.DAYS
    }
    facts = []
    # Sleep on a row's date is the night that ended that morning.
    sleep_by_day = {_day(r["metric_date"]): r["sleep_minutes"] for r in rows if r.get("sleep_minutes") is not None}
    history = [m for d, m in sleep_by_day.items() if 0 < (start - d).days <= WINDOW_DAYS]
    longs = [w for w in done if plan_lint.is_long(w) and on_day.get(id(w)) in sleep_by_day]
    if longs and len(history) >= SLEEP_MIN_NIGHTS:
        low = usual_range(history, 30)[0]
        short = sum(1 for w in longs if sleep_by_day[on_day[id(w)]] < low)
        if short:
            facts.append({"kind": "short_sleep_long_run", "count": short, "total": len(longs)})
    good = _good_days(rows, start, start + timedelta(days=7))
    hard = [w for w in done if plan_lint.is_hard(w) and on_day.get(id(w)) in good]
    if len(hard) >= 2:
        facts.append({"kind": "hard_on_good_days", "count": sum(good[on_day[id(w)]] for w in hard), "total": len(hard)})
    facts.append({"kind": "sessions", "count": len(done), "total": len(ws)})
    return Card("week_review", None, None, note={"key": "week_review", "week": week, "facts": facts})


# ─── Assembly: the only part that reads the database ───

HISTORY_DAYS = (28, 90)
APPLE_CONNECTED_DAYS = 30
TRAINING_ORDER = (
    "today",
    "goal",
    "response",
    "week_review",
    "aerobic_speed",
    "consistency",
    "volume",
    "durability",
    "load",
)
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
    rows = _single_provider(
        [m for m in metrics if any(m.get(f) is not None for f in ("sleep_minutes", "resting_hr", "hrv_ms"))]
    )
    health = [sleep(rows, today, days), resting_hr(rows, today, days), hrv(rows, today, days)]
    summary = health_summary([c for c in health if isinstance(c, Card)])
    monday = aerobic_speed.plan_monday(plan["start_date"]) if plan else None
    workouts = db.get_plan_workouts_with_match(plan["id"]) if plan else []
    tonight = sleep_target(rows, today, workouts, monday)
    if isinstance(health[0], Card):
        health[0].note["tonight"] = tonight
    if section == "training":
        since = today - timedelta(days=90)
        if plan:
            since = min(since, monday)
        activities = db.get_activities_for_pace(
            uid,
            datetime.combine(since, datetime.min.time()),
            datetime.combine(today + timedelta(days=1), datetime.min.time()),
        )
        if plan:
            current_week = (today - monday).days // 7 + 1
            path = fitness_tracking.path_payload(fitness_tracking.refresh(plan, db.get_user_by_id(uid), today))
            response = training_response(workouts, rows, monday, today)
            results += [
                today_card(workouts, monday, today, summary, response, tonight),
                Card("goal", None, None),
                response,
                week_review(workouts, rows, monday, today),
                aerobic_speed_card(db.get_fitness_checkpoints(plan["id"]), path),
                consistency(workouts, current_week),
                volume(workouts, [a for a in activities if _day(a["start_time"]) >= monday], monday, current_week),
            ]
        else:
            results.append(today_card([], None, today, summary, tonight=tonight))
        results = [r for r in results if r is not None]
        results += [durability(activities), training_load(metrics, days)]
        order = TRAINING_ORDER
    else:
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
