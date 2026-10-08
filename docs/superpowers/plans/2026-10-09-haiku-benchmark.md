# Haiku 5.5 vs Gemini Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Measure, on our own golden set, whether Claude Haiku 5.5 matches Gemini 3.8 Flash's quality on the Goal Determiner while being faster and cheaper, so the model decision rests on data.

**Architecture:** A standalone script, `backend/scripts/model_benchmark.py`, replays every `tests/golden/goal_judge/` fixture through both models with the exact production prompt (`goal_judge.build_prompt`) and the same output schema (`goal_judge.GoalOutput`), several times each. It scores every answer with the production guardrails (`goal_judge.validate`) and against the committed reference answer (`fixture_*.ref.json`), and writes a markdown report with latency, acceptance rate, agreement and cost per call. Nothing in the request path changes: the benchmark is offline, and `anthropic` goes into `requirements-dev.txt` only.

**Tech Stack:** Python 3.12, `google-genai` (existing), `anthropic` 1.x Python SDK (`client.messages.parse(..., output_format=GoalOutput)`), Pydantic, pytest.

## Global Constraints

- Production stays on Gemini. Switching any feature to Claude is a separate decision after this report, and goes through `.claude/skills/llm-change-process/SKILL.md`.
- Same prompt, same schema for both models. No prompt tuning for either side in this plan.
- Claude model ID `claude-haiku-5-5`, `output_config={"effort": "low"}` (Haiku 5.5 thinks by default at `medium`; `low` is the latency-oriented setting). No `temperature`: non-default sampling parameters return a 400 on Haiku 5.5. Check `stop_reason == "refusal"` before reading output (Haiku has no server-side refusal fallback).
- Gemini side mirrors `goal_judge._call_gemini`: `settings.GEMINI_MODEL`, JSON schema `GoalOutput`, `temperature=0.0`, `thinking_level=settings.GEMINI_THINKING_LEVEL`.
- Prices (USD per 1M tokens, input/output): Gemini 3.8 Flash 0.75 / 3.75 until 2026-12-31, then 1.50 / 7.50 (`config.DEFAULT_LLM_PRICES_USD_PER_M`; Gemini output includes thinking tokens); Claude Haiku 5.5 0.10 / 0.50 for prompts up to 100K tokens.
- Unit tests make no network calls. Live runs need `GEMINI_API_KEY` in `backend/.env` and `ANTHROPIC_API_KEY` in the environment; never commit either.
- Every live run spends real money; it is small (12 fixtures × 3 repeats × 2 models = 72 calls), but get the user's go-ahead before running.

## File Structure

- Create `backend/scripts/model_benchmark.py`: engines, scoring, summary, report, CLI.
- Create `backend/tests/unit/test_model_benchmark.py`: scoring and summary, with fake answers.
- Modify `backend/requirements-dev.txt`: add `anthropic`.
- Output (committed): `backend/tests/golden/benchmark_goal_judge.md`.

---

### Task 1: Scoring and summary (pure functions)

**Files:**
- Create: `backend/scripts/model_benchmark.py`
- Create: `backend/tests/unit/test_model_benchmark.py`

**Interfaces:**
- Produces:
  - `score(raw_json: str, fixture: dict, ref: dict | None) -> dict` → `{"parsed": bool, "accepted": bool, "errors": list[str], "b_vs_ref_pct": float | None}`
  - `summarize(rows: list[dict]) -> dict[str, dict]` where each row is `{"engine": str, "seconds": float, "input_tokens": int, "output_tokens": int, **score(...)}`; result per engine: `{"calls", "parsed_rate", "accepted_rate", "p50_s", "p95_s", "median_b_vs_ref_pct", "mean_input_tokens", "mean_output_tokens", "usd_per_call"}`
  - `PRICES: dict[str, tuple[float, float]]`, keys `"gemini"`, `"haiku"`.

- [ ] **Step 1: Write the failing tests** (`tests/unit/test_model_benchmark.py`)

```python
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts import model_benchmark  # noqa: E402

FIXTURE = {
    "lang": "en",
    "cutoff_mins": 700,
    "context": {"race": {"field": {}}},
    "anchors": [{"id": "r1", "minutes": 560}],
}
REF = {"output": {"goals": {"a": 535.0, "b": 565.0, "c": 595.0}}}


def _answer(a=540, b=570, c=600, bullets=3, anchor_id="r1"):
    return json.dumps(
        {
            "goals": {"a": a, "b": b, "c": c},
            "confidence": "medium",
            "reasoning": ["x"] * bullets,
            "anchors_weighted": [{"id": anchor_id, "weight": 1.0}],
            "missing": [],
        }
    )


def test_score_accepts_a_valid_answer_and_measures_distance_to_ref():
    result = model_benchmark.score(_answer(), FIXTURE, REF)
    assert result["parsed"] and result["accepted"]
    assert result["errors"] == []
    assert round(result["b_vs_ref_pct"], 2) == 0.88  # |570 - 565| / 565


def test_score_reports_guardrail_violations():
    result = model_benchmark.score(_answer(a=600, b=570, c=540), FIXTURE, REF)
    assert result["parsed"] and not result["accepted"]
    assert "goals must satisfy a < b < c" in result["errors"]


def test_score_handles_unparseable_output():
    result = model_benchmark.score("not json", FIXTURE, REF)
    assert result == {"parsed": False, "accepted": False, "errors": ["unparseable"], "b_vs_ref_pct": None}


def test_summarize_per_engine():
    rows = [
        {"engine": "haiku", "seconds": s, "input_tokens": 2000, "output_tokens": 400,
         "parsed": True, "accepted": ok, "errors": [], "b_vs_ref_pct": 1.0}
        for s, ok in [(1.0, True), (2.0, True), (3.0, False)]
    ]
    summary = model_benchmark.summarize(rows)["haiku"]
    assert summary["calls"] == 3
    assert summary["p50_s"] == 2.0
    assert round(summary["accepted_rate"], 3) == 0.667
    # 2000 * 0.10 / 1e6 + 400 * 0.50 / 1e6
    assert round(summary["usd_per_call"], 6) == 0.0004
```

- [ ] **Step 2: Run to verify they fail**

Run: `pytest tests/unit/test_model_benchmark.py -q`
Expected: FAIL with `ImportError: cannot import name 'model_benchmark'`

- [ ] **Step 3: Implement** (`scripts/model_benchmark.py`, first part)

```python
"""Benchmark Claude Haiku 5.5 against Gemini on the goal_judge golden set.

  python scripts/model_benchmark.py --repeats 3

Same production prompt and schema for both models; writes
tests/golden/benchmark_goal_judge.md. Needs GEMINI_API_KEY (backend/.env) and
ANTHROPIC_API_KEY. Offline tool: nothing in the request path imports it.
"""

import json
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
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/unit/test_model_benchmark.py -q`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add backend/scripts/model_benchmark.py backend/tests/unit/test_model_benchmark.py
git commit -m "test(bench): scoring and summary for the model benchmark"
```

---

### Task 2: Model calls, report and CLI

**Files:**
- Modify: `backend/scripts/model_benchmark.py`
- Modify: `backend/requirements-dev.txt`

**Interfaces:**
- Consumes: `score`, `summarize`, `PRICES` (Task 1); `goal_judge.build_prompt(context, anchors, lang)`.
- Produces: `call_gemini(prompt: str) -> tuple[str, int, int]` and `call_haiku(prompt: str) -> tuple[str, int, int]` returning `(raw_json, input_tokens, output_tokens)`; `render_report(summary, rows) -> str`; CLI `--repeats N` (default 3).

- [ ] **Step 1: Add the SDK for the benchmark only**

Run: `pip install "anthropic>=1.12,<2"` and append `anthropic>=1.12,<2` to `requirements-dev.txt`. Do **not** add it to `requirements.txt` (production image is unchanged).

- [ ] **Step 2: Implement the calls, report and CLI** (append to `scripts/model_benchmark.py`)

```python
import argparse
import glob
import os
import time

from config import settings

GOLDEN_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests", "golden")


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
        ref = json.load(open(ref_path)) if os.path.exists(ref_path) else None
        out.append((os.path.basename(path), json.load(open(path)), ref))
    return out


def render_report(summary: dict[str, dict], rows: list[dict]) -> str:
    lines = ["# Goal judge: Gemini vs Haiku 5.5", "", "| Metric | " + " | ".join(summary) + " |", "|---|" + "---|" * len(summary)]
    for key in ("calls", "parsed_rate", "accepted_rate", "p50_s", "p95_s", "median_b_vs_ref_pct",
                "mean_input_tokens", "mean_output_tokens", "usd_per_call"):
        cells = []
        for engine in summary:
            v = summary[engine][key]
            cells.append("—" if v is None else (f"{v:.6f}" if key == "usd_per_call" else f"{v:.2f}" if isinstance(v, float) else str(v)))
        lines.append(f"| {key} | " + " | ".join(cells) + " |")
    lines += ["", "## Rejected or failed answers", ""]
    for r in rows:
        if not r["accepted"]:
            lines.append(f"- {r['engine']} / {r['fixture']}: {'; '.join(r['errors'])}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()

    rows: list[dict] = []
    for name, fixture, ref in _fixtures():
        prompt = goal_judge.build_prompt(fixture["context"], fixture["anchors"], fixture.get("lang", "en"))
        for _ in range(args.repeats):
            for engine, call in ENGINES.items():
                start = time.perf_counter()
                try:
                    raw, in_tok, out_tok = call(prompt)
                    result = score(raw, fixture, ref)
                except Exception as exc:  # network, quota, refusal
                    raw, in_tok, out_tok = "", 0, 0
                    result = {"parsed": False, "accepted": False, "errors": [f"call failed: {type(exc).__name__}"], "b_vs_ref_pct": None}
                rows.append({"engine": engine, "fixture": name, "seconds": time.perf_counter() - start,
                             "input_tokens": in_tok, "output_tokens": out_tok, **result})
                print(f"{engine:6} {name:40} {rows[-1]['seconds']:5.1f}s accepted={result['accepted']}")

    report = render_report(summarize(rows), rows)
    out_path = os.path.join(GOLDEN_DIR, "benchmark_goal_judge.md")
    with open(out_path, "w") as f:
        f.write(report)
    print(report)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
```

Move the new imports to the top of the file with the others, then run `ruff check --fix scripts/model_benchmark.py && ruff format scripts/model_benchmark.py`.

- [ ] **Step 3: Add a report test** (append to `tests/unit/test_model_benchmark.py`)

```python
def test_render_report_lists_metrics_and_rejections():
    rows = [
        {"engine": "gemini", "fixture": "fixture_a.json", "seconds": 4.0, "input_tokens": 2000, "output_tokens": 600,
         "parsed": True, "accepted": False, "errors": ["give 3 to 5 reasoning bullets"], "b_vs_ref_pct": 2.0},
    ]
    report = model_benchmark.render_report(model_benchmark.summarize(rows), rows)
    assert "| p50_s | 4.00 |" in report
    assert "gemini / fixture_a.json: give 3 to 5 reasoning bullets" in report
```

- [ ] **Step 4: Run unit tests**

Run: `pytest tests/unit/test_model_benchmark.py -q && pytest tests/unit -q`
Expected: all PASS

- [ ] **Step 5: Smoke one live call per model** (ask the user first; costs well under $0.01)

Run: `python -c "from scripts.model_benchmark import *; import json; f=json.load(open('tests/golden/goal_judge/fixture_cutoff_tight.json')); p=goal_judge.build_prompt(f['context'], f['anchors'], 'en'); print(call_gemini(p)[1:]); print(call_haiku(p)[1:])"`
Expected: two `(input_tokens, output_tokens)` tuples, no exception. If `messages.parse` rejects `output_config` alongside `output_format`, read the SDK's `parse` signature (`python -c "import anthropic, inspect; print(inspect.signature(anthropic.Anthropic().messages.parse))"`) and fix the call before going on.

- [ ] **Step 6: Commit**

```bash
git add backend/scripts/model_benchmark.py backend/tests/unit/test_model_benchmark.py backend/requirements-dev.txt
git commit -m "feat(bench): Gemini vs Haiku 5.5 benchmark on the goal_judge golden set"
```

---

### Task 3: Run it and write up the result

**Files:**
- Create: `backend/tests/golden/benchmark_goal_judge.md` (generated)

- [ ] **Step 1: Run the full benchmark** (user's go-ahead; 72 calls)

Run: `python scripts/model_benchmark.py --repeats 3`
Expected: per-call lines, then the report table; `tests/golden/benchmark_goal_judge.md` written.

- [ ] **Step 2: Read the rejected answers** in the report. A rejection that is a schema or ordering failure counts against the model; a failure that is a call error (rate limit, network) gets re-run, not counted.

- [ ] **Step 3: Decide with the user** using this bar, stated in the PR:
  - Haiku's `accepted_rate` ≥ Gemini's, and its `median_b_vs_ref_pct` within 2 points of Gemini's, **and**
  - Haiku's `p50_s` at least 30% lower than Gemini's.
  If all three hold, the next step is a separate plan to move `goal_judge` behind a model switch and run the `goal` hold-out backtest (`python scripts/golden_eval.py compare --service goal`) on Haiku before any production change. If not, record the numbers and stop.

- [ ] **Step 4: Commit and open the PR**

```bash
git add backend/tests/golden/benchmark_goal_judge.md
git commit -m "docs(bench): goal_judge Gemini vs Haiku 5.5 results"
```

## Follow-ups (not in this plan)

- Extend the benchmark to `nutrition` (10 fixtures). Its prompt is built inline in `nutrition_planner` (`services/nutrition_planner.py:159`), so first extract a `build_prompt` function like `goal_judge`'s.
- Coach Chat on Haiku needs the LangChain tool binding swapped (`langchain-anthropic`) and is only worth evaluating if the goal/nutrition results are clearly positive.
