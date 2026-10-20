"""Does the plan deliver the training improvement the Goal Determiner's goals assume?

The Goal Determiner's A/B/C start from the athlete's current-fitness anchors and credit them with
0.25% improvement per week of structured training, capped at 5% (race_estimator
IMPROVEMENT_PER_WEEK / IMPROVEMENT_CAP). That credit is only earned by a structured block: a week
that breaks the doctrine's rules, or sits behind the path to the benchmark peak, does not earn it.

This scores the weeks still ahead (generated weeks by lint, ungenerated weeks by whether the
timeline can still reach the benchmark), converts them to the improvement the plan can actually
deliver, and returns the factor by which the goals must be pushed later so that they never assume
more than that. It assumes the athlete follows the plan; it cannot promise a finish time.
"""

from dataclasses import dataclass, field
from typing import Any

from services import plan_lint, race_readiness
from services.athlete_tier import TierProfile
from services.race_estimator import IMPROVEMENT_CAP, IMPROVEMENT_PER_WEEK

A_SHORTFALL_TOLERANCE = 0.005  # a goal pushed later by under 0.5% still counts as supported


@dataclass(frozen=True)
class Adequacy:
    weeks_assumed: float  # weeks to race: what the goals credit
    weeks_supported: float  # weeks of structured training the plan can actually deliver
    improvement_assumed: float
    improvement_supported: float
    shortfall_factor: float  # >= 1: multiply the goals by this
    adequate_weeks: tuple[int, ...]
    problems: dict[int, list[str]] = field(default_factory=dict)  # week -> issue codes
    reach_ratio: float = 1.0
    note: str = ""

    @property
    def a_supported(self) -> bool:
        return self.shortfall_factor - 1 <= A_SHORTFALL_TOLERANCE


def _improvement(weeks: float) -> float:
    return min(IMPROVEMENT_CAP, max(0.0, weeks) * IMPROVEMENT_PER_WEEK)


def assess(
    workouts: list[dict[str, Any]],
    *,
    total_weeks: int,
    current_week: int,
    weeks_to_race: float | None,
    distance_km: float | None,
    profile: TierProfile,
    prefs: plan_lint.Prefs | None = None,
    flat_pace_min_km: float | None = None,
) -> Adequacy | None:
    """None when there is nothing to judge (no date, no distance, or the race is past)."""
    if weeks_to_race is None or weeks_to_race <= 0 or not distance_km or total_weeks < 4:
        return None
    remaining = max(1, round(weeks_to_race))
    taper = min(race_readiness.TAPER_WEEKS, remaining)
    build_remaining = remaining - taper
    last_build_week = total_weeks - race_readiness.TAPER_WEEKS
    by_week = plan_lint._by_week(workouts)
    generated = [w for w in sorted(by_week) if current_week <= w <= last_build_week][:build_remaining]

    adequate: list[int] = []
    problems: dict[int, list[str]] = {}
    for wk in generated:
        codes = [i.code for i in plan_lint.lint_week(workouts, wk, profile, prefs)]
        r = race_readiness.assess_week(
            workouts,
            wk,
            total_weeks=total_weeks,
            distance_km=distance_km,
            max_prog=profile.max_weekly_progression,
            flat_pace_min_km=flat_pace_min_km,
        )
        if race_readiness.readiness_issue(r, wk, race_readiness.weekly_km(by_week[wk], flat_pace_min_km)):
            codes.append("READINESS_BEHIND")
        if codes:
            problems[wk] = codes
        else:
            adequate.append(wk)

    # Weeks not generated yet earn credit only as far as the timeline can still reach the benchmark.
    ungenerated = max(0, build_remaining - len(generated))
    reach_ratio, note = 1.0, ""
    if ungenerated:
        first = (max(generated) + 1) if generated else current_week
        r = race_readiness.assess_week(
            workouts,
            first,
            total_weeks=total_weeks,
            distance_km=distance_km,
            max_prog=profile.max_weekly_progression,
            flat_pace_min_km=flat_pace_min_km,
        )
        if r and r.status == "at_risk":
            reach_ratio = max(0.0, min(1.0, r.reachable_km / r.peak_lo))
            note = r.message

    weeks_supported = min(float(remaining), len(adequate) + reach_ratio * ungenerated + taper)
    assumed = _improvement(weeks_to_race)
    supported = min(assumed, _improvement(weeks_supported))
    return Adequacy(
        weeks_assumed=weeks_to_race,
        weeks_supported=weeks_supported,
        improvement_assumed=assumed,
        improvement_supported=supported,
        shortfall_factor=(1 - supported) / (1 - assumed),
        adequate_weeks=tuple(adequate),
        problems=problems,
        reach_ratio=reach_ratio,
        note=note,
    )


def adjust_goals(goals: dict[str, float], adequacy: Adequacy | None) -> dict[str, float]:
    """The goals pushed later by exactly the improvement the plan cannot deliver."""
    if not adequacy or adequacy.shortfall_factor <= 1:
        return dict(goals)
    return {k: round(v * adequacy.shortfall_factor, 1) for k, v in goals.items()}


def summary_lines(adequacy: Adequacy | None) -> list[str]:
    """Plain-English facts for the generator and the week brief; empty when the goals are supported."""
    if not adequacy or adequacy.a_supported:
        return []
    lines = [
        f"The goal times assume {adequacy.improvement_assumed * 100:.1f}% improvement from structured training; "
        f"this plan can deliver {adequacy.improvement_supported * 100:.1f}%, so the goals move "
        f"{(adequacy.shortfall_factor - 1) * 100:.1f}% later."
    ]
    if adequacy.problems:
        codes = sorted({c for cs in adequacy.problems.values() for c in cs})
        lines.append(f"Weeks that broke the plan rules or fell behind the path: {', '.join(codes)}. Avoid these.")
    if adequacy.note:
        lines.append(adequacy.note)
    return lines
