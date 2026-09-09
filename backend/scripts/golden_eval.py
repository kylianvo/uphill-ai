"""Golden-set regression eval for the Gemini+KB pipeline.

  python scripts/golden_eval.py capture --service gear      # snapshot today's output as the baseline
  python scripts/golden_eval.py compare --service gear      # re-run and diff against that baseline

Originally a NotebookLM-vs-Gemini bake-off used to decide which engine to ship. That
decision is settled and NotebookLM is gone, so this is now a plain before/after harness:
capture takes a baseline of the CURRENT pipeline, compare re-runs it and reports what moved.
Re-capture deliberately, after you have reviewed a change — a baseline captured from a
regression silently becomes the thing every later run is measured against.

capture saves <fixture>.ref.json next to each fixture. compare writes
tests/golden/report_<service>.md. Requires backend/.env (GEMINI_API_KEY + a distilled KB).

Scheduler attribution: gear/nutrition call _generate_with_gemini directly, but the plan
generator falls back internally (Gemini → reduced-prompt retry → rule-based), so scheduler
output is attributed to whichever tier's Prometheus "used" counter moved. A run that fell
through to rule-based is flagged loudly — it is not a valid baseline or comparison row.
"""

import argparse
import asyncio
import glob
import json
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings  # noqa: E402

GOLDEN_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests", "golden")


def _fixtures(service: str) -> list[str]:
    # "fixture_*.json" also matches this script's own output: a captured baseline is
    # named "<fixture>.ref.json", which itself starts with "fixture_" and ends in
    # ".json". Without the exclusion, capture's OWN saved output becomes an input on the
    # next run -- it gets loaded as a fixture, has none of the {"user_profile", ...}
    # keys a real fixture has, and crashes with KeyError. Excluding *.ref.json makes a
    # second capture over the same directory safe.
    paths = sorted(
        p for p in glob.glob(os.path.join(GOLDEN_DIR, service, "fixture_*.json")) if not p.endswith(".ref.json")
    )
    if not paths:
        sys.exit(f"No fixtures in tests/golden/{service}/ — add fixture_*.json files first.")
    return paths


async def _run_gear_nutrition(service: str, fixture: dict) -> dict:
    if service == "gear":
        import services.gear_planner as mod

        planner, params_cls, cache = mod.gear_planner, mod.GearParams, mod._GEAR_CACHE
    else:
        import services.nutrition_planner as mod

        planner, params_cls, cache = mod.nutrition_planner, mod.NutritionParams, mod._NUTRITION_CACHE
    cache.clear()  # never serve a previous run's cached answer
    params = params_cls(**fixture["params"])
    key = planner._generate_cache_key(params)
    # gear methods: (params, key); nutrition methods: (user_profile, params, key)
    args = (params, key) if service == "gear" else ("", params, key)
    return await planner._generate_with_gemini(*args)


def _sample(name: str, labels: dict) -> float:
    from prometheus_client import REGISTRY

    return REGISTRY.get_sample_value(name, labels) or 0.0


def _scheduler_counters() -> dict:
    # status="used" fires in plan_generator only when that engine's parsed output is
    # what the call actually returns — an API "success" whose JSON fails to parse is
    # discarded by the fallback loop and never increments "used".
    return {
        "gemini_ok": _sample("rag_attempts_total", {"service": "plan_generator", "engine": "gemini", "status": "used"}),
        "retry_ok": _sample(
            "rag_attempts_total", {"service": "plan_generator", "engine": "gemini_retry", "status": "used"}
        ),
    }


def _scheduler_engine_used(before: dict, after: dict) -> str:
    """Attribute the produced plan to the tier whose "used" counter moved."""
    if after["gemini_ok"] > before["gemini_ok"]:
        return "gemini"
    if after["retry_ok"] > before["retry_ok"]:
        return "gemini_retry"
    return "rule-based-or-unknown"


async def _run_scheduler(fixture: dict) -> tuple[list[dict], str]:
    from services.plan_generator import PlanGenerator

    before = _scheduler_counters()
    workouts, _tier = await PlanGenerator.generate_plan_workouts(
        plan_id=0,
        user_profile=fixture["user_profile"],
        race_info=fixture["race_info"],
        total_weeks=fixture.get("total_weeks", 8),
        api_key=settings.GEMINI_API_KEY,
        block_number=1,
    )
    return workouts, _scheduler_engine_used(before, _scheduler_counters())


async def _run(service: str, fixture: dict) -> tuple[dict | list, str]:
    """Returns (output, tier_used). Gear/nutrition have no fallback tier by construction."""
    if service == "scheduler":
        return await _run_scheduler(fixture)
    return await _run_gear_nutrition(service, fixture), "gemini"


def _scheduler_summary(workouts: list[dict]) -> dict:
    types: dict[str, int] = {}
    for w in workouts:
        types[w.get("type", "?")] = types.get(w.get("type", "?"), 0) + 1
    me = [w for w in workouts if w.get("type") == "Muscular Endurance"]
    return {
        "workout_count": len(workouts),
        "types": types,
        "me_sessions": len(me),
        "me_looks_like_circuit": all("repeat circuit" in (w.get("description") or "").lower() for w in me)
        if me
        else None,
    }


def capture(service: str):
    for path in _fixtures(service):
        fixture = json.load(open(path, encoding="utf-8"))
        print(f"[capture] {os.path.basename(path)} → Gemini+KB baseline...")
        start = time.time()
        result, engine_used = asyncio.run(_run(service, fixture))
        ref = {"latency_s": round(time.time() - start, 1), "engine_used": engine_used, "output": result}
        if engine_used != "gemini":
            ref["engine_mismatch"] = True
            print(
                f"[capture] WARNING: {os.path.basename(path)} baseline came from "
                f"'{engine_used}', not a clean Gemini run — do not keep it as a baseline."
            )
        ref_path = path.replace(".json", ".ref.json")
        json.dump(ref, open(ref_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"[capture] saved {os.path.basename(ref_path)} ({ref['latency_s']}s)")


def compare(service: str):
    from db import get_kb_chunks
    from services.kb_context import find_uncatalogued

    lines = [f"# Golden report — {service}\n"]
    catalog_titles = [c["title"] for c in get_kb_chunks(service, kind="catalog_item")]
    for path in _fixtures(service):
        fixture = json.load(open(path, encoding="utf-8"))
        ref_path = path.replace(".json", ".ref.json")
        ref = json.load(open(ref_path, encoding="utf-8")) if os.path.exists(ref_path) else None
        print(f"[compare] {os.path.basename(path)} → Gemini+KB...")
        start = time.time()
        result, engine_used = asyncio.run(_run(service, fixture))
        latency = round(time.time() - start, 1)

        lines.append(f"\n## {os.path.basename(path)}\n")
        lines.append(
            f"- Gemini+KB latency: **{latency}s**"
            + (f" (baseline: {ref['latency_s']}s)" if ref else " (no baseline captured)")
        )
        if service == "scheduler":
            attribution = f"- Tier attribution: **{engine_used}**"
            if engine_used != "gemini":
                attribution = f"- ❌ fell through to {engine_used} — do not trust this comparison row"
            lines.append(attribution)
            if ref and ref.get("engine_mismatch"):
                lines.append(
                    f"- ⚠️ Baseline came from '{ref.get('engine_used')}', not a clean Gemini run — re-capture it"
                )
        if service in ("gear", "nutrition"):
            recs = result.get("recommendations") or result.get("products") or []
            missing = find_uncatalogued(recs, catalog_titles)
            lines.append(
                f"- Hallucination guard: {'❌ NOT IN CATALOG: ' + ', '.join(missing) if missing else '✅ all recommendations exist in the distilled catalog'}"
            )
        else:
            lines.append(f"- New: `{json.dumps(_scheduler_summary(result))}`")
            if ref:
                lines.append(f"- Ref: `{json.dumps(_scheduler_summary(ref['output']))}`")
        lines.append(
            "\n<details><summary>Gemini+KB output</summary>\n\n```json\n"
            + json.dumps(result, ensure_ascii=False, indent=2)
            + "\n```\n</details>"
        )
        if ref:
            lines.append(
                "<details><summary>Captured baseline</summary>\n\n```json\n"
                + json.dumps(ref["output"], ensure_ascii=False, indent=2)
                + "\n```\n</details>"
            )
    report_path = os.path.join(GOLDEN_DIR, f"report_{service}.md")
    open(report_path, "w", encoding="utf-8").write("\n".join(lines))
    print(f"[compare] report written: {report_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["capture", "compare"])
    parser.add_argument("--service", required=True, choices=["gear", "nutrition", "scheduler"])
    args = parser.parse_args()
    (capture if args.mode == "capture" else compare)(args.service)


if __name__ == "__main__":
    main()
