"""Benchmark Claude Haiku 5.5 against Gemini on the goal_judge golden set.

  python scripts/model_benchmark.py --repeats 3

Same production prompt and schema for both models; writes
tests/golden/benchmark_goal_judge.md. Needs GEMINI_API_KEY (backend/.env) and
ANTHROPIC_API_KEY. Offline tool: nothing in the request path imports it.
"""

import argparse
import glob
import json
import os
import statistics
import time

from pydantic import ValidationError

from config import settings
from services import goal_judge

HAIKU_MODEL = "claude-haiku-5-5"
# USD per 1M tokens (input, output). Gemini output includes thinking tokens.
PRICES: dict[str, tuple[float, float]] = {"gemini": (0.75, 3.75), "haiku": (0.10, 0.50)}
GOLDEN_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests", "golden")


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
        tokens_known = all(r["input_tokens"] is not None for r in mine)
        in_tok = statistics.mean(r["input_tokens"] for r in mine) if tokens_known else None
        out_tok = statistics.mean(r["output_tokens"] for r in mine) if tokens_known else None
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
            "usd_per_call": (in_tok * price_in + out_tok * price_out) / 1_000_000 if tokens_known else None,
        }
    return summary


class RefusalError(RuntimeError):
    pass


def call_gemini(prompt: str) -> tuple[str, int, int]:
    """Mirrors goal_judge._call_gemini's config (one attempt, no retry)."""
    from google import genai
    from google.genai import types

    response = genai.Client(api_key=settings.GEMINI_API_KEY).models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=goal_judge.GoalOutput,
            temperature=0.0,
            thinking_config=types.ThinkingConfig(thinking_level=settings.GEMINI_THINKING_LEVEL),
        ),
    )
    usage = response.usage_metadata
    output_tokens = (usage.candidates_token_count or 0) + (usage.thoughts_token_count or 0)
    return response.text, usage.prompt_token_count or 0, output_tokens


def call_haiku(prompt: str) -> tuple[str, int, int]:
    import anthropic

    response = anthropic.Anthropic().messages.parse(
        model=HAIKU_MODEL,
        max_tokens=4096,
        output_config={"effort": "low"},
        output_format=goal_judge.GoalOutput,
        messages=[{"role": "user", "content": prompt}],
    )
    if response.stop_reason == "refusal":
        raise RefusalError("refusal")
    return response.parsed_output.model_dump_json(), response.usage.input_tokens, response.usage.output_tokens


ENGINES = {"gemini": call_gemini, "haiku": call_haiku}


def _fixtures() -> list[tuple[str, dict, dict | None]]:
    out = []
    for path in sorted(glob.glob(os.path.join(GOLDEN_DIR, "goal_judge", "fixture_*.json"))):
        if path.endswith(".ref.json"):
            continue
        ref_path = path[: -len(".json")] + ".ref.json"
        with open(path) as f:
            fixture = json.load(f)
        ref = None
        if os.path.exists(ref_path):
            with open(ref_path) as f:
                ref = json.load(f)
        out.append((os.path.basename(path), fixture, ref))
    return out


def gemini_rows_from_refs(fixtures: list[tuple[str, dict, dict | None]]) -> list[dict]:
    """Gemini side from the committed golden baselines instead of new calls: one clean
    (no-retry) answer per fixture, with its captured latency. Token counts were not saved."""
    rows = []
    for name, fixture, ref in fixtures:
        if not ref or ref.get("engine_used") != "gemini":
            continue
        result = score(json.dumps(ref["output"]), fixture, None)
        rows.append(
            {
                "engine": "gemini",
                "fixture": name,
                "seconds": ref["latency_s"],
                "input_tokens": None,
                "output_tokens": None,
                **result,
            }
        )
    return rows


def _cell(key: str, value) -> str:
    if value is None:
        return "—"
    if key == "usd_per_call":
        return f"{value:.6f}"
    return f"{value:.2f}" if isinstance(value, float) else str(value)


def render_report(summary: dict[str, dict], rows: list[dict]) -> str:
    engines = list(summary)
    lines = [
        "# Goal judge: Gemini vs Haiku 5.5",
        "",
        "| Metric | " + " | ".join(engines) + " |",
        "|---|" + "---|" * len(engines),
    ]
    for key in (
        "calls",
        "parsed_rate",
        "accepted_rate",
        "p50_s",
        "p95_s",
        "median_b_vs_ref_pct",
        "mean_input_tokens",
        "mean_output_tokens",
        "usd_per_call",
    ):
        lines.append(f"| {key} | " + " | ".join(_cell(key, summary[e][key]) for e in engines) + " |")
    lines += ["", "## Rejected or failed answers", ""]
    for r in rows:
        if not r["accepted"]:
            lines.append(f"- {r['engine']} / {r['fixture']}: {'; '.join(r['errors'])}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument(
        "--gemini-from-refs",
        action="store_true",
        help="Score the committed Gemini baselines (*.ref.json) instead of calling Gemini again",
    )
    args = parser.parse_args()

    fixtures = _fixtures()
    engines = {"haiku": call_haiku} if args.gemini_from_refs else ENGINES
    rows: list[dict] = gemini_rows_from_refs(fixtures) if args.gemini_from_refs else []
    for name, fixture, ref in fixtures:
        prompt = goal_judge.build_prompt(fixture["context"], fixture["anchors"], fixture.get("lang", "en"))
        for _ in range(args.repeats):
            for engine, call in engines.items():
                start = time.perf_counter()
                try:
                    raw, in_tok, out_tok = call(prompt)
                    result = score(raw, fixture, ref)
                except Exception as exc:  # network, quota, refusal
                    in_tok, out_tok = 0, 0
                    result = {
                        "parsed": False,
                        "accepted": False,
                        "errors": [f"call failed: {type(exc).__name__}"],
                        "b_vs_ref_pct": None,
                    }
                rows.append(
                    {
                        "engine": engine,
                        "fixture": name,
                        "seconds": time.perf_counter() - start,
                        "input_tokens": in_tok,
                        "output_tokens": out_tok,
                        **result,
                    }
                )
                print(f"{engine:6} {name:40} {rows[-1]['seconds']:5.1f}s accepted={result['accepted']}")

    report = render_report(summarize(rows), rows)
    out_path = os.path.join(GOLDEN_DIR, "benchmark_goal_judge.md")
    with open(out_path, "w") as f:
        f.write(report)
    print(report)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
