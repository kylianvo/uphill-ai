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
from services import b_race, goal_demands, goal_feasibility, plan_lint, ultra_rules  # noqa: E402
from services import plan_generator as plan_generator_module  # noqa: E402
from services.athlete_tier import for_race, get_profile  # noqa: E402
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
HARD_RULES = {"ME_SPACING", "HARD_ADJACENT", "SESSION_TOO_LONG", "LONG_RUN_DAY", "DAYS_SHORT", "HARD_IN_DOWN_WEEK"}
# A plan the athlete's week cannot hold is best effort: feasibility says so, and these may then appear.
CAPACITY_CODES = {"LONG_SHARE", "BACK_TO_BACK", "RECOVERY_DUE", "VOLUME_JUMP", "VERT_JUMP", "LONG_RUN_JUMP"}
MOUNTAIN_MINIMUM_CODES = {
    "LONG_SHARE",
    "RECOVERY_DUE",
    "VOLUME_JUMP",
    "VERT_JUMP",
}  # the 180-min mountain long run (owner-kept, #142)
DEMAND_CODES = {
    "TIME_ON_FEET",
    "SPECIFICITY_LATE",
    "CLIMB_SPECIFICITY",
    "WEEKDAY_SHORT",
    "ULTRA_LADDER",
    "QUALITY_COUNT",
    "VERT_SHORT",
}


@dataclass(frozen=True)
class Scenario:
    name: str
    athlete: str
    race: str
    goal: str  # finish | time
    venue: str  # flat | mountain
    weeks: int = 26
    back_to_back: bool = False  # the athlete's long-day format: a back-to-back weekend for the 6-7 h rungs


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
    out.append(
        Scenario("65km 6d | 100K | time | mountain | back-to-back", "65km 6d", "100K", "time", "mountain", 26, True)
    )
    out.append(Scenario("65km 6d | 100K | time | mountain | 13 weeks", "65km 6d", "100K", "time", "mountain", 13))
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
        "long_day_format": "back_to_back" if s.back_to_back else None,
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
    prof = for_race(get_profile(tier), dist, mountain)  # mountain days: an ultra follows Quang's ladder
    venue_rate = long_run_climb_rate(MOUNTAIN) if mountain else None
    demands = goal_demands.compute(dist, gain, target_h, cutoff, venue_climb_rate=venue_rate)
    prefs = plan_lint.Prefs(
        long_run_day=long_day,
        days_per_week=dpw,
        demands=demands,
        flat_only=not mountain,
        total_weeks=s.weeks,
        race_km=dist,
        mountain_day=mountain,
        quality_gated=True,  # PROFILE's thresholds are estimates (no threshold_source): the AeT gate is on
        back_to_back=s.back_to_back,
        vert_targets=PlanGenerator.vert_targets_for(race_info, demands, s.weeks),
        # as the generator's lint: a short ultra plan opens with ME weeks (2 a week), not Zone 3
        me_first_weeks=ultra_rules.me_first_weeks(s.weeks, False, dist) if prof.allows_me_blocks else frozenset(),
        start_load_minutes=float(km) * (PlanGenerator.flat_zone2_pace(profile, race_info["goal_type"], tier) or 6.0),
    )
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
        mountain_day=mountain,
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


# B-races (services/b_race.py) on "65km 6d | 50K | time | flat": (name, races as (days before A, km, gain), levels)
A_RACE_DAY = START + timedelta(weeks=24, days=5)
B_CASES = [
    ("25K at 6 weeks", [(42, 25, 1000)], ["good"]),
    ("50K at 3 weeks", [(21, 50, 2500)], ["risky"]),
    ("25K at 10 days", [(10, 25, 1000)], ["not_recommended"]),
    ("two 25Ks 2 weeks apart", [(56, 25, 1000), (42, 25, 1000)], ["good", "risky"]),  # the second one stacks
]


def _generate(races: list[dict]) -> list[dict]:
    """The rule-based plan for the B-race athlete, with `races` loaded as the plan's B-races (no database)."""
    saved = (b_race.safe_races_for_plan, plan_generator_module.get_plan_by_id, settings.PLAN_LINT_ENABLED)
    b_race.safe_races_for_plan = lambda plan_id: races
    plan_generator_module.get_plan_by_id = lambda plan_id: {"start_date": START.isoformat()}
    settings.PLAN_LINT_ENABLED = False
    km, days, long_day, dpw = ATHLETES["65km 6d"]
    dist, gain, cutoff, target = RACES["50K"]
    try:
        workouts, _ = asyncio.run(
            PlanGenerator.generate_plan_workouts(
                plan_id=0,
                user_profile={**PROFILE, "current_weekly_km": float(km)},
                race_info={
                    "name": "VHT 50K",
                    "date": A_RACE_DAY.isoformat(),
                    "plan_start_date": START.isoformat(),
                    "terrain": "trail",
                    "course_distance_km": dist,
                    "course_elevation_gain_m": gain,
                    "goal_type": "time",
                    "target_time_hours": target,
                    "preferred_days": days,
                    "long_run_day": long_day,
                    "days_per_week": dpw,
                    "training_environment": "flat",
                },  # fmt: skip
                total_weeks=26,
                api_key=None,
                cutoff_time_hours=cutoff,
                block_number=1,
                weeks_per_block=26,
            )
        )
    finally:
        b_race.safe_races_for_plan, plan_generator_module.get_plan_by_id, settings.PLAN_LINT_ENABLED = saved
    return workouts


def run_b_race(name: str, specs: list[tuple[int, float, float]], levels: list[str], baseline: list[dict]) -> list[str]:
    races, rows, failures = [], [], []
    for i, (days_before, km, gain) in enumerate(specs, 1):
        row = {"id": i, "race_name": f"B{i}", "race_date": (A_RACE_DAY - timedelta(days=days_before)).isoformat(),
               "distance_km": km, "elevation_gain_m": gain, "effort": "race", "kept_against": None}  # fmt: skip
        facts = b_race.PlanFacts(A_RACE_DAY, 56.4, 2946, START, 26, 30.0, 210.0,
                                 tuple(b_race._row_race(r) for r in rows))  # fmt: skip
        level = b_race.assess(b_race._row_race(row), facts).level
        if level != levels[i - 1]:
            failures.append(f"B{i}: level {level}, expected {levels[i - 1]}")
        if level == "not_recommended":
            row = {**row, "effort": "training", "kept_against": "not_recommended"}
        elif level == "risky":
            row = {**row, "kept_against": "risky"}
        rows.append(row)
        races.append(row)
    workouts = _generate(races)
    view = b_race.lint_view(races, START)
    weeks = {w["week_number"] for w in workouts}
    if issues := plan_lint._b_race_issues(workouts, weeks, view):
        failures.append(f"guard broken: {sorted({i.code for i in issues})}")

    def a_taper(ws: list[dict]) -> list[tuple]:
        race_days = {(v["week"], v["day"]) for v in view}  # a B-race inside the taper takes only its own day
        return sorted((w["week_number"], w["day_of_week"], w["type"], w["duration_minutes"])
                      for w in ws if w.get("phase") in ("Taper", "Race Week")
                      and (w["week_number"], w["day_of_week"]) not in race_days)  # fmt: skip

    before = {(wk, d, t): m for wk, d, t, m in a_taper(baseline)}
    after = {(wk, d, t): m for wk, d, t, m in a_taper(workouts)}
    # the taper may get lighter (its long-share fit reacts to the race's minutes), never heavier or reshaped
    if set(after) != set(before) or any(after[k] > before[k] for k in after):
        failures.append("the A-race taper gained load or changed shape")
    print(f"{'B-race | ' + name:58} {'':12} {','.join(levels):12} {len(failures) and 'FAIL' or 'ok'}")
    for f in failures:
        print(f"    FAIL {f}")
    return failures


def main() -> int:
    failed = 0
    print(f"{'scenario':58} {'tier':12} {'verdict':12} issues")
    for s in SCENARIOS:
        r = run(s)
        failed += bool(r.failures)
        print(f"{s.name:58} {r.tier:12} {r.verdict:12} {','.join(r.issues) or '-'}")
        for f in r.failures:
            print(f"    FAIL {f}")
    baseline = _generate([])
    for name, specs, levels in B_CASES:
        failed += bool(run_b_race(name, specs, levels, baseline))
    total = len(SCENARIOS) + len(B_CASES)
    print(f"\n{total - failed}/{total} scenarios pass")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
