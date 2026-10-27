"""Live check of the MODEL path (paid: a handful of Gemini calls; keep the scenario list small).

Generates one week at a time for a few athlete x race scenarios with the real model, the plan lint and its
corrective retry switched on, and reports which engine answered, the lint issues left, and the week's shape.
Complements scripts/plan_reliability.py, which covers the rule-based path. The key comes from the environment
(GEMINI_LIVE_KEY) and is never stored.

    GEMINI_LIVE_KEY=... python scripts/plan_live_check.py [--only substring]
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import settings  # noqa: E402
from services import goal_demands, plan_lint  # noqa: E402
from services.athlete_tier import get_profile  # noqa: E402
from services.plan_generator import PlanGenerator  # noqa: E402

START = date(2026, 10, 19)
PROFILE = {
    "max_hr": 185,
    "resting_hr": 55,
    "aet_hr": 145,
    "ant_hr": 168,
    "zone2_pace_min": "6:30",
    "zone2_pace_max": "5:45",
}
RACES = {"50K": (56.4, 2946, 12.0, 9.0), "100K": (104.2, 5533, 29.0, 14.67)}
SIX = ["Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
FOUR = ["Tuesday", "Thursday", "Saturday", "Sunday"]
THREE = ["Tuesday", "Saturday", "Sunday"]
# name: (km/week, days, long-run day, race, goal, mountain, weeks, week to generate)
SCENARIOS = {
    "65km 6d | 100K time | base wk1": (65, SIX, "Sunday", "100K", "time", None, 13, 1),
    "65km 6d | 100K time | peak wk9": (65, SIX, "Sunday", "100K", "time", None, 13, 9),
    "40km 4d | 50K finish | base wk1": (40, FOUR, "Sunday", "50K", "finish", None, 12, 1),
    "25km 3d | 100K finish | wk1 (infeasible)": (25, THREE, "Sunday", "100K", "finish", None, 13, 1),
    "65km 6d | 100K time | mountain wk1": (65, SIX, "Sunday", "100K", "time", "nui_dinh", 13, 1),
}


async def run(name: str, key: str) -> None:
    km, days, long_day, race, goal, mountain, weeks, week = SCENARIOS[name]
    dist, gain, cutoff, target = RACES[race]
    info = {
        "name": f"VHT {race}", "date": (START + timedelta(weeks=weeks - 2, days=5)).isoformat(),
        "plan_start_date": START.isoformat(), "terrain": "trail", "course_distance_km": dist,
        "course_elevation_gain_m": gain, "goal_type": goal, "target_time_hours": target if goal == "time" else None,
        "preferred_days": days, "long_run_day": long_day, "days_per_week": len(days), "lang": "en",
        "training_environment": "flat", "training_mountain": mountain,
        "mountain_days": json.dumps(["Saturday", "Sunday"]) if mountain else None,
        "mountain_min_minutes": 180 if mountain else None,
    }  # fmt: skip
    from telemetry import rag_attempts_total

    def used(engine: str) -> float:
        return rag_attempts_total.labels(service="plan_generator", engine=engine, status="used")._value.get()

    before = {e: used(e) for e in ("gemini", "gemini_retry")}

    context = None
    if week > 1:
        context = (
            "  Block 8 summary: 4 of 5 sessions done, volume 540 min, long run 190 min.\n  Coach evaluation: on track."
        )
    with (
        patch("services.kb_retrieval.search_scheduler_chunks", return_value=[]),
        patch("services.plan_signals.record_generation", lambda **kw: None),
    ):
        workouts, tier = await PlanGenerator.generate_plan_workouts(
            plan_id=0, user_profile={**PROFILE, "current_weekly_km": float(km)}, race_info=info, total_weeks=weeks,
            api_key=key, cutoff_time_hours=cutoff, block_number=week, weeks_per_block=1, block_context=context,
        )  # fmt: skip
    engines = [e for e in before if used(e) > before[e]] or ["rules"]
    d = goal_demands.compute(dist, gain, target if goal == "time" else None, cutoff)
    prefs = plan_lint.Prefs(
        long_run_day=long_day,
        days_per_week=len(days),
        demands=d,
        flat_only=not mountain,
        total_weeks=weeks,
        race_km=dist,
    )
    issues = plan_lint.lint_weeks(workouts, {w["week_number"] for w in workouts}, get_profile(tier), prefs)
    active = [w for w in workouts if w["type"] != "Rest"]
    longest = max((w["duration_minutes"] for w in active), default=0)
    print(f"{name}\n   engine={','.join(engines) or '?'} tier={tier} sessions={len(active)} minutes={sum(w['duration_minutes'] for w in active):.0f}"
          f" longest={longest:.0f} issues={sorted({i.code for i in issues}) or '-'}")  # fmt: skip
    for w in active:
        print(
            f"     {w['day_of_week'][:3]} {w['type'][:14]:14} {w['duration_minutes']:5.0f}m {w.get('target_zone','')}"
        )


def main() -> int:
    key = os.environ.get("GEMINI_LIVE_KEY")
    if not key:
        sys.exit("Set GEMINI_LIVE_KEY (a Gemini key you are allowed to spend).")
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", default="")
    args = parser.parse_args()
    settings.PLAN_LINT_ENABLED = settings.PLAN_LINT_RETRY = settings.PLAN_DEMANDS_ENABLED = True
    logging.getLogger().setLevel(logging.INFO)
    for name in SCENARIOS:
        if args.only in name:
            asyncio.run(run(name, key))
    return 0


if __name__ == "__main__":
    sys.exit(main())
