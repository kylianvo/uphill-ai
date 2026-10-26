"""Deterministic structural lint of generated training weeks (no LLM).

The generation prompt already states these rules; this checks the result, because under
constraints (few training days, gym access, a mountain minimum) the model breaks them.
Each Issue.message is an imperative instruction, written to be pasted into a corrective
retry prompt. Caps come from the athlete's tier profile, not from one-size numbers.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from services import ultra_rules
from services.athlete_tier import (
    LONG_SHARE_SOFT,
    TierProfile,
    session_cap_minutes,
    taper_shift,
    week_capacity_parts,
)

if TYPE_CHECKING:  # goal_demands imports race_readiness, which imports this module
    from services.goal_demands import Demands

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DOWN_PHASES = {"Recovery", "Taper", "Race Week"}
HARD_TYPES = {"Tempo", "Threshold", "Interval"}
HARD_ZONES = {"Zone 3", "Zone 4", "Zone 5"}
LONG_SHARE_TOLERANCE = LONG_SHARE_SOFT + 0.02  # soft margin plus rounding of planned minutes
# Planned D+ is a noisy estimate (it moves with which session lands on a mountain day), so
# the vertical check only catches gross spikes; the doctrine's 7-10% cap is applied to time.
MAX_VERT_GROWTH = 0.25
MIN_VERT_STEP_M = 300  # ignore growth on tiny bases
BACK_TO_BACK_SHARE = 0.50  # two consecutive big days may hold at most half the week
BACK_TO_BACK_MIN_DAY = 0.25  # ...and a "big" day is one holding a quarter of the week (a long run + a short recovery run is not a back-to-back)
# hill sprints, short hill repeats (PlanGenerator.HILL_SPRINT_TITLE_KEYWORDS), bounding, strides, and the
# "Fartlek / Surges" a hill sprint becomes on a day with no hill
NEUROMUSCULAR_KEYWORDS = ("sprint", "stride", "bound", "hill repeat", "surges")
MAX_SESSION_MIN = 300  # KB: the longest single session is capped at four to five hours
# No doctrine number for one session; this catches the gross spikes (130 -> 213 min) the weekly cap misses.
MAX_LONG_RUN_GROWTH = 0.25
MIN_LONG_RUN_STEP_MIN = 20
BUILD_WEEKS_BEFORE_RECOVERY = 3  # 3 build : 1 recovery


@dataclass(frozen=True)
class Prefs:
    """What the athlete asked for; a week that ignores it is a defect, not a style choice."""

    long_run_day: str | None = None
    days_per_week: int | None = None
    demands: "Demands | None" = None  # the goal's physical demands (enables the specificity checks)
    flat_only: bool = False  # no training mountain or local hills: climbing cannot be judged on gain
    total_weeks: int | None = None  # lets the specificity checks find the last pre-taper week
    mountain_day: bool = False  # a weekly mountain day: an ultra follows Quang's ladder (services/ultra_rules.py)
    me_first_weeks: frozenset[int] = frozenset()  # short ultra plans: ME weeks before the Zone 3 weeks
    quality_gated: bool = False  # AeT gate on (gap > 10% or estimated thresholds): one quality session at most


@dataclass(frozen=True)
class Issue:
    code: str
    week: int
    message: str


def _min(w: dict[str, Any]) -> float:
    try:
        return max(float(w.get("duration_minutes") or 0), 0.0)
    except (TypeError, ValueError):
        return 0.0


def _active(ws: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [w for w in ws if w.get("type") != "Rest"]


def _day(w: dict[str, Any]) -> int | None:
    return DAYS.index(w["day_of_week"]) if w.get("day_of_week") in DAYS else None


def is_hard(w: dict[str, Any]) -> bool:
    return w.get("type") in HARD_TYPES or w.get("target_zone") in HARD_ZONES


def is_long(w: dict[str, Any]) -> bool:
    return (w.get("type") or "").strip().lower() == "long run"


def _is_me(w: dict[str, Any]) -> bool:
    return (w.get("type") or "").strip().lower() == "muscular endurance"


def week_minutes(ws: list[dict[str, Any]]) -> float:
    """Run time of the week. ME sits on top of the aerobic volume (book), so it is not counted."""
    return sum(_min(w) for w in _active(ws) if not _is_me(w))


def _vert(ws: list[dict[str, Any]]) -> float:
    return sum(float(w.get("elevation_gain_m") or 0) for w in _active(ws))


def _label(w: dict[str, Any]) -> str:
    return f"{w.get('title') or w.get('type')} ({DAYS[_day(w)]})"


def _by_week(workouts: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    out: dict[int, list[dict[str, Any]]] = {}
    for w in workouts:
        if isinstance(w.get("week_number"), int):
            out.setdefault(w["week_number"], []).append(w)
    return out


def _is_down(weeks: dict[int, list[dict[str, Any]]], wk: int) -> bool:
    """A planned down week: a down phase, or at least 10% under the week before."""
    ws = weeks.get(wk) or []
    if any((w.get("phase") or "") in DOWN_PHASES for w in ws):
        return True
    prev = week_minutes(weeks.get(wk - 1) or [])
    return bool(prev) and week_minutes(ws) <= prev * 0.9


def _day_minutes(ws: list[dict[str, Any]]) -> dict[int, float]:
    out: dict[int, float] = {}
    for w in ws:
        if _day(w) is not None:
            out[_day(w)] = out.get(_day(w), 0.0) + _min(w)
    return out


def is_b2b_week(ws: list[dict[str, Any]]) -> bool:
    """Two consecutive days that each hold a long day's running (a back-to-back weekend)."""
    dm = _day_minutes(_active(ws))
    return any(d + 1 in dm and dm[d] >= B2B_DAY_MIN and dm[d + 1] >= B2B_DAY_MIN for d in dm)


def b2b_targets(workouts: list[dict[str, Any]], week: int, longest_target: float) -> tuple[int, int]:
    """(Saturday, Sunday) minutes for a back-to-back weekend: the Sunday long run stays close to last week's
    (the growth cap still applies) and Saturday is almost as long, so the pair is what adds the volume."""
    prior = [_min(w) for w in workouts if (w.get("week_number") or 0) < week and is_long(w)]
    recent = max(prior[-2:], default=120.0)
    sun = min(recent * (1 + MAX_LONG_RUN_GROWTH) * 0.9, longest_target, MAX_SESSION_MIN)
    sat = min(max(sun * 0.85, B2B_DAY_MIN), 180.0)
    return int(round(sat / 5) * 5), int(round(sun / 5) * 5)


def _ultra(prefs: Prefs | None, profile: TierProfile) -> tuple["ultra_rules.Band", bool] | None:
    """(band, advanced) when the plan follows Quang's mountain-day ladder, else None."""
    if not prefs or not prefs.mountain_day or not prefs.demands or not prefs.total_weeks:
        return None
    band = ultra_rules.band_for(prefs.demands.distance_km)
    return (band, ultra_rules.is_advanced(profile.key)) if band else None


def is_quality(w: dict[str, Any]) -> bool:
    """A Zone 3+ session; hill sprints and strides are neuromuscular work, not quality sessions."""
    title = (w.get("title") or "").lower()
    return is_hard(w) and w.get("type") != "Race" and not any(k in title for k in NEUROMUSCULAR_KEYWORDS)


def in_ultra_window(prefs: Prefs | None, week: int) -> bool:
    """Is `week` one of the last build weeks of an ultra plan, where a back-to-back weekend belongs? Never for a
    mountain-day ladder plan: one long mountain day replaces the back-to-back."""
    d = prefs.demands if prefs else None
    if prefs and prefs.mountain_day and d is not None and ultra_rules.band_for(d.distance_km):
        return False
    if d is None or not prefs.total_weeks or d.distance_km < ULTRA_KM or (prefs.days_per_week or 5) < 5:
        return False
    lo, hi = _B2B_WINDOW_FROM_END
    shift = taper_shift(prefs.total_weeks)
    return prefs.total_weeks - lo - shift <= week <= prefs.total_weeks - hi - shift


def _climbs(w: dict[str, Any]) -> bool:
    if (
        float(w.get("treadmill_incline") or 0) > 0
        if str(w.get("treadmill_incline") or "").replace(".", "").isdigit()
        else False
    ):
        return True
    text = f"{w.get('title') or ''} {w.get('description') or ''}".lower()
    return any(k in text for k in CLIMB_KEYWORDS)


def lint_week(
    workouts: list[dict[str, Any]], week: int, profile: TierProfile, prefs: Prefs | None = None
) -> list[Issue]:
    """Issues in `week`, judged against the weeks before it in `workouts`."""
    weeks = _by_week(workouts)
    ws = _active(weeks.get(week) or [])
    if not ws:
        return []
    total = week_minutes(ws)
    prev_ws = weeks.get(week - 1) or []
    prev_total = week_minutes(prev_ws)
    issues: list[Issue] = []
    ultra = _ultra(prefs, profile)

    # Strength needs 48 h clear of the long run and of hard sessions (DOMS peaks ~48 h).
    for me in (w for w in ws if _is_me(w) and _day(w) is not None):
        for other in ws:
            if other is me or _day(other) is None or not (is_long(other) or is_hard(other)):
                continue
            gap = abs(_day(other) - _day(me)) * 24
            if 0 < gap < 48:
                issues.append(
                    Issue(
                        "ME_SPACING",
                        week,
                        f"Week {week}: the Muscular Endurance session {_label(me)} is only {gap} h from "
                        f"{_label(other)}. Keep ME at least 48 hours from the long run and from any Zone 3+ or "
                        f"interval session: move it to another day.",
                    )
                )

    hard_days = sorted({_day(w) for w in ws if is_hard(w) and _day(w) is not None})
    for a, b in zip(hard_days, hard_days[1:]):
        if b - a == 1:
            issues.append(
                Issue(
                    "HARD_ADJACENT",
                    week,
                    f"Week {week}: hard sessions on consecutive days ({DAYS[a]} and {DAYS[b]}). "
                    f"Put an easy or rest day between them.",
                )
            )

    cap = profile.max_weekly_progression
    # On a ladder plan the long run's step is Quang's (ultra_rules), so growth is judged on the rest of the week.
    lr_now = max((_min(w) for w in ws if is_long(w)), default=0.0) if ultra else 0.0
    lr_prev = max((_min(w) for w in _active(prev_ws) if is_long(w)), default=0.0) if ultra else 0.0
    if prev_total and not _is_down(weeks, week - 1) and total - lr_now > (prev_total - lr_prev) * (1 + cap) + 1:
        issues.append(
            Issue(
                "VOLUME_JUMP",
                week,
                f"Week {week}: total time {total:.0f} min is {(total / prev_total - 1) * 100:.0f}% above week "
                f"{week - 1} ({prev_total:.0f} min). Cap the increase at {cap * 100:.0f}% "
                f"(at most {prev_total * (1 + cap):.0f} min).",
            )
        )

    prev_vert = _vert(prev_ws)
    vert_now, vert_prev = (
        (_vert([w for w in ws if not is_long(w)]), _vert([w for w in prev_ws if not is_long(w)]))
        if ultra
        else (_vert(ws), prev_vert)
    )
    if (
        vert_prev
        and not _is_down(weeks, week - 1)  # rebuilding after a down week, like the volume rule
        and vert_now > vert_prev * (1 + MAX_VERT_GROWTH)
        and vert_now - vert_prev > MIN_VERT_STEP_M
    ):
        issues.append(
            Issue(
                "VERT_JUMP",
                week,
                f"Week {week}: planned climbing {_vert(ws):.0f} m D+ is {(_vert(ws) / prev_vert - 1) * 100:.0f}% "
                f"above week {week - 1} ({prev_vert:.0f} m). Keep vertical progression gradual "
                f"(at most about +{MAX_VERT_GROWTH * 100:.0f}%).",
            )
        )

    # An ultra's last build weeks may hold a back-to-back weekend (at most twice), with a larger long-run share.
    b2b_ok = False
    if in_ultra_window(prefs, week) and is_b2b_week(ws):
        lo, hi = _B2B_WINDOW_FROM_END
        lo += taper_shift(prefs.total_weeks)
        earlier = sum(1 for wk in range(prefs.total_weeks - lo, week) if wk in weeks and is_b2b_week(weeks[wk]))
        b2b_ok = earlier < B2B_MAX_WEEKS
    long_cap = profile.long_run_share_cap + (B2B_LONG_SHARE_BONUS if b2b_ok else 0.0)
    phase_for_share = next((w.get("phase") for w in ws if w.get("phase")), "")
    if phase_for_share == "Taper":
        long_cap += TAPER_LONG_SHARE_BONUS  # volume drops faster than the long run does
    if any(is_long(w) and _min(w) > MAX_SESSION_MIN for w in ws):
        long_cap = max(long_cap, BIG_DAY_LONG_SHARE)  # an 8-hour day is about a third of a 150 mile build week

    # A recovery week is for recovering: no Zone 3+ session. (Taper and race weeks have their own shape.)
    phase_now = next((w.get("phase") for w in ws if w.get("phase")), "")
    planned_recovery = bool(prev_total) and total <= prev_total * RECOVERY_DROP
    if phase_now not in ("Taper", "Race Week") and (phase_now == "Recovery" or planned_recovery) and week > 1:
        for w in ws:
            if is_hard(w) and w.get("type") != "Race":
                issues.append(
                    Issue(
                        "HARD_IN_DOWN_WEEK",
                        week,
                        f"Week {week} is a recovery week: replace {_label(w)} with an easy Zone 1-2 session. "
                        f"A recovery week has no Zone 3+ work.",
                    )
                )
                break

    if phase_now == "Taper" and prev_total and total > prev_total * TAPER_MAX_SHARE:
        issues.append(
            Issue(
                "TAPER_NOT_LIGHT",
                week,
                f"Week {week} is the taper: cut the volume to at most {prev_total * TAPER_MAX_SHARE:.0f} min "
                f"(now {total:.0f}); keep the long run and one short quality session, drop the rest.",
            )
        )

    # A steep race without hills: every build-phase Muscular Endurance session is climbing work (stairs, incline
    # treadmill, weighted carries), not gym straight sets.
    d = prefs.demands if prefs else None
    if (
        d is not None
        and prefs.flat_only
        and d.steepness_m_per_km >= MIN_STEEP_M_PER_KM
        and phase_now in ("Build", "Peak")
    ):
        for w in ws:
            if _is_me(w) and not _climbs(w):
                issues.append(
                    Issue(
                        "CLIMB_SPECIFICITY",
                        week,
                        f"Week {week}: the course climbs {d.steepness_m_per_km:.0f} m D+/km and the athlete has no "
                        f"hills. Make {_label(w)} outdoor weighted carries, stair climbing or incline-treadmill laps "
                        f"(a 5-15% bodyweight pack, laps of 5+ min), not gym straight sets.",
                    )
                )
                break

    # An ultra's back-to-back weekend belongs in the last build weeks: asked at total-4, and again at total-3 when
    # the first ask fell on a recovery week (a recovery week is excused).
    shift = taper_shift(prefs.total_weeks) if prefs and prefs.total_weeks else 0
    if (
        in_ultra_window(prefs, week)
        and d is not None
        and week in (prefs.total_weeks - 4 - shift, prefs.total_weeks - 3 - shift)
    ):
        lo = prefs.total_weeks - _B2B_WINDOW_FROM_END[0] - shift
        done_before = any(wk in weeks and is_b2b_week(weeks[wk]) for wk in range(lo, week))
        if not done_before and not planned_recovery and not is_b2b_week(ws):
            sat, sun = b2b_targets(workouts, week, d.longest_session_min)
            issues.append(
                Issue(
                    "B2B_MISSING",
                    week,
                    f"Week {week}: this ultra has no back-to-back weekend in its last build weeks. Make Saturday "
                    f"about {sat} min and Sunday's Long Run about {sun} min, both Zone 2, practising race fueling; "
                    f"shorten the midweek easy runs so the week total stays within the weekly cap.",
                )
            )

    # the share caps were calibrated on all training time, ME included; volume (`total`) leaves ME out
    all_minutes = sum(_min(w) for w in ws)
    longest = max((_min(w) for w in ws if is_long(w)), default=0.0)
    if longest and longest / all_minutes > long_cap + LONG_SHARE_TOLERANCE:
        issues.append(
            Issue(
                "LONG_SHARE",
                week,
                f"Week {week}: the long run is {longest / all_minutes * 100:.0f}% of weekly time; the cap for this "
                f"athlete is {long_cap * 100:.0f}%. Shorten the long run or lengthen the "
                f"other sessions.",
            )
        )

    day_min = _day_minutes(ws)
    for d in sorted(day_min):
        # a ladder plan's mountain day and the easy day beside it are Quang's week shape, not an overreach block
        if d + 1 in day_min and len(ws) >= 3 and not b2b_ok and not ultra:
            pair = day_min[d] + day_min[d + 1]
            if (
                pair > all_minutes * BACK_TO_BACK_SHARE
                and min(day_min[d], day_min[d + 1]) >= BACK_TO_BACK_MIN_DAY * all_minutes
            ):
                issues.append(
                    Issue(
                        "BACK_TO_BACK",
                        week,
                        f"Week {week}: {DAYS[d]} and {DAYS[d + 1]} hold {pair / all_minutes * 100:.0f}% of the week. "
                        f"Back-to-back long days are only an occasional overreach block and must stay under "
                        f"{BACK_TO_BACK_SHARE * 100:.0f}% of weekly volume.",
                    )
                )
                break

    long_runs = [w for w in ws if is_long(w) and _day(w) is not None]
    if (
        prefs
        and prefs.long_run_day in DAYS
        and long_runs
        and not any(_day(w) == DAYS.index(prefs.long_run_day) for w in long_runs)
    ):
        issues.append(
            Issue(
                "LONG_RUN_DAY",
                week,
                f"Week {week}: the long run is on {DAYS[_day(long_runs[0])]} but the athlete's long-run day is "
                f"{prefs.long_run_day}. Put it on {prefs.long_run_day}.",
            )
        )
    training_days = {_day(w) for w in ws if _day(w) is not None}
    in_down_phase = any(
        (w.get("phase") or "") in DOWN_PHASES for w in ws
    )  # race/taper/recovery weeks are short on purpose
    if prefs and prefs.days_per_week and len(training_days) < prefs.days_per_week and not in_down_phase:
        issues.append(
            Issue(
                "DAYS_SHORT",
                week,
                f"Week {week} has {len(training_days)} training days; the athlete trains {prefs.days_per_week} days "
                f"a week. Spread the week over {prefs.days_per_week} days.",
            )
        )
    recent_long = max(
        (_min(w) for back in (1, 2) for w in weeks.get(week - back, []) if is_long(w)),
        default=0.0,
    )
    longest_now = max((_min(w) for w in long_runs), default=0.0)
    ladder = ultra_rules.ladder(ultra[0], ultra[1], prefs.total_weeks) if ultra else {}
    if (
        recent_long
        and not (ultra and longest_now <= ladder.get(week, 0))  # a ladder step is Quang's, not a jump
        and longest_now > recent_long * (1 + MAX_LONG_RUN_GROWTH)
        and longest_now - recent_long > MIN_LONG_RUN_STEP_MIN
    ):
        issues.append(
            Issue(
                "LONG_RUN_JUMP",
                week,
                f"Week {week}: the long run is {longest_now:.0f} min, up from {recent_long:.0f} min in the last two "
                f"weeks (+{(longest_now / recent_long - 1) * 100:.0f}%). Grow the long run gradually "
                f"(at most about +{MAX_LONG_RUN_GROWTH * 100:.0f}% per step).",
            )
        )

    session_cap = session_cap_minutes(
        profile, prefs.demands.distance_km if prefs and prefs.demands else None, prefs.mountain_day if prefs else False
    )
    for w in ws:
        if _min(w) > session_cap and w.get("type") != "Race":  # the race is not a training session
            issues.append(
                Issue(
                    "SESSION_TOO_LONG",
                    week,
                    f"Week {week}: {_label(w)} is {_min(w):.0f} min. No single session may exceed "
                    f"{session_cap // 60} hours.",
                )
            )

    if ultra:
        issues += _ultra_issues(weeks, ws, week, ultra, recent_long, prefs)
        issues += _me_load(ws, week, profile, total, week in prefs.me_first_weeks)  # only ladder plans state it

    if not _is_down(weeks, week):
        builds, wk = 1, week - 1
        while wk >= 1 and weeks.get(wk) and not _is_down(weeks, wk):
            builds += 1
            wk -= 1
        if builds > BUILD_WEEKS_BEFORE_RECOVERY:
            issues.append(
                Issue(
                    "RECOVERY_DUE",
                    week,
                    f"Week {week} is build week {builds} in a row. Make it a recovery week at about 70-85% of "
                    f"week {week - 1}'s time before building again (3 build weeks : 1 recovery week).",
                )
            )
    return issues


def _ultra_issues(
    weeks: dict[int, list[dict[str, Any]]],
    ws: list[dict[str, Any]],
    week: int,
    ultra: tuple["ultra_rules.Band", bool],
    recent_long: float,
    prefs: Prefs,
) -> list[Issue]:
    """Quang's mountain-day rules: the ladder long run, weekday minimum, quality sessions only in the window."""
    band, advanced = ultra
    out: list[Issue] = []
    phase = next((w.get("phase") for w in ws if w.get("phase")), "")
    building = phase in ("Base", "Build", "Peak") and not _is_down(weeks, week)
    lo = ultra_rules.weekday_minutes(band, advanced)[0]
    if building:
        for w in ws:
            if (
                w.get("type") in ("Easy", "Aerobic Capacity")
                and _day(w) is not None
                and _day(w) < 5
                and _min(w) < lo
                and not any(k in (w.get("title") or "").lower() for k in NEUROMUSCULAR_KEYWORDS)  # short by design
            ):
                out.append(
                    Issue(
                        "WEEKDAY_SHORT",
                        week,
                        f"Week {week}: {_label(w)} is {_min(w):.0f} min. Weekday easy runs for this race are at "
                        f"least {lo} min: lengthen it (the extra volume goes on weekdays, not the long run).",
                    )
                )
                break
        target = ultra_rules.long_run_target(band, advanced, week, prefs.total_weeks, recent_long or None)
        longest = max((_min(w) for w in ws if is_long(w)), default=0.0)
        if target and not ultra_rules.is_deload(week, prefs.total_weeks) and longest < target * 0.9:
            out.append(
                Issue(
                    "ULTRA_LADDER",
                    week,
                    f"Week {week}: the mountain-day Long Run is {longest:.0f} min. Make the Long Run about "
                    f"{target} min (the long-run ladder for this race).",
                )
            )
    quality = [w for w in ws if is_quality(w)]
    if any(w.get("target_zone") in ("Zone 4", "Zone 5") for w in quality):
        out.append(
            Issue(
                "QUALITY_COUNT",
                week,
                f"Week {week}: no Zone 4-5 work for an ultra. Make the quality session uphill or rolling intervals "
                f"in Zone 3.",
            )
        )
    elif phase in ("Base", "Build", "Peak"):
        in_window = week in ultra_rules.quality_weeks(prefs.total_weeks) and week not in prefs.me_first_weeks
        want, reps, rep = ultra_rules.quality_dose(advanced, prefs.quality_gated, week_minutes(ws))
        want = want if in_window else 0
        if not _is_down(weeks, week) and len(quality) != want:
            out.append(
                Issue(
                    "QUALITY_COUNT",
                    week,
                    f"Week {week} has {len(quality)} Zone 3+ sessions; it needs {want}. "
                    + (
                        f"Make {want} of them uphill or rolling intervals in Zone 3 ({reps} x {rep} min of work, "
                        f"at most {ultra_rules.QUALITY_MAX_MIN} min in all), 48 h from the long run and ME."
                        if want
                        else "Before the last 8 build weeks an ultra has no Zone 3+ sessions: hill sprints, strides "
                        "and ME only."
                    ),
                )
            )
    return out


def _me_load(
    ws: list[dict[str, Any]], week: int, profile: TierProfile, run_minutes: float, me_first: bool = False
) -> list[Issue]:
    """Book: ME once a week (advanced athletes up to twice in Base and Build), at most 10% of training time."""
    me = [w for w in ws if _is_me(w)]
    if not me:
        return []
    phase = next((w.get("phase") for w in ws if w.get("phase")), "")
    allowed = 2 if me_first or (ultra_rules.is_advanced(profile.key) and phase in ("Base", "Build")) else 1
    me_min = sum(_min(w) for w in me)
    # one standard session (45-60 min) is always allowed; the 10% share caps what is added beyond it
    if len(me) <= allowed and (
        len(me) == 1 or me_first or me_min <= ultra_rules.ME_MAX_SHARE * (run_minutes + me_min) + 1
    ):
        return []
    return [
        Issue(
            "ME_LOAD",
            week,
            f"Week {week} has {len(me)} Muscular Endurance sessions ({me_min:.0f} min). Keep ME to {allowed} a week "
            f"and at most {ultra_rules.ME_MAX_SHARE * 100:.0f}% of the week's training time.",
        )
    ]


TIME_ON_FEET_SHARE = 0.90  # the longest session must reach 90% of the target (or of what the days can hold)
GRADIENT_SHARE = 0.60  # long runs must reach 60% of the course steepness (or of the training mountain's)
RECOVERY_DROP = 0.85  # a week this far under the one before is a planned recovery week (not a phase-change dip)
ULTRA_KM = 80  # races at or above this get back-to-back weekends and climbing-specific work
B2B_DAY_MIN = 90  # each day of a back-to-back weekend holds at least this much running
B2B_LONG_SHARE_BONUS = 0.10  # a back-to-back week may put more of its time into the long run
TAPER_MAX_SHARE = 0.85  # the taper week is at most this share of the week before
TAPER_LONG_SHARE_BONUS = 0.10
BIG_DAY_LONG_SHARE = 0.35
B2B_MAX_WEEKS = 2  # ...in at most this many of the last build weeks
CLIMB_KEYWORDS = (
    "stair",
    "incline",
    "carry",
    "carries",
    "uphill",
    "hill",
    "cầu thang",
    "dốc",
    "leo ",
    "mang tạ",
    "balo",
)
MIN_CLIMB_SESSIONS = 2  # climbing-load sessions in the build for a steep race without hills
_B2B_WINDOW_FROM_END = (6, 3)  # the last four pre-taper weeks: total-6 .. total-3
SPECIFICITY_WEEKS_BEFORE_END = 3  # taper, race week and the recovery week close the plan
MIN_STEEP_M_PER_KM = 25.0  # flatter courses need no climbing rehearsal
LATE_WEEKS = 4
_NO_CLIMB_MODES = {"skip", "indoor", "chill"}


def _specificity(
    workouts: list[dict[str, Any]], weeks: set[int], profile: TierProfile, prefs: Prefs | None
) -> list[Issue]:
    """Plan-level checks against the goal's demands. Run only on a block that holds its Peak phase."""
    d = prefs.demands if prefs else None
    by = _by_week(workouts)
    peaks = sorted(w for w in weeks if any(x.get("phase") == "Peak" for x in by.get(w, [])))
    last_build = (
        prefs.total_weeks - SPECIFICITY_WEEKS_BEFORE_END - taper_shift(prefs.total_weeks)
        if prefs and prefs.total_weeks
        else None
    )
    if d is None:
        return []
    # Models rarely label a "Peak" phase: the last pre-taper week is the anchor when the plan length is known.
    anchor = last_build if last_build in weeks else (peaks[-1] if peaks else None)
    if anchor is None:
        return []
    training = [w for w in sorted(by) if w <= anchor and any(x.get("phase") in ("Build", "Peak") for x in by[w])]
    if not training:
        return []
    issues: list[Issue] = []
    held = max((_min(x) for w in training for x in by[w]), default=0.0)
    _, long_cap = week_capacity_parts(
        profile, prefs.days_per_week, session_cap_minutes(profile, d.distance_km, prefs.mountain_day)
    )
    target = TIME_ON_FEET_SHARE * min(d.longest_session_min, long_cap)
    if held < target:
        issues.append(
            Issue(
                "TIME_ON_FEET",
                anchor,
                f"Build the longest session up to about {target:.0f} min before the race (the plan's longest is "
                f"{held:.0f} min): the goal needs that much time on feet.",
            )
        )
    if d.steepness_m_per_km >= MIN_STEEP_M_PER_KM and not prefs.flat_only:
        need = GRADIENT_SHARE * min(d.steepness_m_per_km, d.venue_climb_rate or d.steepness_m_per_km)
        late = training[len(training) // 2 :]
        longs = [
            x
            for w in late
            for x in by[w]
            if is_long(x) and x.get("mountain_mode") not in _NO_CLIMB_MODES and float(x.get("distance_km") or 0) > 0
        ]
        best = max((float(x.get("elevation_gain_m") or 0) / float(x["distance_km"]) for x in longs), default=need)
        if longs and best < need:
            issues.append(
                Issue(
                    "LONG_RUN_GRADIENT",
                    anchor,
                    f"Give the late long runs about {need:.0f} m D+/km of climbing (the steepest now climbs {best:.0f}): "
                    f"the course needs it.",
                )
            )
    if profile.allows_intensity:
        recent = training[-LATE_WEEKS:]
        work = [
            x
            for w in recent
            for x in by[w]
            if is_hard(x)
            or (x.get("type") in ("Easy", "Long Run") and float(x.get("elevation_gain_m") or 0) > 0)
            or (_is_me(x) and _climbs(x))  # weighted climbing is the specific work for an athlete without hills
        ]
        if not work:
            issues.append(
                Issue(
                    "SPECIFICITY_LATE",
                    anchor,
                    "Add hard or climbing work in the last build weeks: the course needs race-specific work.",
                )
            )
    return issues


def lint_weeks(
    workouts: list[dict[str, Any]], weeks: set[int], profile: TierProfile, prefs: Prefs | None = None
) -> list[Issue]:
    found = [i for wk in sorted(weeks) for i in lint_week(workouts, wk, profile, prefs)]
    return found + _specificity(workouts, weeks, profile, prefs)
