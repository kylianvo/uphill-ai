"""Re-sweep operator-curated principle rows from NotebookLM into kb_chunks + seed files.

This is the ONLY remaining NotebookLM consumer in the codebase. Everything else --
plan generation, the gear finder, the nutrition lab, the Knowledge Hub -- runs on
Gemini grounded by the distilled KB.

It lives as a script rather than an endpoint or a DAG on purpose: a principle sweep
REPLACES a domain's curated doctrine wholesale (services.kb_distiller.save_domain),
so an unattended run that returned junk would overwrite a working knowledge base.
Doctrine changes when an operator decides it changes -- not weekly. The automated,
insert-only web-discovery sweeps (gear + nutrition catalogs) keep their endpoint and
their DAG; see WEB_DOMAINS in services/kb_distiller.py.

Operator workflow:
    1. add/curate sources in the NotebookLM notebook
    2. NOTEBOOKLM_AUTH_JSON + the notebook id must be set in the environment
    3. python scripts/distill_principles.py --domain scheduler
    4. review the diff in backend/kb_seed/<domain>.json, then commit it
    5. other environments pick it up via POST /api/kb/import or scripts/load_kb.py

Usage:
    python scripts/distill_principles.py --domain scheduler
    python scripts/distill_principles.py --domain nutrition
    python scripts/distill_principles.py --domain all --dry-run
"""

import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic import BaseModel  # noqa: E402

from config import settings  # noqa: E402
from services.kb_distiller import (  # noqa: E402
    _gemini_structured,
    export_seed,
    save_domain,
    validate_domain_rows,
)
from services.notebooklm_service import NotebookLmService  # noqa: E402

PRINCIPLE_DOMAINS = ("scheduler", "nutrition")


class PrincipleChunk(BaseModel):
    title: str
    content: str


class PrincipleList(BaseModel):
    principles: list[PrincipleChunk]


# ─── Sweep queries ───────────────────────────────────────────────────────────

SCHEDULER_TOPICS = [
    "Muscular Endurance (ME) session design: circuit structure, exercise selection, reps per pass, rounds, rest between rounds, progression over weeks, and exactly how ME differs from conventional strength training",
    "Periodization: Base, Build, Peak, Taper, Race Week and Recovery phases — how long each lasts, what workouts belong in each, and weekly volume progression rules",
    "Zone 2 / aerobic base training: weekly volume share, AeT vs AnT, the 80/20 intensity distribution, aerobic deficiency syndrome",
    "Long runs for trail and mountain races: distance and vert scaling to the goal race, back-to-back long days, fueling during long efforts",
    "Taper and race week: how much to cut volume, keeping intensity, structuring the final week",
    "Hill workouts and treadmill substitution: hill sprints vs hill repeats, incline and speed settings, matching grade to race-specific vert",
    "Double sessions and weekly scheduling: when two-a-days make sense, what goes in morning vs afternoon sessions, recovery spacing",
    "Strength training (non-ME): exercise selection, sets/reps/rest, and how gym work fits each training phase",
    "Recovery weeks and deloads: frequency, volume reduction, signs of overtraining, adjusting after missed training",
    "Race-day pacing and course-specific preparation for uphill athletes",
    "Downhill running mechanics, eccentric quadriceps conditioning, vert adaptation, and injury-prevention protocols (step-downs, weighted lunges, downhill repeats)",
    "Back-to-back long runs for ultra endurance: volume caps, weekly percentage distribution, fueling between days, and fatigue management",
    "Altitude and heat acclimation: timeline for adaptations, pacing adjustments per 1000m elevation gain, plasma volume expansion, and heat protocol integration",
    "Pre-race carb-loading protocols (g/kg bodyweight over 36-48h), low-residue diet transition to prevent GI distress, and electrolyte pre-loading",
    # ─── Tier-gap topics ──────────────────────────────────────────────────────
    # The 29 rows this notebook produced before these were added were all pitched at
    # one audience: a trained mountain athlete. services/athlete_tier.py now generates
    # for five tiers, and retrieval had nothing to ground the two ends of that range --
    # so a beginner's plan was grounded on gym ME protocols. These topics exist to fill
    # that. EXPECT SOME TO COME BACK "NOT COVERED": this notebook is not a
    # couch-to-5k source, and an honest gap is the correct outcome. Do not soften the
    # NOT COVERED instruction in _sweep_query to make them return something.
    "Walk-to-run progression for a complete beginner: the starting run:walk ratio and interval duration, repetitions per session, how the ratio changes week to week, and the specific criterion that says the athlete is ready to progress",
    "Transitioning from run/walk intervals to continuous running: what threshold (unbroken minutes, run:walk ratio, or effort) signals readiness, and how to structure that transition",
    "Injury risk in new runners: bone and connective-tissue adaptation timelines, weekly session-count and rest-day limits, and the early warning signs that require backing off",
    "Regulating effort without reliable pace or heart-rate data: the talk test and other field cues for an athlete who has no established threshold numbers",
    "Weeks containing two or more quality sessions: how they are spaced, sequenced relative to the long run, and what total weekly high-intensity volume a highly trained athlete tolerates",
    "Periodization above 100 km per week: how progression rates, deload frequency and recovery needs differ from those of lower-volume athletes",
    "Double-day training: when a second daily session is warranted, what belongs in each session, and the minimum recovery between them",
    "Markers of readiness and overreaching in highly trained athletes: which metrics matter, and what thresholds should trigger a change to the plan",
]

NUTRITION_PRINCIPLE_TOPICS = [
    "Carbohydrate intake targets per hour for ultra racing, gut training, and how to build up carb tolerance",
    "Sodium and hydration strategy: mg per hour targets, hot weather adjustments, sweat rate",
    "Pre-race nutrition, real food vs gels during long races, and common race fueling mistakes",
]


# A sweep asks about topics the notebook may simply not cover -- the tier-gap topics
# below are the obvious case, since this is not a beginner-running source. Without the
# NOT COVERED escape, "summarize everything your documents say about X" invites the
# model to generalise from adjacent material, and the result is plausible prose with no
# source behind it. That is strictly worse than a gap here: scheduler principles REPLACE
# the domain wholesale on save, so an ungrounded sweep would overwrite good rows with
# invented ones. The marker is filtered out before structuring.
NOT_COVERED = "NOT COVERED"


def _sweep_query(topic: str, specificity: str) -> str:
    return (
        f"Summarize everything your documents say about: {topic}. {specificity}\n\n"
        f"IMPORTANT: answer ONLY from these documents. If they do not address this topic, "
        f"reply with exactly '{NOT_COVERED}' and nothing else. Do NOT generalise from "
        f"related material, and do NOT draw on knowledge outside these documents -- an "
        f"honest gap is more useful here than a plausible answer."
    )


def _is_not_covered(answer: str) -> bool:
    """True when the notebook said it has nothing on this topic. Checked loosely --
    models tend to wrap a bare marker in a sentence -- but only over a short answer, so
    a real summary that happens to mention the phrase is not discarded."""
    stripped = (answer or "").strip()
    return not stripped or (len(stripped) < 200 and NOT_COVERED.lower() in stripped.lower())


async def _query_with_retries(notebook_id: str, auth_json: str, query: str, attempts: int = 3) -> str:
    """NotebookLM calls fail transiently (server disconnects, truncated streams,
    brief DNS outages) — observed holing an entire sweep. Retry with a growing
    backoff before giving up on a topic/brand."""
    for attempt in range(1, attempts + 1):
        try:
            return await NotebookLmService.query_notebook(
                notebook_id=notebook_id, auth_json=auth_json, query=query, service="kb_distiller"
            )
        except Exception as e:
            if "RPC response exceeded" in str(e):
                # Deterministic: the answer itself overflows the client's stream
                # cap, so the same query will always fail — callers must narrow it.
                raise
            if attempt == attempts:
                raise
            wait_s = 15.0 * attempt
            print(f"[KBDistiller] Query attempt {attempt}/{attempts} failed ({e}); retrying in {wait_s:.0f}s…")
            await asyncio.sleep(wait_s)


async def _distill_nutrition(notebook_id: str, auth_json: str, api_key: str, status: dict) -> list[dict]:
    rows: list[dict] = []
    skipped: list[str] = []
    total = len(NUTRITION_PRINCIPLE_TOPICS)
    for j, topic in enumerate(NUTRITION_PRINCIPLE_TOPICS):
        status.update({"current_topic": f"nutrition principle {j + 1}", "progress": j, "total": total})
        try:
            answer = await _query_with_retries(
                notebook_id,
                auth_json,
                _sweep_query(topic, "Be specific with numbers."),
            )
            if _is_not_covered(answer):
                print(f"[distill_principles] NOT COVERED, skipping: {topic[:60]}…")
                skipped.append(topic)
                await asyncio.sleep(1.5)
                continue
            structured = await _gemini_structured(
                api_key,
                "Split this text into 1-3 self-contained principle chunks (title + 100-400 word content). "
                "NEVER add facts not present in the text. Write every field in clear English only — "
                "never any other language.\n\n" + answer,
                PrincipleList,
            )
            for principle in structured.get("principles", []):
                rows.append(
                    {
                        "domain": "nutrition",
                        "kind": "principle",
                        "title": principle.get("title", topic[:60]),
                        "content": principle.get("content", ""),
                        "payload": None,
                    }
                )
        except Exception as e:
            print(f"[distill_principles][nutrition] Principle topic failed, continuing: {e}")
        await asyncio.sleep(1.5)
    if skipped:
        print(f"\n[distill_principles] {len(skipped)} topic(s) NOT COVERED by this notebook:")
        for t in skipped:
            print(f"    - {t[:100]}")
        print("    These are real gaps, not failures. Source material would have to be added")
        print("    to the notebook for them to produce rows.\n")
    return rows


async def _distill_scheduler(notebook_id: str, auth_json: str, api_key: str, status: dict) -> list[dict]:
    rows: list[dict] = []
    skipped: list[str] = []
    for i, topic in enumerate(SCHEDULER_TOPICS):
        status.update({"current_topic": f"scheduler: {topic[:50]}…", "progress": i, "total": len(SCHEDULER_TOPICS)})
        try:
            answer = await _query_with_retries(
                notebook_id,
                auth_json,
                _sweep_query(topic, "Be specific — numbers, protocols, examples."),
            )
            if _is_not_covered(answer):
                print(f"[distill_principles] NOT COVERED, skipping: {topic[:60]}…")
                skipped.append(topic)
                await asyncio.sleep(1.5)
                continue
            structured = await _gemini_structured(
                api_key,
                "Split this text into 2-4 self-contained principle chunks (title + 200-600 word content) "
                "for grounding a training-plan generator. NEVER add facts not present in the text. "
                "Write every field in clear English only — never any other language.\n\n" + answer,
                PrincipleList,
            )
            for principle in structured.get("principles", []):
                rows.append(
                    {
                        "domain": "scheduler",
                        "kind": "principle",
                        "title": principle.get("title", topic[:60]),
                        "content": principle.get("content", ""),
                        "payload": None,
                    }
                )
        except Exception as e:
            print(f"[distill_principles][scheduler] Topic failed, continuing: {e}")
        await asyncio.sleep(1.5)
    if skipped:
        print(f"\n[distill_principles] {len(skipped)} topic(s) NOT COVERED by this notebook:")
        for t in skipped:
            print(f"    - {t[:100]}")
        print("    These are real gaps, not failures. Source material would have to be added")
        print("    to the notebook for them to produce rows.\n")
    return rows


def _notebook_id(domain: str) -> str:
    """Gear is absent on purpose -- its catalog comes from web discovery, not a notebook."""
    return {
        "nutrition": settings.NOTEBOOKLM_NUTRITION_ID,
        "scheduler": settings.NOTEBOOKLM_NOTEBOOK_ID,
    }[domain]


async def sweep_principles(domain: str, api_key: str) -> list[dict]:
    """NotebookLM sweep -> Gemini structuring -> principle rows for one domain."""
    notebook_id, auth_json = _notebook_id(domain), settings.NOTEBOOKLM_AUTH_JSON
    if not notebook_id or not auth_json:
        raise RuntimeError(
            f"NotebookLM is not configured for '{domain}' — set NOTEBOOKLM_AUTH_JSON and the notebook id."
        )
    status: dict = {}
    distiller = _distill_scheduler if domain == "scheduler" else _distill_nutrition
    return await distiller(notebook_id, auth_json, api_key, status)


async def _run(domains: list[str], api_key: str, dry_run: bool) -> int:
    failures = 0
    for domain in domains:
        print(f"\n=== {domain}: sweeping NotebookLM ===")
        try:
            rows = await sweep_principles(domain, api_key)
        except Exception as e:
            print(f"!! {domain}: sweep failed — {e}")
            failures += 1
            continue

        print(f"{domain}: {len(rows)} principle rows returned")
        try:
            # Same batch-level floor the automated path uses: a thin sweep means the
            # notebook refused or timed out, and replacing curated doctrine with it
            # would be worse than doing nothing.
            rows = validate_domain_rows(domain, rows)
        except Exception as e:
            print(f"!! {domain}: validation rejected the sweep — {e}")
            failures += 1
            continue

        if dry_run:
            path = export_seed(f"{domain}.dryrun", rows)
            print(f"{domain}: DRY RUN — wrote {len(rows)} rows to {path}, database untouched")
            continue

        saved = await save_domain(domain, rows, api_key)
        print(f"{domain}: {saved} chunks saved, seed exported to backend/kb_seed/{domain}.json")
        print(f"{domain}: review the seed diff and commit it so other environments pick it up")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--domain", default="scheduler", choices=[*PRINCIPLE_DOMAINS, "all"])
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="sweep and validate, write <domain>.dryrun.json, but do not touch Postgres/Qdrant",
    )
    args = parser.parse_args()

    api_key = settings.GEMINI_API_KEY
    if not api_key:
        print("!! GEMINI_API_KEY is not set — the sweep needs it to structure raw notebook text.")
        return 1

    domains = list(PRINCIPLE_DOMAINS) if args.domain == "all" else [args.domain]
    failures = asyncio.run(_run(domains, api_key, args.dry_run))
    if failures:
        print(f"\n{failures} domain(s) failed — existing KB left untouched for those.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
