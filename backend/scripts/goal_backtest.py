"""Launch gate for LLM goal estimation (docs/superpowers/specs/2026-09-26-llm-goal-estimation-design.md).

  python scripts/golden_eval.py compare --service goal        # or run this file directly
  python scripts/goal_backtest.py [--limit 50] [--no-llm]

For every athlete with 2+ finished trail results in race_results: hold out the latest
finish and estimate it from the results dated before it only. Watch, block and profile
data are left out (we don't have them as they were back then), and the target race's
field curve excludes the held-out year. Three estimators are compared on the same cases:

  old   - the pre-LLM engine: one reference (the most relevant prior result), physics A/B/C
  rules - the new rules tier: median of all anchors
  llm   - the Gemini judge (skipped with --no-llm or without GEMINI_API_KEY)

Metrics: A-C hit rate (actual finish between ambitious and safe) and median |B - actual| %,
overall and by confidence. Ship when llm >= old on both. Writes tests/golden/report_goal.md.
Point DATABASE_URL at a copy of production data; athletes' race history goes to Gemini
exactly as it does in the product.
"""

import argparse
import os
import statistics
import sys
from datetime import date
from typing import Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REPORT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests", "golden", "report_goal.md")


def score(goals: dict[str, float] | None, actual_mins: float) -> dict[str, Any] | None:
    """Hit = actual within [a, c]; error = |b - actual| / actual."""
    if not goals:
        return None
    return {"hit": goals["a"] <= actual_mins <= goals["c"], "error": abs(goals["b"] - actual_mins) / actual_mins}


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    scored = [r for r in rows if r]
    if not scored:
        return {"n": 0, "hit_rate": None, "median_error": None}
    return {
        "n": len(scored),
        "hit_rate": sum(r["hit"] for r in scored) / len(scored),
        "median_error": statistics.median(r["error"] for r in scored),
    }


def passes_gate(old: dict[str, Any], llm: dict[str, Any]) -> bool:
    if not old["n"] or not llm["n"]:
        return False
    return llm["hit_rate"] >= old["hit_rate"] and llm["median_error"] <= old["median_error"]


def old_engine(target: dict[str, Any], prior: list[dict[str, Any]], as_of: date) -> dict[str, float] | None:
    from services.goal_anchors import resolve_course, select_anchor_results
    from services.race_estimator import AMBITIOUS_FACTOR, SAFE_FACTOR, RaceEstimator

    picked = select_anchor_results(prior, target["distance_km"], as_of)
    if not picked:
        return None
    ref = picked[0]
    ref_course = resolve_course(ref["race_name"], ref["distance_km"], ref.get("elevation_gain_m"))
    estimate = RaceEstimator.estimate(
        distance_km=target["distance_km"],
        elevation_gain_m=target["elevation_gain_m"],
        reference={
            "distance_km": ref["distance_km"],
            "elevation_gain_m": ref.get("elevation_gain_m") or 0.0,
            "finish_time_mins": ref["finish_time_sec"] / 60,
            "terrain_tags": ref_course["terrain"] or None,
            "checkpoints": ref_course["checkpoints"],
        },
        terrain_tags=target["terrain"] or None,
        target_checkpoints=target["checkpoints"],
    )
    b = estimate["predicted_time_mins"]
    return {"a": b * AMBITIOUS_FACTOR, "b": b, "c": b * SAFE_FACTOR}


def cases(limit: int | None) -> list[tuple[int, dict[str, Any], list[dict[str, Any]]]]:
    from sqlalchemy import text

    from db import engine
    from services import race_history

    with engine.connect() as conn:
        users = [
            row[0]
            for row in conn.execute(
                text("""
                SELECT user_id FROM race_results
                WHERE discipline = 'trail' AND NOT is_dnf AND finish_time_sec IS NOT NULL AND selected
                GROUP BY user_id HAVING COUNT(*) >= 2 ORDER BY user_id
            """)
            )
        ]
    out = []
    for uid in users[:limit] if limit else users:
        rows = [r for r in race_history._dedupe(race_history.list_results(uid, False)) if not r.get("hidden")]
        trail = [r for r in rows if r["discipline"] == "trail" and not r["is_dnf"] and r["finish_time_sec"]]
        if len(trail) < 2:
            continue
        held = trail[0]  # newest first
        prior = [r for r in rows if r["race_date"] < held["race_date"]]
        if prior:
            out.append((uid, held, prior))
    return out


def run(limit: int | None = None, use_llm: bool = True) -> dict[str, Any]:
    from config import settings
    from services import goal_anchors, goal_context, goal_judge

    use_llm = use_llm and bool(settings.GEMINI_API_KEY)
    results: dict[str, list[dict[str, Any]]] = {"old": [], "rules": [], "llm": []}
    by_confidence: dict[str, list[dict[str, Any]]] = {}
    for uid, held, prior in cases(limit):
        as_of = date.fromisoformat(held["race_date"][:10])
        target = goal_anchors.resolve_course(
            held["race_name"], held["distance_km"], held.get("elevation_gain_m"), before_year=as_of.year
        )
        actual = held["finish_time_sec"] / 60
        anchors = goal_anchors.compute_anchors(target, prior, as_of=as_of)
        results["old"].append(score(old_engine(target, prior, as_of), actual))
        rules = goal_judge.deterministic(anchors, None)
        results["rules"].append(score(rules["goals"] if rules else None, actual))
        if use_llm:
            ctx = goal_context.gather(user=None, target=target, race_date=held["race_date"], extra_results=prior)
            judged = goal_judge.assess(ctx.prompt, anchors, api_key=settings.GEMINI_API_KEY, llm_enabled=True)
            scored = score(judged["goals"] if judged else None, actual)
            results["llm"].append(scored)
            if judged:
                by_confidence.setdefault(judged["confidence"], []).append(scored)
        print(f"user {uid}: {held['race_name'][:40]} actual {actual:.0f} min, {len(anchors)} anchors")

    summary = {name: summarize(rows) for name, rows in results.items()}
    summary["llm_by_confidence"] = {k: summarize(v) for k, v in by_confidence.items()}
    summary["gate"] = passes_gate(summary["old"], summary["llm"]) if use_llm else None
    write_report(summary)
    return summary


def _fmt(s: dict[str, Any]) -> str:
    if not s["n"]:
        return "| 0 | – | – |"
    return f"| {s['n']} | {s['hit_rate']:.0%} | {s['median_error']:.1%} |"


def write_report(summary: dict[str, Any]) -> None:
    lines = [
        "# Goal estimation backtest",
        "",
        "Latest trail finish held out per athlete, estimated from earlier results only.",
        "",
        "| Estimator | Cases | A–C hit rate | Median abs error of B |",
        "|---|---|---|---|",
    ]
    for name in ("old", "rules", "llm"):
        lines.append(f"| {name} {_fmt(summary[name])}")
    if summary["llm_by_confidence"]:
        lines += [
            "",
            "## LLM by confidence",
            "",
            "| Confidence | Cases | A–C hit rate | Median abs error of B |",
            "|---|---|---|---|",
        ]
        for conf, s in sorted(summary["llm_by_confidence"].items()):
            lines.append(f"| {conf} {_fmt(s)}")
    gate = summary["gate"]
    lines += ["", f"**Gate:** {'PASS' if gate else 'FAIL' if gate is False else 'not run (no LLM)'}"]
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--no-llm", action="store_true")
    args = parser.parse_args()
    run(args.limit, use_llm=not args.no_llm)


if __name__ == "__main__":
    main()
