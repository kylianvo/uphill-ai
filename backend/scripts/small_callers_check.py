"""Side-by-side check for the small Claude callers (PAID, cents): runs week brief or coach nudge on N synthetic inputs
and prints how many came back usable and the latency.

    python scripts/small_callers_check.py --feature week_brief --provider claude --thinking off
    python scripts/small_callers_check.py --feature coach_nudge --provider gemini

Usable means: week brief returned {why, benefits, watch}; nudge came from the model (passed grounded()), not the
rule-based fallback.
"""

import argparse
import asyncio
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import settings  # noqa: E402
from services import claude_llm, coach_nudge, week_brief  # noqa: E402

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _week(n: int, km: int) -> list[dict]:
    kinds = ["Easy", "Intervals", "Rest", "Easy", "Tempo", "Long Run", "Recovery"]
    return [
        {"week_number": n, "day_of_week": d, "type": t, "title": t, "duration_minutes": 0 if t == "Rest" else 40 + km}
        for d, t in zip(DAYS, kinds, strict=True)
    ]


def _nudge_facts(i: int) -> dict:
    return {
        "current_week": 3 + i,
        "total_weeks": 16,
        "phase": ["Base", "Build", "Peak"][i % 3],
        "days_to_race": 90 - 7 * i,
        "last_week": {"planned": 6, "done": 6 - i % 3, "adherence": round((6 - i % 3) / 6, 2)},
        "consistent_weeks": i % 4,
        "milestones_just_done": [{"key": "first_long_run_2h", "week": 2 + i}] if i % 2 else [],
        "next_session": {"day": DAYS[i % 7], "title": "Long Run", "minutes": 90 + 10 * i},
        "readiness_flag": None,
        "feasibility_verdict": "supported",
        "plan_supported": True,
        "path": None,
    }


async def _one(feature: str, i: int) -> bool:
    if feature == "coach_nudge":
        out = await coach_nudge.nudge(_nudge_facts(i), ["en", "vi"][i % 2], api_key=settings.GEMINI_API_KEY)
        return bool(out) and out["source"] == "model"
    out = await week_brief.generate_week_brief(
        race_info={"name": "VMM 70K", "terrain": "trail"},
        block_context="Build block, weeks 5-8",
        week_number=5 + i % 3,
        workouts=_week(5 + i % 3, 10 + i),
        prev_workouts=_week(4 + i % 3, 5 + i),
        decision_log=[f"Week {4 + i % 3} was {70 + 3 * i}% complete.", "Long run moved to Sunday."],
        api_key=settings.GEMINI_API_KEY,
    )
    return bool(out) and bool(out.get("why"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--feature", choices=["week_brief", "coach_nudge"], required=True)
    ap.add_argument("--provider", choices=["claude", "gemini"], default="claude")
    ap.add_argument("--thinking", choices=["on", "off"], default=None, help="override the call site's thinking setting")
    ap.add_argument("--n", type=int, default=10)
    args = ap.parse_args()
    flag = "WEEK_BRIEF_LLM_PROVIDER" if args.feature == "week_brief" else "COACH_NUDGE_LLM_PROVIDER"
    setattr(settings, flag, args.provider)
    if args.thinking:
        real = claude_llm.generate
        claude_llm.generate = lambda *a, **kw: real(*a, **{**kw, "thinking": args.thinking == "on"})
    usable, seconds = 0, []
    for i in range(args.n):
        start = time.monotonic()
        ok = asyncio.run(_one(args.feature, i))
        seconds.append(time.monotonic() - start)
        usable += ok
        print(f"{i}: {'usable' if ok else 'NOT usable'} {seconds[-1]:.1f}s")
    print(
        f"{args.feature} {args.provider} thinking={args.thinking or 'site'} usable={usable}/{args.n} p50={statistics.median(seconds):.1f}s"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
