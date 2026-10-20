"""Reliability scorecard: does a generated plan hold up against the goal it was built for?

Runs the rule-based path (no Gemini, no network, no database) over a fixed matrix of athlete x race x goal
x training venue and checks, per scenario:
  1. no hard doctrine rule is broken (spacing, adjacency, session length, the athlete's long-run day/days);
  2. a plan that breaks a capacity rule (long-run share, back-to-back, recovery cadence, progression) or
     misses the goal's time-on-feet or specificity demands is one feasibility called unsupported; the one
     exception is the mountain Long Run minimum, which may break long-run share / recovery cadence when
     feasibility lists the lever `fewer_mountain_minimum`;
  3. the verdict agrees with the athlete's capacity (four days or fewer is never `supported` for a 100K).
The model path is judged separately (retry hit-rate and coach review on throwaway plans). Usage:
    python scripts/plan_reliability.py        # prints a table, exit 1 on any failure
"""

import asyncio
import json
import sys
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import settings  # noqa: E402
from services import goal_demands, goal_feasibility, plan_lint  # noqa: E402
from services.athlete_tier import get_profile  # noqa: E402
from services.plan_generator import PlanGenerator  # noqa: E402
from services.training_mountains import long_run_climb_rate  # noqa: E402

PROFILE = {
    "max_hr": 185,
    "resting_hr": 55,
    "aet_hr": 145,
    "ant_hr": 168,
    "zone2_pace_min": "6:30",
    "zone2_pace_max": "5:45",
}
# name: (current km/week, preferred days, long-run day, days per week)
ATHLETES = {
    "65km 6d": (65, ["Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], "Sunday", 6),
    "40km 4d": (40, ["Tuesday", "Thursday", "Saturday", "Sunday"], "Sunday", 4),
    "25km 3d": (25, ["Tuesday", "Saturday", "Sunday"], "Sunday", 3),
    "100km 6d": (100, None, "Saturday", 6),
}
# name: (distance km, gain m, cutoff h, time target h); VHT 50K and 100K
RACES = {"50K": (56.4, 2946, 12.0, 9.0), "100K": (104.2, 5533, 29.0, 14.67)}
START = date(2026, 10, 19)  # a Monday, fixed: the plan must not depend on the day the scorecard runs
MOUNTAIN = "nui_dinh"  # 60 m D+/km, minimum long run 180 min
MOUNTAIN_MIN = 180
HARD_RULES = {"ME_SPACING", "HARD_ADJACENT", "SESSION_TOO_LONG", "LONG_RUN_DAY", "DAYS_SHORT"}
# A plan the athlete's week cannot hold is best effort: feasibility says so, and these may then appear.
CAPACITY_CODES = {"LONG_SHARE", "BACK_TO_BACK", "RECOVERY_DUE", "VOLUME_JUMP", "VERT_JUMP", "LONG_RUN_JUMP"}
MOUNTAIN_MINIMUM_CODES = {
    "LONG_SHARE",
    "RECOVERY_DUE",
    "VOLUME_JUMP",
    "VERT_JUMP",
}  # the 180-min mountain long run (owner-kept, #142)
DEMAND_CODES = {"TIME_ON_FEET", "SPECIFICITY_LATE"}


@dataclass(frozen=True)
class Scenario:
    name: str
    athlete: str
    race: str
    goal: str  # finish | time
    venue: str  # flat | mountain
    weeks: int = 26


@dataclass
class Result:
    scenario: Scenario
    tier: str
    verdict: str
    issues: list[str]
    levers: tuple[str, ...]
    failures: list[str] = field(default_factory=list)


def _scenarios() -> list[Scenario]:
    out = []
    for a in ATHLETES:
        for r in RACES:
            for g in ("finish", "time"):
                for v in ("flat", "mountain"):
                    out.append(Scenario(f"{a} | {r} | {g} | {v}", a, r, g, v))
    out.append(Scenario("40km 4d | 100K | finish | flat | short runway", "40km 4d", "100K", "finish", "flat", 8))
    return out


SCENARIOS = _scenarios()


def run(s: Scenario) -> Result:
    km, days, long_day, dpw = ATHLETES[s.athlete]
    dist, gain, cutoff, target = RACES[s.race]
    target_h = target if s.goal == "time" else None
    mountain = s.venue == "mountain"
    race_info = {
        "name": f"VHT {s.race}",
        "date": (START + timedelta(weeks=s.weeks - 2, days=5)).isoformat(),  # Saturday of the race week
        "plan_start_date": START.isoformat(),
        "terrain": "trail",
        "course_distance_km": dist,
        "course_elevation_gain_m": gain,
        "goal_type": "time" if target_h else "finish",
        "target_time_hours": target_h,
        "preferred_days": days,
        "long_run_day": long_day,
        "days_per_week": dpw,
        "training_environment": "flat",
        "training_mountain": MOUNTAIN if mountain else None,
        "mountain_days": json.dumps(["Saturday", "Sunday"]) if mountain else None,
        "mountain_min_minutes": MOUNTAIN_MIN if mountain else None,
    }
    profile = {**PROFILE, "current_weekly_km": float(km)}
    saved = (settings.PLAN_DEMANDS_ENABLED, settings.PLAN_LINT_ENABLED)
    settings.PLAN_DEMANDS_ENABLED, settings.PLAN_LINT_ENABLED = True, False  # lint reads the DB; run it below
    try:
        workouts, tier = asyncio.run(
            PlanGenerator.generate_plan_workouts(
                plan_id=0,
                user_profile=profile,
                race_info=race_info,
                total_weeks=s.weeks,
                api_key=None,
                cutoff_time_hours=cutoff,
                block_number=1,
                weeks_per_block=s.weeks,
            )
        )
    finally:
        settings.PLAN_DEMANDS_ENABLED, settings.PLAN_LINT_ENABLED = saved
    prof = get_profile(tier)
    venue_rate = long_run_climb_rate(MOUNTAIN) if mountain else None
    demands = goal_demands.compute(dist, gain, target_h, cutoff, venue_climb_rate=venue_rate)
    prefs = plan_lint.Prefs(long_run_day=long_day, days_per_week=dpw, demands=demands, flat_only=not mountain)
    found = plan_lint.lint_weeks(workouts, {w["week_number"] for w in workouts}, prof, prefs)
    codes = {i.code for i in found}
    flat_pace = PlanGenerator.flat_zone2_pace(profile, race_info["goal_type"], tier) or 6.0
    feas = goal_feasibility.assess(
        demands,
        prof,
        dpw,
        flat_pace,
        float(km),
        float(s.weeks),
        False,
        mountain_min_minutes=MOUNTAIN_MIN if mountain else None,
        flat_only=not mountain,
    )
    result = Result(s, tier, feas.verdict, sorted(codes), feas.levers)
    if codes & HARD_RULES:
        result.failures.append(f"hard rules broken: {sorted(codes & HARD_RULES)}")
    if feas.verdict != "unsupported":
        allowed = MOUNTAIN_MINIMUM_CODES if mountain and "fewer_mountain_minimum" in feas.levers else set()
        if loose := (codes & CAPACITY_CODES) - allowed:
            result.failures.append(f"{sorted(loose)} on a goal called {feas.verdict}")
        if codes & DEMAND_CODES:
            result.failures.append(f"{sorted(codes & DEMAND_CODES)} missed on a goal called {feas.verdict}")
    if dpw <= 4 and s.race == "100K" and feas.verdict == "supported":
        result.failures.append("a plan of four days or fewer called supported for a 100K")
    return result


def main() -> int:
    failed = 0
    print(f"{'scenario':58} {'tier':12} {'verdict':12} issues")
    for s in SCENARIOS:
        r = run(s)
        failed += bool(r.failures)
        print(f"{s.name:58} {r.tier:12} {r.verdict:12} {','.join(r.issues) or '-'}")
        for f in r.failures:
            print(f"    FAIL {f}")
    print(f"\n{len(SCENARIOS) - failed}/{len(SCENARIOS)} scenarios pass")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
