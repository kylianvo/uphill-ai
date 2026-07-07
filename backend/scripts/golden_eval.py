"""Golden-set eval: NotebookLM reference vs Gemini+KB pipeline, side by side.

  python scripts/golden_eval.py capture --service gear      # slow: real NotebookLM calls
  python scripts/golden_eval.py compare --service gear      # runs Gemini+KB, writes report

capture saves <fixture>.ref.json next to each fixture. compare writes
tests/golden/report_<service>.md. Review the report before flipping RAG_ENGINE=gemini.
Requires backend/.env (NotebookLM creds for capture, GEMINI_API_KEY + distilled KB for compare).

Scheduler engine attribution: gear/nutrition call single-engine methods directly, but the
plan generator has internal engine fallback (Gemini → NotebookLM → rule-based), so scheduler
output is attributed to the engine whose in-process Prometheus success counter moved — a
mismatched attribution is flagged loudly in the ref file and the report.
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
    paths = sorted(glob.glob(os.path.join(GOLDEN_DIR, service, "fixture_*.json")))
    if not paths:
        sys.exit(f"No fixtures in tests/golden/{service}/ — add fixture_*.json files first.")
    return paths


async def _run_gear_nutrition(service: str, fixture: dict, engine: str) -> dict:
    if service == "gear":
        import services.gear_planner as mod

        planner, params_cls, cache = mod.gear_planner, mod.GearParams, mod._GEAR_CACHE
    else:
        import services.nutrition_planner as mod

        planner, params_cls, cache = mod.nutrition_planner, mod.NutritionParams, mod._NUTRITION_CACHE
    cache.clear()  # never serve the other engine's cached answer
    params = params_cls(**fixture["params"])
    key = planner._generate_cache_key(params)
    # gear methods: (params, key); nutrition methods: (user_profile, params, key)
    args = (params, key) if service == "gear" else ("", params, key)
    if engine == "notebooklm":
        return await planner._generate_with_notebooklm(*args)
    return await planner._generate_with_gemini(*args)


def _sample(name: str, labels: dict) -> float:
    from prometheus_client import REGISTRY

    return REGISTRY.get_sample_value(name, labels) or 0.0


def _scheduler_counters() -> dict:
    return {
        "gemini_ok": _sample(
            "rag_attempts_total", {"service": "plan_generator", "engine": "gemini", "status": "success"}
        ),
        "nlm_ok": _sample("notebooklm_attempts_total", {"service": "plan_generator", "status": "success"}),
    }


def _scheduler_engine_used(before: dict, after: dict) -> str:
    """Attribute the produced plan to the engine whose success counter moved."""
    if after["gemini_ok"] > before["gemini_ok"]:
        return "gemini"
    if after["nlm_ok"] > before["nlm_ok"]:
        return "notebooklm"
    return "rule-based-or-unknown"


async def _run_scheduler(fixture: dict, engine: str) -> tuple[list[dict], str]:
    from services.plan_generator import PlanGenerator

    settings.RAG_ENGINE = "gemini" if engine == "gemini" else "notebooklm"
    before = _scheduler_counters()
    workouts = await PlanGenerator.generate_plan_workouts(
        plan_id=0,
        user_profile=fixture["user_profile"],
        race_info=fixture["race_info"],
        total_weeks=fixture.get("total_weeks", 8),
        api_key=settings.GEMINI_API_KEY,
        block_number=1,
    )
    return workouts, _scheduler_engine_used(before, _scheduler_counters())


async def _run(service: str, fixture: dict, engine: str) -> tuple[dict | list, str]:
    """Returns (output, engine_used). Gear/nutrition are single-engine by construction."""
    if service == "scheduler":
        return await _run_scheduler(fixture, engine)
    return await _run_gear_nutrition(service, fixture, engine), engine


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
        print(f"[capture] {os.path.basename(path)} → NotebookLM (slow)...")
        start = time.time()
        result, engine_used = asyncio.run(_run(service, fixture, "notebooklm"))
        ref = {"latency_s": round(time.time() - start, 1), "engine_used": engine_used, "output": result}
        if engine_used != "notebooklm":
            ref["engine_mismatch"] = True
            print(
                f"[capture] WARNING: {os.path.basename(path)} reference was produced by "
                f"'{engine_used}', NOT NotebookLM — do not trust it as a reference."
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
        result, engine_used = asyncio.run(_run(service, fixture, "gemini"))
        latency = round(time.time() - start, 1)

        lines.append(f"\n## {os.path.basename(path)}\n")
        lines.append(
            f"- Gemini+KB latency: **{latency}s**"
            + (f" (NotebookLM reference: {ref['latency_s']}s)" if ref else " (no reference captured)")
        )
        if service == "scheduler":
            attribution = f"- Engine attribution: **{engine_used}**"
            if engine_used != "gemini":
                attribution = f"- ❌ NOT GEMINI — result came from {engine_used}; do not trust this comparison row"
            lines.append(attribution)
            if ref and ref.get("engine_mismatch"):
                lines.append(
                    f"- ⚠️ Reference was produced by '{ref.get('engine_used')}', not NotebookLM — re-capture it"
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
                "<details><summary>NotebookLM reference</summary>\n\n```json\n"
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
