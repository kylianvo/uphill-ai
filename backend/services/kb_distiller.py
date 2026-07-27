"""Distills gear/nutrition/scheduler content into kb_chunks rows + committed seed files.

Offline batch job, triggered by POST /api/kb/distill or the Airflow kb_distill DAG. Two
source types feed it: NotebookLM sweeps (operator-curated notebooks, still used for
scheduler's training-philosophy principles and nutrition's science principles) and live
web discovery via Tavily (gear's shoe catalog, nutrition's product catalog) -- both are
structured through Gemini (temperature 0) into the same row shape. Rows land in Postgres
(kb_chunks), get exported to backend/kb_seed/<domain>.json (committed so prod imports
without re-distilling), and scheduler chunks are embedded into Qdrant. NotebookLM-sourced
content fully replaces its (domain, kind) on each run; web-discovered content only appends
new rows, since a search naturally surfaces what's new rather than a full catalog.
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


def _whitelisted_brand(returned_brand: str, queried_brand: str, allowed_brands: list[str] = GEAR_BRANDS) -> str | None:
    """Keep only whitelisted brands. The per-brand sweep text may mention
    competitors (review comparisons), and Gemini may restyle the brand name
    (e.g. 'HOKA ONE ONE' for the 'Hoka' query) — coerce those to the queried
    brand; drop anything else. `allowed_brands` defaults to GEAR_BRANDS but any
    domain with its own whitelist (e.g. nutrition) passes its own list."""
    returned = (returned_brand or "").strip()
    allowed = {b.lower(): b for b in allowed_brands}
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
# Floors apply only to each domain's fully-resweepable source: nutrition's floor
# checks its NotebookLM-sourced principle rows (3 topics -> ~3-9 principle rows
# expected), not its incrementally-appended web-discovered product rows.
_MIN_ROWS = {"nutrition": 3, "scheduler": 15}


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


def _known_titles(domain: str, kind: str) -> set[str]:
    import db

    return {row["title"].lower() for row in db.get_kb_chunks(domain, kind=kind)}


async def discover_gear_web(api_key: str, tavily_api_key: str, status_holder: dict) -> list[dict]:
    """Search RunRepeat/BelieveInTheRun for new reviews of whitelisted gear brands, skip
    results matching an already-known shoe, structure the rest with Gemini. Incremental —
    an empty result (no new shoes this week) is a normal, valid outcome."""
    client = TavilyClient(api_key=tavily_api_key)
    known_titles = _known_titles("gear", "catalog_item")
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


# Operator-curated whitelist, same role as GEAR_BRANDS: scopes web search to brands
# already trusted in this KB and coerces Gemini's brand restyling back to a canonical
# name. Sourced from the brands already present in the committed nutrition seed.
NUTRITION_BRANDS = [
    "GU",
    "Maurten",
    "Tailwind Nutrition",
    "Hammer Nutrition",
    "Science in Sport (SiS)",
    "Precision Fuel & Hydration",
    "Näak",
    "Bix",
]


# Nutrition brands' official sites vary (no fixed include_domains list is possible,
# unlike gear's two review sites) -- exclude social/UGC platforms instead, since a
# brand announcement there is unreliable/unverifiable compared to a retailer, review
# site, or the brand's own site, all of which Tavily naturally surfaces higher anyway.
_NUTRITION_EXCLUDED_DOMAINS = [
    "facebook.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "reddit.com",
    "youtube.com",
    "pinterest.com",
    "tiktok.com",
]


_NUTRITION_PRODUCT_ASK = (
    "Structure every properly-described sports nutrition product (gel, drink mix, chew, bar) in this "
    "text into the schema. ONLY include products with real detail in the text — skip products merely "
    "mentioned in passing. For each: exact product name; format; carbs per unit (g); sodium per unit "
    "(mg); protein per unit (g); any technology/science notes. If the text doesn't state a numeric "
    "value, use 0 rather than guessing. NEVER add a product or macro figure not present in the text. "
    "Write every field in clear English only — never any other language.\n\nArticle:\n"
)


async def discover_nutrition_web(api_key: str, tavily_api_key: str, status_holder: dict) -> list[dict]:
    """Search the web for new products from whitelisted nutrition brands, skip results
    matching an already-known product, structure the rest with Gemini. Incremental --
    an empty result (no new products this week) is a normal, valid outcome. Unlike
    gear's discover_gear_web, this doesn't restrict to a fixed set of review sites --
    nutrition brands publish new products on their own (varied) official sites, so
    search only excludes low-reliability social/UGC platforms (_NUTRITION_EXCLUDED_DOMAINS)
    rather than allowlisting specific sites, and relies on the brand whitelist + per-row
    brand coercion below to keep results on-topic."""
    client = TavilyClient(api_key=tavily_api_key)
    known_titles = _known_titles("nutrition", "catalog_item")
    rows: list[dict] = []

    for i, brand in enumerate(NUTRITION_BRANDS):
        status_holder.update(
            {"current_topic": f"nutrition web: {brand}", "progress": i, "total": len(NUTRITION_BRANDS)}
        )
        try:
            response = await asyncio.to_thread(
                client.search,
                f"{brand} new sports nutrition product 2026",
                exclude_domains=_NUTRITION_EXCLUDED_DOMAINS,
                max_results=5,
                include_raw_content="markdown",
            )
        except Exception as e:
            print(f"[KBDistiller][nutrition-web] Search failed for '{brand}', continuing: {e}")
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
                structured = await _gemini_structured(api_key, _NUTRITION_PRODUCT_ASK + content, ProductList)
            except Exception as e:
                print(f"[KBDistiller][nutrition-web] Structuring failed for '{result.get('url')}', continuing: {e}")
                continue
            source_label = urlparse(result.get("url", "")).netloc.removeprefix("www.")
            for product in structured.get("products", []):
                brand_final = _whitelisted_brand(product.get("brand", brand), brand, allowed_brands=NUTRITION_BRANDS)
                if brand_final is None:
                    continue
                product["brand"] = brand_final
                name = (product.get("name") or "").strip()
                if not name:
                    continue
                if name.lower().startswith(brand_final.lower() + " "):
                    # Gemini sometimes repeats the brand inside the product name
                    name = name[len(brand_final) :].strip()
                product["name"] = name  # keep payload consistent so UIs don't show "GU GU Roctane"
                title = f"{brand_final} {name}".strip()
                if title.lower() in known_titles:
                    continue  # post-structure dedup: article title didn't match, structured name did
                known_titles.add(title.lower())
                rows.append(
                    {
                        "domain": "nutrition",
                        "kind": "catalog_item",
                        "title": title,
                        "content": f"{title}: {product.get('tech_notes', '')}",
                        "payload": product,
                        "source_label": source_label,
                    }
                )
        await asyncio.sleep(1.5)  # search-API rate-limit courtesy, same pacing as the NotebookLM sweeps
    return rows


# Nutrition products are now sourced by discover_nutrition_web (live web search) --
# this function only sweeps NotebookLM for the nutrition-science principle topics
# (carb/sodium/pre-race guidance), which is curated philosophy content rather than
# a product catalog and stays on the operator-curated NotebookLM path.
async def _distill_nutrition(notebook_id: str, auth_json: str, api_key: str, status: dict) -> list[dict]:
    rows: list[dict] = []
    total = len(NUTRITION_PRINCIPLE_TOPICS)
    for j, topic in enumerate(NUTRITION_PRINCIPLE_TOPICS):
        status.update({"current_topic": f"nutrition principle {j + 1}", "progress": j, "total": total})
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
    nutrition (hybrid): the floor applies only to its NotebookLM-sourced principle rows
    (a broad-sweep-failure signal); its web-discovered catalog_item rows pass through
    unfiltered — 0 new products this week is a normal, valid outcome, same as gear.
    scheduler (full-replace): below-floor row counts mean the sweep likely hit a
    broad NotebookLM outage/refusal — raise rather than replace a working KB with junk."""
    if domain == "gear":
        return [r for r in rows if _shoe_richness(r.get("payload") or {}) >= _MIN_AVG_RICHNESS]
    if domain == "nutrition":
        principle_rows = [r for r in rows if r.get("kind") == "principle"]
        catalog_rows = [r for r in rows if r.get("kind") == "catalog_item"]
        floor = _MIN_ROWS["nutrition"]
        if len(principle_rows) < floor:
            raise RuntimeError(
                f"Distillation produced only {len(principle_rows)} principle rows for 'nutrition' "
                f"(floor {floor}) — keeping existing KB."
            )
        return principle_rows + catalog_rows
    floor = _MIN_ROWS.get(domain)
    if floor is not None and len(rows) < floor:
        raise RuntimeError(
            f"Distillation produced only {len(rows)} rows for '{domain}' (floor {floor}) — keeping existing KB."
        )
    return rows


async def sweep_domain(domain: str, api_key: str, status_holder: dict) -> list[dict]:
    """Dispatch to this domain's data source(s). gear discovers from the live web
    (RunRepeat/BelieveInTheRun via Tavily). nutrition combines both: NotebookLM for its
    curated principle rows, plus live web discovery (Tavily) for new products -- if
    TAVILY_API_KEY isn't configured, nutrition still proceeds with principles alone.
    scheduler still sweeps NotebookLM only."""
    if domain == "gear":
        if not settings.TAVILY_API_KEY:
            raise RuntimeError("TAVILY_API_KEY is not configured.")
        return await discover_gear_web(api_key, settings.TAVILY_API_KEY, status_holder)
    if domain == "nutrition":
        notebook_id, auth_json = _notebook_id(domain), settings.NOTEBOOKLM_AUTH_JSON
        if not notebook_id or not auth_json:
            raise RuntimeError("NotebookLM is not configured for domain 'nutrition'.")
        principle_rows = await _distill_nutrition(notebook_id, auth_json, api_key, status_holder)
        if not settings.TAVILY_API_KEY:
            print("[KBDistiller][nutrition] TAVILY_API_KEY not configured — skipping web product discovery.")
            return principle_rows
        web_rows = await discover_nutrition_web(api_key, settings.TAVILY_API_KEY, status_holder)
        return principle_rows + web_rows
    notebook_id, auth_json = _notebook_id(domain), settings.NOTEBOOKLM_AUTH_JSON
    if not notebook_id or not auth_json:
        raise RuntimeError(f"NotebookLM is not configured for domain '{domain}'.")
    distiller = globals()[f"_distill_{domain}"]
    return await distiller(notebook_id, auth_json, api_key, status_holder)


_SEED_KEYS = ("domain", "kind", "title", "content", "payload", "source_label")


async def save_domain(domain: str, rows: list[dict], api_key: str) -> int:
    """Persist validated rows. gear appends new rows without touching existing ones (its
    source is incremental discovery, not a full catalog sweep). nutrition is hybrid: its
    principle rows fully replace (NotebookLM re-sweep), its catalog_item rows append
    (web discovery) -- neither wipes the other. scheduler fully replaces and reindexes
    Qdrant."""
    import db

    if domain == "gear":
        saved = db.add_kb_chunks(domain, rows)
        # full current catalog, not just new rows — project down to the six clean seed
        # fields so machine-specific id/content_hash/created_at never leak into the
        # committed, human-editable seed file.
        clean_rows = [{k: row[k] for k in _SEED_KEYS} for row in db.get_kb_chunks(domain, kind="catalog_item")]
        export_seed(domain, clean_rows)
        print(f"[KBDistiller] 'gear' web discovery: {saved} new chunks added, seed exported.")
        return saved
    if domain == "nutrition":
        principle_rows = [r for r in rows if r.get("kind") == "principle"]
        catalog_rows = [r for r in rows if r.get("kind") == "catalog_item"]
        saved = db.replace_kb_chunks_by_kind(domain, "principle", principle_rows)
        saved += db.add_kb_chunks(domain, catalog_rows)
        # full current catalog (principles + products), same clean-projection reasoning as gear
        clean_rows = [{k: row[k] for k in _SEED_KEYS} for row in db.get_kb_chunks(domain)]
        export_seed(domain, clean_rows)
        print(f"[KBDistiller] 'nutrition': {saved} chunks saved (principles replaced, products appended).")
        return saved
    saved = db.replace_kb_chunks(domain, rows)
    export_seed(domain, rows)
    if domain == "scheduler":
        from services.kb_retrieval import reindex_scheduler_chunks

        await asyncio.to_thread(reindex_scheduler_chunks, rows, api_key)
    print(f"[KBDistiller] '{domain}' distilled: {saved} chunks saved, seed exported.")
    return saved


async def distill_domain(domain: str, api_key: str, status_holder: dict) -> int:
    """Sweep one domain's source -> validate -> save. Thin composition used by the FastAPI
    admin endpoint; the Airflow DAG reimplements this same composition across its own tasks."""
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
