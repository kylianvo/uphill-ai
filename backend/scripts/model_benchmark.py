"""Benchmark Claude Haiku 5.5 against Gemini on the goal_judge golden set.

  python scripts/model_benchmark.py --repeats 3

Same production prompt and schema for both models; writes
tests/golden/benchmark_goal_judge.md. Needs GEMINI_API_KEY (backend/.env) and
ANTHROPIC_API_KEY. Offline tool: nothing in the request path imports it.
"""

import statistics

from pydantic import ValidationError

from services import goal_judge

HAIKU_MODEL = "claude-haiku-5-5"
# USD per 1M tokens (input, output). Gemini output includes thinking tokens.
PRICES: dict[str, tuple[float, float]] = {"gemini": (0.75, 3.75), "haiku": (0.10, 0.50)}


def score(raw_json: str, fixture: dict, ref: dict | None) -> dict:
    try:
        output = goal_judge.GoalOutput.model_validate_json(raw_json)
    except (ValidationError, ValueError):
        return {"parsed": False, "accepted": False, "errors": ["unparseable"], "b_vs_ref_pct": None}
    race = fixture["context"].get("race") or {}
    errors = goal_judge.validate(output, fixture["anchors"], race, fixture.get("cutoff_mins"))
    ref_b = (((ref or {}).get("output") or {}).get("goals") or {}).get("b")
    b_vs_ref = abs(output.goals.b - ref_b) / ref_b * 100 if ref_b else None
    return {"parsed": True, "accepted": not errors, "errors": errors, "b_vs_ref_pct": b_vs_ref}


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round(0.95 * (len(ordered) - 1)))]


def summarize(rows: list[dict]) -> dict[str, dict]:
    summary: dict[str, dict] = {}
    for engine in sorted({r["engine"] for r in rows}):
        mine = [r for r in rows if r["engine"] == engine]
        seconds = [r["seconds"] for r in mine]
        devs = [r["b_vs_ref_pct"] for r in mine if r["b_vs_ref_pct"] is not None]
        in_tok = statistics.mean(r["input_tokens"] for r in mine)
        out_tok = statistics.mean(r["output_tokens"] for r in mine)
        price_in, price_out = PRICES[engine]
        summary[engine] = {
            "calls": len(mine),
            "parsed_rate": sum(r["parsed"] for r in mine) / len(mine),
            "accepted_rate": sum(r["accepted"] for r in mine) / len(mine),
            "p50_s": statistics.median(seconds),
            "p95_s": _p95(seconds),
            "median_b_vs_ref_pct": statistics.median(devs) if devs else None,
            "mean_input_tokens": in_tok,
            "mean_output_tokens": out_tok,
            "usd_per_call": (in_tok * price_in + out_tok * price_out) / 1_000_000,
        }
    return summary
