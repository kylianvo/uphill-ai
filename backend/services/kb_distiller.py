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
from urllib.parse import urlparse

import google.generativeai as genai
from pydantic import BaseModel
from tavily import TavilyClient

from config import settings
from services.notebooklm_service import NotebookLmService

SEED_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "kb_seed")
DOMAINS = ("gear", "nutrition", "scheduler")
# Hand-curated domains have no NotebookLM notebook to sweep -- they only ever
# load via load_seed(), never distill_domain(). Kept separate from DOMAINS so
# /api/kb/distill (which sweeps notebooks) never tries to validate against them.
HAND_CURATED_DOMAINS = ("race_courses",)


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
    # Fields below mirror the Gear planner's input criteria (GearParams) so the
    # runtime engine can match athlete needs against catalog facts directly.
    cushioning: str  # e.g. "max", "moderate", "firm/minimal"
    foot_shape: str  # e.g. "narrow", "standard", "wide", "roomy toe box"
    carbon_plate: str  # "yes (carbon plate)", "yes (rods)", "no" — plus detail if noted
    arch_support: str  # e.g. "neutral", "stability", "motion control" — plus detail if noted
    terrain: list[str]  # e.g. ["muddy", "technical", "rocky", "runnable", "road"]
    intended_use: str  # e.g. "daily trainer", "race day", "tempo/workouts", "recovery", "ultras"
    overview: str  # 1-2 sentence plain-language summary of the shoe's character
    highlights: str  # standout tech or special features worth calling out
    suitability: str  # who it suits/doesn't: heavier runners, injury-prone, beginners…


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
_SPEC_FIELDS = (
    "foam_material",
    "outsole_compound",
    "lug_depth",
    "drop",
    "stack",
    "price",
    "pros",
    "cons",
    "best_for",
    "cushioning",
    "foot_shape",
    "carbon_plate",
    "arch_support",
    "terrain",
    "intended_use",
    "overview",
    "highlights",
    "suitability",
)
_MIN_AVG_RICHNESS = 4
_MIN_ROWS = {"nutrition": 5, "scheduler": 15}


def _shoe_richness(shoe: dict) -> int:
    score = 0
    for field in _SPEC_FIELDS:
        value = shoe.get(field)
        if isinstance(value, str):
            score += 1 if value.strip() else 0
        elif isinstance(value, list):
            score += 1 if value else 0
    return score


def _sweep_richness(shoes: list[dict]) -> int:
    return sum(_shoe_richness(s) for s in shoes)


_GEAR_ARTICLE_ASK = (
    "Structure every properly-reviewed shoe in this article into the schema. ONLY include shoes with "
    "real spec/testing detail in the text — skip shoes merely mentioned in passing. For each: exact model "
    "name; foam material with type in parentheses; outsole compound; lug depth in mm; drop in mm; stack "
    "height; price; cushioning level (max/moderate/firm); toe box/fit width; carbon plate or rods (yes/no "
    "+ detail); arch support; recommended terrain; intended use; a 1-2 sentence overview; standout tech; "
    "who it suits/doesn't; pros; cons. If the article doesn't state a detail, skip that detail rather than "
    "guessing. NEVER add a shoe, spec, or price not present in the text. Write every field in clear English "
    "only — never any other language.\n\nArticle:\n"
)


def _known_gear_titles() -> set[str]:
    import db

    return {row["title"].lower() for row in db.get_kb_chunks("gear", kind="catalog_item")}


async def discover_gear_web(api_key: str, tavily_api_key: str, status_holder: dict) -> list[dict]:
    """Search RunRepeat/BelieveInTheRun for new reviews of whitelisted gear brands, skip
    results matching an already-known shoe, structure the rest with Gemini. Incremental —
    an empty result (no new shoes this week) is a normal, valid outcome."""
    client = TavilyClient(api_key=tavily_api_key)
    known_titles = _known_gear_titles()
    rows: list[dict] = []

    for i, brand in enumerate(GEAR_BRANDS):
        status_holder.update({"current_topic": f"gear web: {brand}", "progress": i, "total": len(GEAR_BRANDS)})
        try:
            response = await asyncio.to_thread(
                client.search,
                f"{brand} new trail running shoe review 2026",
                include_domains=["runrepeat.com", "believeintherun.com"],
                max_results=5,
                include_raw_content="markdown",
            )
        except Exception as e:
            print(f"[KBDistiller][gear-web] Search failed for '{brand}', continuing: {e}")
            await asyncio.sleep(1.5)
            continue

        for result in response.get("results", []):
            title_lower = (result.get("title") or "").lower()
            if any(known in title_lower for known in known_titles) or title_lower in known_titles:
                continue  # pre-filter: cheap skip before spending a Gemini call
            content = result.get("raw_content") or result.get("content") or ""
            if not content.strip():
                continue
            try:
                structured = await _gemini_structured(api_key, _GEAR_ARTICLE_ASK + content, ShoeList)
            except Exception as e:
                print(f"[KBDistiller][gear-web] Structuring failed for '{result.get('url')}', continuing: {e}")
                continue
            source_label = urlparse(result.get("url", "")).netloc.removeprefix("www.")
            for shoe in structured.get("shoes", []):
                brand_final = _whitelisted_brand(shoe.get("brand", brand), brand)
                if brand_final is None:
                    continue
                shoe["brand"] = brand_final
                model = (shoe.get("model") or "").strip()
                if model.lower().startswith(brand_final.lower() + " "):
                    model = model[len(brand_final) :].strip()
                shoe["model"] = model
                shoe_title = f"{brand_final} {model}".strip()
                if shoe_title.lower() in known_titles:
                    continue  # post-structure dedup: article title didn't match, structured model did
                known_titles.add(shoe_title.lower())
                rows.append(
                    {
                        "domain": "gear",
                        "kind": "catalog_item",
                        "title": shoe_title,
                        "content": f"{shoe_title}: {shoe.get('pros', '')} Cons: {shoe.get('cons', '')}",
                        "payload": shoe,
                        "source_label": source_label,
                    }
                )
        await asyncio.sleep(1.5)  # search-API rate-limit courtesy, same pacing as the NotebookLM sweeps
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
                    "protein per unit (g), and any technology/science notes. Include every product mentioned. "
                    "Answer as a COMPACT plain-text list right here in chat, at most 3 short lines per "
                    "product — do NOT compile a guide, table document, note, or file."
                ),
            )
            structured = await _gemini_structured(
                api_key,
                "Structure every product in this text into the schema. NEVER add a product or macro "
                "figure that is not present in the text. Write every field in clear English only — "
                "never any other language.\n\n" + answer,
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
            print(f"[KBDistiller][scheduler] Topic failed, continuing: {e}")
        await asyncio.sleep(1.5)
    return rows


def _notebook_id(domain: str) -> str:
    return {
        "gear": settings.NOTEBOOKLM_GEAR_ID,
        "nutrition": settings.NOTEBOOKLM_NUTRITION_ID,
        "scheduler": settings.NOTEBOOKLM_NOTEBOOK_ID,
    }[domain]


def validate_domain_rows(domain: str, rows: list[dict]) -> list[dict]:
    """Batch-level gate before a sweep's rows reach Postgres/Qdrant.
    gear (incremental): 0 new rows is a normal outcome — just drop any individual thin row.
    nutrition/scheduler (full-replace): below-floor row counts mean the sweep likely hit a
    broad NotebookLM outage/refusal — raise rather than replace a working KB with junk."""
    if domain == "gear":
        return [r for r in rows if _shoe_richness(r.get("payload") or {}) >= _MIN_AVG_RICHNESS]
    floor = _MIN_ROWS.get(domain)
    if floor is not None and len(rows) < floor:
        raise RuntimeError(
            f"Distillation produced only {len(rows)} rows for '{domain}' (floor {floor}) — keeping existing KB."
        )
    return rows


async def sweep_domain(domain: str, api_key: str, status_holder: dict) -> list[dict]:
    """Dispatch to this domain's data source. gear discovers from the live web
    (RunRepeat/BelieveInTheRun via Tavily); nutrition/scheduler still sweep NotebookLM."""
    if domain == "gear":
        if not settings.TAVILY_API_KEY:
            raise RuntimeError("TAVILY_API_KEY is not configured.")
        return await discover_gear_web(api_key, settings.TAVILY_API_KEY, status_holder)
    notebook_id, auth_json = _notebook_id(domain), settings.NOTEBOOKLM_AUTH_JSON
    if not notebook_id or not auth_json:
        raise RuntimeError(f"NotebookLM is not configured for domain '{domain}'.")
    distiller = globals()[f"_distill_{domain}"]
    return await distiller(notebook_id, auth_json, api_key, status_holder)


async def save_domain(domain: str, rows: list[dict], api_key: str) -> int:
    """Persist validated rows. gear appends new rows without touching existing ones (its
    source is incremental discovery, not a full catalog sweep); nutrition/scheduler fully
    replace; scheduler also reindexes Qdrant."""
    import db

    if domain == "gear":
        saved = db.add_kb_chunks(domain, rows)
        export_seed(domain, db.get_kb_chunks(domain, kind="catalog_item"))  # full current catalog, not just new rows
        print(f"[KBDistiller] 'gear' web discovery: {saved} new chunks added, seed exported.")
        return saved
    saved = db.replace_kb_chunks(domain, rows)
    export_seed(domain, rows)
    if domain == "scheduler":
        from services.kb_retrieval import reindex_scheduler_chunks

        await asyncio.to_thread(reindex_scheduler_chunks, rows, api_key)
    print(f"[KBDistiller] '{domain}' distilled: {saved} chunks saved, seed exported.")
    return saved


async def distill_domain(domain: str, api_key: str, status_holder: dict) -> int:
    """Sweep one domain's source -> validate -> save. Thin composition used by both
    the FastAPI admin endpoint and the Airflow DAG."""
    rows = await sweep_domain(domain, api_key, status_holder)
    if not rows and domain != "gear":
        raise RuntimeError(f"Distillation produced an empty result for '{domain}' — keeping existing KB.")
    rows = validate_domain_rows(domain, rows)
    return await save_domain(domain, rows, api_key)


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
