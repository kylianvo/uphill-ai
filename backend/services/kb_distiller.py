"""Distills the three NotebookLM notebooks into kb_chunks rows + committed seed files.

Offline batch job — NotebookLM's 2-minute latency is irrelevant here; it runs when an
operator adds sources to a notebook and hits POST /api/kb/distill. Sweep queries pull
notebook content out; Gemini structures each response (temperature 0); rows land in
Postgres (kb_chunks), get exported to backend/kb_seed/<domain>.json (committed so prod
imports without re-distilling), and scheduler chunks are embedded into Qdrant.
"""

import asyncio
import json
import os
import re
from typing import Any

import google.generativeai as genai
from pydantic import BaseModel

from config import settings
from services.notebooklm_service import NotebookLmService

SEED_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "kb_seed")
DOMAINS = ("gear", "nutrition", "scheduler")


# ─── Gemini structuring schemas ──────────────────────────────────────────────


class BrandList(BaseModel):
    brands: list[str]


class ShoeEntry(BaseModel):
    model: str
    brand: str
    foam_material: str
    outsole_compound: str
    lug_depth: str
    drop: str
    stack: str
    price: str
    pros: str
    cons: str
    best_for: str


class ShoeList(BaseModel):
    shoes: list[ShoeEntry]


class ProductEntry(BaseModel):
    brand: str
    name: str
    format: str
    carbs_per_unit: float
    sodium_per_unit: float
    protein_per_unit: float
    tech_notes: str


class ProductList(BaseModel):
    products: list[ProductEntry]


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
]

NUTRITION_PRINCIPLE_TOPICS = [
    "Carbohydrate intake targets per hour for ultra racing, gut training, and how to build up carb tolerance",
    "Sodium and hydration strategy: mg per hour targets, hot weather adjustments, sweat rate",
    "Pre-race nutrition, real food vs gels during long races, and common race fueling mistakes",
]


async def _gemini_structured(api_key: str, prompt: str, schema: type[BaseModel]) -> dict[str, Any]:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = await asyncio.to_thread(
        model.generate_content,
        prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json", response_schema=schema, temperature=0.0
        ),
    )
    return json.loads(response.text)


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


async def _sweep_brands(notebook_id: str, auth_json: str, api_key: str, thing: str) -> list[str]:
    brands_text = await _query_with_retries(
        notebook_id,
        auth_json,
        f"List every {thing} brand covered in your documents. Output one brand name per line, nothing else.",
    )
    parsed = await _gemini_structured(
        api_key, f"Extract the list of brand names from this text:\n{brands_text}", BrandList
    )
    return parsed.get("brands", [])


# Gear sweeps use this operator-curated whitelist instead of a NotebookLM brand
# enumeration — the sources mention many competitor brands in passing (review
# sites compare shoes), and sweeping every mentioned brand adds noise. Add a
# brand here and re-run POST /api/kb/distill?domain=gear to onboard it.
GEAR_BRANDS = [
    "adidas",
    "Nike",
    "New Balance",
    "Hoka",
    "Salomon",
    "Saucony",
    "Brooks",
    "Mount to Coast",
    "Norda",
    "Puma",
    "NNormal",
    "Asics",
    "On",
    "Kailas",
    "Altra",
]


def _whitelisted_brand(returned_brand: str, queried_brand: str) -> str | None:
    """Keep only whitelisted brands. The per-brand sweep text may mention
    competitors (review comparisons), and Gemini may restyle the brand name
    (e.g. 'HOKA ONE ONE' for the 'Hoka' query) — coerce those to the queried
    brand; drop anything else."""
    returned = (returned_brand or "").strip()
    allowed = {b.lower(): b for b in GEAR_BRANDS}
    if returned.lower() in allowed:
        return allowed[returned.lower()]
    if re.search(rf"\b{re.escape(queried_brand.lower())}\b", returned.lower()):
        return queried_brand
    return None


# A distilled shoe is only useful if it carries real specs. Score = number of
# filled spec fields; a brand sweep averaging below the threshold is re-swept
# (NotebookLM under load returns thin series-level summaries).
_SPEC_FIELDS = ("foam_material", "outsole_compound", "lug_depth", "drop", "stack", "price", "pros", "cons", "best_for")
_MIN_AVG_RICHNESS = 4


def _shoe_richness(shoe: dict) -> int:
    return sum(1 for field in _SPEC_FIELDS if (shoe.get(field) or "").strip())


def _sweep_richness(shoes: list[dict]) -> int:
    return sum(_shoe_richness(s) for s in shoes)


_GEAR_SPEC_ASK = (
    "For each shoe give: exact model name, foam material with its type in parentheses "
    "(e.g. ZoomX (PEBA)), outsole compound, lug depth in mm, drop in mm, stack height, price, "
    "what it is best for and its strengths (pros), and its drawbacks or who shouldn't buy it (cons). "
    "Include every model mentioned, even briefly."
)


async def _sweep_gear_brand(notebook_id: str, auth_json: str, api_key: str, brand: str) -> list[dict]:
    async def sweep_query(query_text: str) -> list[dict]:
        answer = await _query_with_retries(notebook_id, auth_json, query_text)
        structured = await _gemini_structured(
            api_key,
            "Structure every shoe in this text into the schema. NEVER add a shoe, spec, or price "
            "that is not present in the text.\n\n" + answer,
            ShoeList,
        )
        return structured.get("shoes", [])

    try:
        return await sweep_query(f"List EVERY {brand} shoe in your documents. {_GEAR_SPEC_ASK}")
    except Exception as e:
        if "RPC response exceeded" not in str(e):
            raise
        # The brand's full answer overflows the NotebookLM client's stream cap
        # (seen with Nike and Altra) — split the sweep into narrower scopes.
        print(f"[KBDistiller][gear] Brand '{brand}' answer overflowed the stream cap — splitting trail/road.")
        shoes: list[dict] = []
        for scope in ("trail running", "road running"):
            try:
                shoes += await sweep_query(
                    f"List EVERY {brand} {scope} shoe in your documents. Keep each shoe brief. {_GEAR_SPEC_ASK}"
                )
            except Exception as scope_e:
                print(f"[KBDistiller][gear] '{brand}' {scope} split failed, continuing: {scope_e}")
            await asyncio.sleep(1.5)
        seen: set[str] = set()
        unique: list[dict] = []
        for shoe in shoes:
            key = (shoe.get("model") or "").strip().lower()
            if key and key not in seen:
                seen.add(key)
                unique.append(shoe)
        return unique


async def _distill_gear(notebook_id: str, auth_json: str, api_key: str, status: dict) -> list[dict]:
    brands = GEAR_BRANDS
    rows: list[dict] = []

    for i, brand in enumerate(brands):
        status.update({"current_topic": f"gear: {brand}", "progress": i, "total": len(brands)})
        try:
            shoes = await _sweep_gear_brand(notebook_id, auth_json, api_key, brand)
            if not shoes or _sweep_richness(shoes) / max(len(shoes), 1) < _MIN_AVG_RICHNESS:
                # Under load NotebookLM sometimes "succeeds" with a refusal or a
                # thin series-level summary (model names, no specs) — either way
                # the catalog entry would be useless. Re-sweep once and keep the
                # richer of the two results.
                print(
                    f"[KBDistiller][gear] Brand '{brand}' sweep was empty/thin "
                    f"({len(shoes)} shoes, richness {_sweep_richness(shoes)}) — retrying the sweep once."
                )
                await asyncio.sleep(10)
                second = await _sweep_gear_brand(notebook_id, auth_json, api_key, brand)
                if _sweep_richness(second) > _sweep_richness(shoes):
                    shoes = second
            kept = 0
            for shoe in shoes:
                brand_final = _whitelisted_brand(shoe.get("brand", brand), brand)
                if brand_final is None:
                    print(f"[KBDistiller][gear] Skipping non-whitelisted brand row: {shoe.get('brand')!r}")
                    continue
                shoe["brand"] = brand_final
                model = (shoe.get("model") or "").strip()
                if model.lower().startswith(brand_final.lower() + " "):
                    # Gemini sometimes repeats the brand inside the model name
                    model = model[len(brand_final) :].strip()
                shoe["model"] = model  # keep payload consistent so UIs don't show "Kailas Kailas Fuga"
                title = f"{brand_final} {model}".strip()
                rows.append(
                    {
                        "domain": "gear",
                        "kind": "catalog_item",
                        "title": title,
                        "content": f"{title}: {shoe.get('pros', '')} Cons: {shoe.get('cons', '')}",
                        "payload": shoe,
                    }
                )
                kept += 1
            print(f"[KBDistiller][gear] Brand '{brand}': {kept} shoes")
        except Exception as e:
            print(f"[KBDistiller][gear] Brand '{brand}' failed, continuing: {e}")
        await asyncio.sleep(1.5)  # NotebookLM rate-limit courtesy (same as knowledge_extractor)
    return rows


async def _distill_nutrition(notebook_id: str, auth_json: str, api_key: str, status: dict) -> list[dict]:
    brands = await _sweep_brands(notebook_id, auth_json, api_key, "sports nutrition")
    rows: list[dict] = []
    total = len(brands) + len(NUTRITION_PRINCIPLE_TOPICS)
    for i, brand in enumerate(brands):
        status.update({"current_topic": f"nutrition: {brand}", "progress": i, "total": total})
        try:
            answer = await _query_with_retries(
                notebook_id,
                auth_json,
                (
                    f"List EVERY {brand} product in your documents (gels, drink mixes, chews, bars). "
                    "For each give: exact product name, format, carbs per unit (g), sodium per unit (mg), "
                    "protein per unit (g), and any technology/science notes. Include every product mentioned."
                ),
            )
            structured = await _gemini_structured(
                api_key,
                "Structure every product in this text into the schema. NEVER add a product or macro "
                "figure that is not present in the text.\n\n" + answer,
                ProductList,
            )
            for product in structured.get("products", []):
                title = f"{product.get('brand', brand)} {product.get('name', '')}".strip()
                rows.append(
                    {
                        "domain": "nutrition",
                        "kind": "catalog_item",
                        "title": title,
                        "content": f"{title}: {product.get('tech_notes', '')}",
                        "payload": product,
                    }
                )
        except Exception as e:
            print(f"[KBDistiller][nutrition] Brand '{brand}' failed, continuing: {e}")
        await asyncio.sleep(1.5)
    for j, topic in enumerate(NUTRITION_PRINCIPLE_TOPICS):
        status.update({"current_topic": f"nutrition principle {j + 1}", "progress": len(brands) + j, "total": total})
        try:
            answer = await _query_with_retries(
                notebook_id,
                auth_json,
                f"Summarize everything your documents say about: {topic}. Be specific with numbers.",
            )
            structured = await _gemini_structured(
                api_key,
                "Split this text into 1-3 self-contained principle chunks (title + 100-400 word content). "
                "NEVER add facts not present in the text.\n\n" + answer,
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
            print(f"[KBDistiller][nutrition] Principle topic failed, continuing: {e}")
        await asyncio.sleep(1.5)
    return rows


async def _distill_scheduler(notebook_id: str, auth_json: str, api_key: str, status: dict) -> list[dict]:
    rows: list[dict] = []
    for i, topic in enumerate(SCHEDULER_TOPICS):
        status.update({"current_topic": f"scheduler: {topic[:50]}…", "progress": i, "total": len(SCHEDULER_TOPICS)})
        try:
            answer = await _query_with_retries(
                notebook_id,
                auth_json,
                f"Summarize everything your documents say about: {topic}. Be specific — numbers, protocols, examples.",
            )
            structured = await _gemini_structured(
                api_key,
                "Split this text into 2-4 self-contained principle chunks (title + 200-600 word content) "
                "for grounding a training-plan generator. NEVER add facts not present in the text.\n\n" + answer,
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
            print(f"[KBDistiller][scheduler] Topic failed, continuing: {e}")
        await asyncio.sleep(1.5)
    return rows


def _notebook_id(domain: str) -> str:
    return {
        "gear": settings.NOTEBOOKLM_GEAR_ID,
        "nutrition": settings.NOTEBOOKLM_NUTRITION_ID,
        "scheduler": settings.NOTEBOOKLM_NOTEBOOK_ID,
    }[domain]


async def distill_domain(domain: str, api_key: str, status_holder: dict) -> int:
    """Sweep one notebook → replace that domain's kb_chunks → export seed → (scheduler) reindex."""
    import db

    notebook_id = _notebook_id(domain)
    auth_json = settings.NOTEBOOKLM_AUTH_JSON
    if not notebook_id or not auth_json:
        raise RuntimeError(f"NotebookLM is not configured for domain '{domain}'.")

    distiller = globals()[f"_distill_{domain}"]
    rows = await distiller(notebook_id, auth_json, api_key, status_holder)
    if not rows:
        # A failed sweep must never wipe a working KB.
        raise RuntimeError(f"Distillation produced an empty result for '{domain}' — keeping existing KB.")

    saved = db.replace_kb_chunks(domain, rows)
    export_seed(domain, rows)
    if domain == "scheduler":
        from services.kb_retrieval import reindex_scheduler_chunks

        await asyncio.to_thread(reindex_scheduler_chunks, rows, api_key)
    print(f"[KBDistiller] '{domain}' distilled: {saved} chunks saved, seed exported.")
    return saved


# ─── Seed export / import (distill once, use in dev AND prod) ────────────────


def export_seed(domain: str, rows: list[dict]) -> str:
    os.makedirs(SEED_DIR, exist_ok=True)
    path = os.path.join(SEED_DIR, f"{domain}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"domain": domain, "chunks": rows}, f, ensure_ascii=False, indent=2)
    return path


def load_seed(domain: str, api_key: str | None = None) -> int:
    """SYNC. Load backend/kb_seed/<domain>.json into Postgres (+ Qdrant for scheduler)."""
    import db

    path = os.path.join(SEED_DIR, f"{domain}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Seed file not found: {path} — run distillation first.")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    chunks = data.get("chunks", [])
    if not chunks:
        raise RuntimeError(f"Seed file for '{domain}' is empty — refusing to wipe existing KB.")
    saved = db.replace_kb_chunks(domain, chunks)
    if domain == "scheduler" and api_key:
        from services.kb_retrieval import reindex_scheduler_chunks

        reindex_scheduler_chunks(chunks, api_key)
    elif domain == "scheduler":
        print(
            "[KBDistiller] WARNING: scheduler chunks saved but Qdrant reindex SKIPPED "
            "(no Gemini API key) — plans will generate without philosophy grounding until reindexed."
        )
    print(f"[KBDistiller] Seed '{domain}' loaded: {saved} chunks.")
    return saved
