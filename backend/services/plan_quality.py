"""Coach-level quality bar for a finished plan, pure and model-free.

plan_lint guards the book's hard rules week by week; this module scores what three coach reviews (doctrine,
safety, Vietnamese ultra) kept finding in plans that passed the lint: no climbing prep, long days far shorter
than the race, long Zone 3/4 sessions, a one-week taper, a Zone 4 race pace on a finish-only goal, road pace on
trail runs, and step lists that do not add up to the session. Thresholds are the coaches' numbers; the
NotebookLM benchmark sweep (kb_seed/plan_benchmarks.json) is meant to replace the guesses where it disagrees.
"""

import re
from dataclasses import dataclass
from typing import Any

from services.athlete_tier import (
    ELITE_ULTRA_KM,
    ELITE_ULTRA_SESSION_MIN,
    MEASURED_THRESHOLD_SOURCES,
    RECENT_LOAD_GROWTH,
    aet_ant_gap,
    hard_work_banned_phases,
)

CLIMB_MIN_PER_KM = 20  # races at or above this m D+/km need climbing prep
VERT_PEAK_SHARE = 0.4  # peak-week climbing as a share of the race's D+
VERT_SUBSTITUTE_SHARE = 0.25  # treadmill / stairs only: one weekly session cannot carry more
LONG_DAY_SHARE = 0.4  # best long day (or back-to-back pair) as a share of race time
SESSION_CAP_MIN = 300
Z3_MAX_SESSION_MIN = 75  # 60 min of work plus warm-up and cool-down
Z4_MAX_SESSION_MIN = 70  # 30 min of work plus recoveries, warm-up and cool-down
Z4_MAX_WEEK_MIN = 40  # book: 30-40 min of Zone 4 a week is hard even for conditioned athletes
Z3_MAX_WEEK_MIN = 120  # book: two-plus hours of Zone 3 a week only for high-level runners
TRAIL_RATE_MIN = 15  # m D+/km above which a run is a trail run and needs a climb-adjusted pace
STEP_TOLERANCE = 0.25
MAX_WEEK_VERT_SHARE = 0.8  # no week carries more climbing than this share of the race's
START_LOAD_TOLERANCE = 0.05  # rounding of the session lengths
_STEP_MIN = re.compile(r"(\d+)\s*(?:min|m\b|phút|')", re.IGNORECASE)


@dataclass
class Check:
    name: str
    ok: bool
    detail: str = ""


def _real(workouts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [w for w in workouts if w.get("type") != "Rest" and (w.get("duration_minutes") or 0) > 0]


def _by_week(workouts: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    weeks: dict[int, list[dict[str, Any]]] = {}
    for w in _real(workouts):
        weeks.setdefault(w["week_number"], []).append(w)
    return weeks


def _pace_mid(pace: str | None) -> float | None:
    nums = re.findall(r"(\d+):(\d{2})", pace or "")
    if not nums:
        return None
    return sum(int(m) + int(s) / 60 for m, s in nums) / len(nums)


def _climbs(w: dict[str, Any]) -> bool:
    try:
        incline = float(str(w.get("treadmill_incline") or 0).split("-")[0])
    except ValueError:
        incline = 0.0
    return incline >= 3 or bool(w.get("mountain_climb_rate")) or w.get("mountain_mode") == "indoor"


def _race_minutes(weeks: dict[int, list[dict[str, Any]]]) -> float:
    last = weeks[max(weeks)]
    race = [w for w in last if w.get("type") == "Race"]
    return float(race[0]["duration_minutes"]) if race else 0.0


def assess(workouts: list[dict[str, Any]], race: dict[str, Any], zone2_pace: str) -> list[Check]:
    """race: course_distance_km, course_elevation_gain_m, goal_type. zone2_pace: the athlete's flat Zone 2 range."""
    weeks = _by_week(workouts)
    if not weeks:
        return [Check("plan has sessions", False)]
    last = max(weeks)
    build = {k: v for k, v in weeks.items() if k < last - 1}
    km = float(race.get("course_distance_km") or 0)
    dplus = float(race.get("course_elevation_gain_m") or 0)
    minutes = {k: sum(w["duration_minutes"] for w in v if w.get("type") != "Race") for k, v in weeks.items()}
    checks: list[Check] = []

    if km and dplus / km >= CLIMB_MIN_PER_KM:
        vert = {k: sum(float(w.get("elevation_gain_m") or 0) for w in v if _climbs(w)) for k, v in build.items()}
        peak = max(vert.values(), default=0)
        share = VERT_PEAK_SHARE if race.get("outdoor_climbing") else VERT_SUBSTITUTE_SHARE
        need = share * dplus
        checks.append(
            Check(
                f"climbing prep: peak week vert >= {share:.0%} of race D+", peak >= need, f"{peak:.0f} of {need:.0f} m"
            )
        )

    race_min = _race_minutes(weeks)
    if race_min and km >= 40:
        cap = ELITE_ULTRA_SESSION_MIN if km >= ELITE_ULTRA_KM else SESSION_CAP_MIN
        need = min(LONG_DAY_SHARE * race_min, cap)
        best = 0.0
        for v in build.values():
            by_day = {w["day_of_week"]: w["duration_minutes"] for w in v}
            best = max(best, *by_day.values(), by_day.get("Saturday", 0) + by_day.get("Sunday", 0) * 1.0)
        checks.append(
            Check(
                "long day (or back-to-back) >= 40% of race time, capped",
                best >= need * 0.95,
                f"{best:.0f} vs {need:.0f} min",
            )
        )

    long_hard = [
        (w["week_number"], w["target_zone"], round(w["duration_minutes"]))
        for w in _real(workouts)
        if w.get("type") != "Race"
        and (w.get("target_zone") == "Zone 3" and w["duration_minutes"] > Z3_MAX_SESSION_MIN)
        or (w.get("target_zone") in ("Zone 4", "Zone 5") and w["duration_minutes"] > Z4_MAX_SESSION_MIN)
    ]
    checks.append(Check("no long Zone 3 (>75 min) or Zone 4 (>70 min) session", not long_hard, str(long_hard[:4])))

    heavy = []
    for k, v in weeks.items():
        z3 = sum(w["duration_minutes"] * 0.6 for w in v if w.get("target_zone") == "Zone 3" and w.get("type") != "Race")
        z4 = sum(w["duration_minutes"] * 0.5 for w in v if w.get("target_zone") in ("Zone 4", "Zone 5"))
        if z3 > Z3_MAX_WEEK_MIN or z4 > Z4_MAX_WEEK_MIN:
            heavy.append((k, round(z3), round(z4)))
    checks.append(Check("weekly Zone 3 <= 120 min and Zone 4 <= 40 min of work", not heavy, str(heavy[:4])))

    if len(weeks) >= 8:
        peak = max(minutes[k] for k in build)
        t1, t2 = minutes.get(last - 1, 0), minutes.get(last - 2, 0)
        checks.append(
            Check(
                "two-step taper (week -2 <= 85%, week -1 <= 70% of peak)",
                t2 <= 0.85 * peak and t1 <= 0.7 * peak,
                f"{t2:.0f} / {t1:.0f} vs peak {peak:.0f}",
            )
        )

    race_pace = _pace_mid(next((w.get("target_pace") for w in weeks[last] if w.get("type") == "Race"), None))
    z2 = re.findall(r"(\d+):(\d{2})", zone2_pace)
    if race_pace and z2 and race.get("goal_type") in ("finish", None):
        slow = max(int(m) + int(s) / 60 for m, s in z2)
        checks.append(
            Check(
                "finish-only race pace is not faster than flat Zone 2",
                race_pace >= slow,
                f"{race_pace:.2f} vs {slow:.2f} min/km",
            )
        )

    z2_slow = max((int(m) + int(s) / 60 for m, s in z2), default=0)
    road_on_trail = []
    for w in _real(workouts):
        dist = float(w.get("distance_km") or 0)
        rate = float(w.get("elevation_gain_m") or 0) / dist if dist else 0
        pace = _pace_mid(w.get("target_pace"))
        if rate >= TRAIL_RATE_MIN and w.get("type") != "Race" and not _climbs(w) and pace and z2_slow:
            if w.get("target_zone") in ("Zone 1", "Zone 2") and pace < z2_slow * (1 + 0.012 * rate) * 0.9:
                road_on_trail.append((w["week_number"], w["day_of_week"][:3], round(pace, 2)))
    checks.append(
        Check("trail runs (>=15 m D+/km) carry a climb-adjusted pace", not road_on_trail, str(road_on_trail[:4]))
    )

    padded = []
    for w in _real(workouts):
        if w.get("type") in ("Muscular Endurance", "Strength"):
            continue  # rep-based circuits, not a minute-by-minute run
        nums = [int(n) for n in _STEP_MIN.findall(w.get("description") or "")]
        if len(nums) >= 3:
            total = sum(nums)
            if (
                abs(total - w["duration_minutes"]) / w["duration_minutes"] > STEP_TOLERANCE
                and total < w["duration_minutes"]
            ):
                padded.append((w["week_number"], w["day_of_week"][:3], total, round(w["duration_minutes"])))
    checks.append(
        Check("step minutes add up to the session (no padding)", len(padded) <= 3, f"{len(padded)}: {padded[:3]}")
    )
    if dplus:
        over = [(k, round(sum(float(w.get("elevation_gain_m") or 0) for w in v))) for k, v in weeks.items()]
        over = [o for o in over if o[1] > MAX_WEEK_VERT_SHARE * dplus]
        checks.append(Check("no week above 80% of the race's climbing", not over, str(over[:3])))

    measured = (race.get("threshold_source") or "").lower() in MEASURED_THRESHOLD_SOURCES
    gap = aet_ant_gap(race.get("aet_hr"), race.get("ant_hr")) if measured else None
    banned = hard_work_banned_phases(is_ads=gap is not None and round(gap * 100) > 10, thresholds_measured=measured)
    hard = [
        (w["week_number"], w["day_of_week"][:3])
        for w in _real(workouts)
        if w.get("phase") in banned
        and w.get("target_zone") in ("Zone 3", "Zone 4", "Zone 5")
        and w.get("type") not in ("Race", "Muscular Endurance", "Strength")
        and not re.search(r"hill (sprint|repeat|bound)", (w.get("title") or "").lower())
    ]
    checks.append(Check("no Zone 3-5 work where the aerobic gate bans it", not hard, str(hard[:3])))
    if not measured:
        test = [w for k in (1, 2) for w in weeks.get(k, []) if "drift" in (w.get("title") or "").lower()]
        checks.append(Check("weeks 1-2 have the AeT drift test (thresholds unmeasured)", bool(test)))

    z2_mid = _pace_mid(zone2_pace)
    recent = float(race.get("current_weekly_km") or 0) * z2_mid if z2_mid else 0.0
    if recent and 1 in weeks:
        start = sum(w["duration_minutes"] for w in weeks[1] if w.get("type") != "Race")
        movable = [w for w in weeks[1] if w.get("type") in ("Easy", "Aerobic Capacity", "Recovery")]
        floor = sum(w["duration_minutes"] for w in weeks[1] if w not in movable and w.get("type") != "Race")
        cap = max(recent * RECENT_LOAD_GROWTH * (1 + START_LOAD_TOLERANCE), floor + 30 * len(movable))
        checks.append(Check("week 1 within 10% of the recent load", start <= cap, f"{start:.0f} vs {cap:.0f} min"))
    if race.get("lang") == "vi":
        from services.vi_style import naturalness_issues

        flagged = [
            (
                w["week_number"],
                w["day_of_week"][:3],
                naturalness_issues(f"{w.get('title') or ''}. {w.get('description') or ''}"),
            )
            for w in _real(workouts)
            if w.get("type") != "Race"
        ]
        flagged = [f for f in flagged if f[2]]
        checks.append(Check("Vietnamese copy: no unnatural wording", not flagged, f"{len(flagged)}: {flagged[:3]}"))
    return checks
