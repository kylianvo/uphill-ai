# Gear Finder Catalog Trim Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cut Gear Finder latency by sending Gemini fewer catalog tokens, without letting a shoe the athlete could want drop out of the prompt.

> **Outcome (2026-10-09):** Task 1 shipped as a **cost** change, not a speed change. On the 12 gear golden fixtures the filter cut prompt size 30–87% (101 → 71 road / 47 trail / 11–12 with a brand) with the gate still passing, but median latency stayed ~10s (10.2s before, 10.0s after); run-to-run noise on the same fixture was several seconds, larger than any input-size effect. Gear's latency is dominated by its ~1,050 output tokens and API variance, not by the catalog. Task 2 (dropping prose fields) rests on the same input-size premise and was not done. Next speed lever, if wanted: shorter output (fewer recommendations or shorter pros/cons).

**Architecture:** Today every request sends all 101 catalog entries with every field (~35k input tokens; production p50 19.7s, p95 45s, model call p50 13.3s, 0 thinking tokens, 0 cached tokens). Two independent cuts, each measured on the gear golden set: (1) a **surface prefilter** in a new `services/gear_catalog.py`: a road request drops trail-only shoes and vice versa, a brand request keeps only those brands when enough match, and any filter that would leave too few entries falls back to the full catalog; (2) **dropping two prose fields** (`overview`, `highlights`, 22% of catalog text) that restate fields the prompt already sends. Field trimming is a separate task because it can change answer quality; it ships only if the golden compare holds.

Not in this plan: Gemini context caching. The catalog is already the prompt's prefix, but gear sees ~7 requests in two weeks and the implicit cache lives minutes, so production shows 0 cached tokens; an explicit cache would bill storage around the clock for a handful of calls.

**Tech Stack:** FastAPI service `services/gear_planner.py`, `google-genai`, `kb_chunks` catalog (`kb_seed/gear.json`, 101 `catalog_item` rows), Langfuse via `services/observability.py`, `scripts/golden_eval.py --service gear` (11 fixtures with `.ref.json` baselines).

## Global Constraints

- The prompt text (`GEAR_FINDER_PROMPT`) does not change; only the `{{catalog_context}}` value shrinks. Still an LLM-behaviour change: follow `.claude/skills/llm-change-process/SKILL.md` (golden compare before and after, checklist in the PR).
- The gear gate must stay green: no recommendation outside the catalog.
- Never filter the catalog down to fewer than `MIN_ENTRIES = 12`; fall back to the full catalog instead. Unclassifiable entries (no terrain info) are always kept.
- The hallucination guard (`quality_signals.score_recommendations`) keeps checking against the **full** catalog titles.
- `catalog_entries` (already an allowed Langfuse metadata key) records the number of entries actually sent.
- Surface values sent by clients: `"road"`, `"trail"`, `"mixed"`, or none (iOS `GearVaultSheet`, golden fixtures).
- No staging: deploy to production by hand (user runs it; auto mode blocks Claude's production writes).

## Baseline (production, 2026-09-25 → 10-09, 7 requests)

| Gear finder | p50 | p95 |
|---|---|---|
| Whole request | 19.7s | 45.0s |
| Gemini call | 13.3s | 22.2s |
| Input tokens | 35,042 | 35,044 |
| Output tokens | 1,052 | 1,086 |

Catalog: 101 entries; by terrain text 54 road, 30 trail, 17 both. A road request would send 71 entries, a trail request 47.

## File Structure

- Create `backend/services/gear_catalog.py`: `surface_of`, `filter_catalog`, `slim_entry` (one responsibility: choose what of the catalog goes into the prompt).
- Modify `backend/services/gear_planner.py:139-176`: filter (and later slim) before `render_catalog_context`; log the sent count.
- Create `backend/tests/unit/test_gear_catalog.py`; extend `backend/tests/unit/test_gear_planner.py`.

---

### Task 1: Surface and brand prefilter

**Files:**
- Create: `backend/services/gear_catalog.py`
- Create: `backend/tests/unit/test_gear_catalog.py`
- Modify: `backend/services/gear_planner.py` (`_generate_with_gemini`)
- Test: `backend/tests/unit/test_gear_planner.py`

**Interfaces:**
- Produces:
  - `surface_of(payload: dict) -> Literal["road", "trail", "both", "unknown"]`
  - `filter_catalog(chunks: list[dict], surface: str | None, preferred_brands: str | None) -> list[dict]`
  - `MIN_ENTRIES = 12`, `MIN_BRAND_ENTRIES = 5`

- [ ] **Step 0: Golden baseline on current code** (before any change; needs `GEMINI_API_KEY` in `backend/.env` and the gear catalog in the local Postgres `kb_chunks`, e.g. `python scripts/load_kb.py --domain gear` against a scratch DB; ~11 Gemini calls)

Run: `python scripts/golden_eval.py compare --service gear`
Expected: `[gate] PASS gear`. Save `tests/golden/report_gear.md` as `report_gear.before.md` outside the repo (reports are gitignored) for the PR.

- [ ] **Step 1: Write the failing tests** (`tests/unit/test_gear_catalog.py`)

```python
from services.gear_catalog import MIN_ENTRIES, filter_catalog, surface_of


def _chunk(name, terrain=None, brand="Hoka"):
    payload = {"brand": brand}
    if terrain is not None:
        payload["terrain"] = terrain
    return {"title": name, "payload": payload}


def test_surface_of_reads_the_terrain_text():
    assert surface_of({"terrain": ["Road", "treadmill"]}) == "road"
    assert surface_of({"terrain": ["Technical trail", "Mud"]}) == "trail"
    assert surface_of({"terrain": ["Gravel", "Road-to-trail"]}) == "both"
    assert surface_of({"terrain": "Smoother singletrack"}) == "trail"
    assert surface_of({}) == "unknown"


def _catalog():
    road = [_chunk(f"road{i}", ["Road"]) for i in range(20)]
    trail = [_chunk(f"trail{i}", ["Technical trail"]) for i in range(15)]
    both = [_chunk(f"both{i}", ["Road-to-trail"]) for i in range(5)]
    unknown = [_chunk("mystery")]
    return road + trail + both + unknown


def test_road_request_drops_trail_only_shoes():
    names = {c["title"] for c in filter_catalog(_catalog(), "road", None)}
    assert "trail0" not in names
    assert {"road0", "both0", "mystery"} <= names
    assert len(names) == 26


def test_mixed_or_missing_surface_keeps_everything():
    assert len(filter_catalog(_catalog(), "mixed", None)) == 41
    assert len(filter_catalog(_catalog(), None, None)) == 41


def test_brand_filter_applies_only_when_enough_entries_match():
    catalog = _catalog() + [_chunk(f"sal{i}", ["Technical trail"], brand="Salomon") for i in range(6)]
    salomon = filter_catalog(catalog, "trail", "Salomon")
    assert {c["payload"]["brand"] for c in salomon} == {"Salomon"}

    few = _catalog() + [_chunk("nb1", ["Technical trail"], brand="New Balance")]
    kept = filter_catalog(few, "trail", "New Balance")
    assert len(kept) > 1  # one match is too few: the prompt's "no match" rule needs the rest


def test_too_small_a_result_falls_back_to_the_full_catalog():
    small = [_chunk(f"road{i}", ["Road"]) for i in range(5)] + [_chunk(f"trail{i}", ["Trail"]) for i in range(20)]
    assert len(filter_catalog(small, "road", None)) == len(small)
    assert MIN_ENTRIES == 12
```

- [ ] **Step 2: Run to verify they fail**

Run: `pytest tests/unit/test_gear_catalog.py -q`
Expected: `ModuleNotFoundError: No module named 'services.gear_catalog'`

- [ ] **Step 3: Implement** (`services/gear_catalog.py`)

```python
"""Choose which gear catalog entries go into the Gear Finder prompt.

The whole catalog used to be sent on every request (~35k tokens). A road request
never needs trail-only shoes and vice versa; entries we can't classify are always
kept, and any filter that leaves too little falls back to the full catalog.
"""

import json
from typing import Any, Literal

MIN_ENTRIES = 12
MIN_BRAND_ENTRIES = 5

_TRAIL_WORDS = ("trail", "singletrack", "mountain", "technical", "mud", "gravel", "rock", "fell", "sky")
_ROAD_WORDS = ("road", "treadmill", "pavement")


def _payload(chunk: dict[str, Any]) -> dict[str, Any]:
    payload = chunk.get("payload") or {}
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except ValueError:
            return {}
    return payload if isinstance(payload, dict) else {}


def surface_of(payload: dict[str, Any]) -> Literal["road", "trail", "both", "unknown"]:
    terrain = payload.get("terrain")
    text = " ".join(terrain) if isinstance(terrain, list) else str(terrain or "")
    text = text.lower()
    road = any(w in text for w in _ROAD_WORDS)
    trail = any(w in text for w in _TRAIL_WORDS)
    if road and trail:
        return "both"
    if road:
        return "road"
    if trail:
        return "trail"
    return "unknown"


def filter_catalog(chunks: list[dict[str, Any]], surface: str | None, preferred_brands: str | None) -> list[dict[str, Any]]:
    wanted = (surface or "").strip().lower()
    if wanted in ("road", "trail"):
        excluded = "trail" if wanted == "road" else "road"
        by_surface = [c for c in chunks if surface_of(_payload(c)) != excluded]
        if len(by_surface) < MIN_ENTRIES:
            by_surface = chunks
    else:
        by_surface = chunks

    brands = [b.strip().lower() for b in (preferred_brands or "").split(",") if b.strip()]
    if brands:
        by_brand = [c for c in by_surface if str(_payload(c).get("brand", "")).strip().lower() in brands]
        if len(by_brand) >= MIN_BRAND_ENTRIES:
            return by_brand
    return by_surface
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/unit/test_gear_catalog.py -q`
Expected: 5 passed. If `surface_of` misclassifies a real entry, check the real catalog: `python -c "import json,collections; from services.gear_catalog import surface_of; d=json.load(open('kb_seed/gear.json')); rows=d if isinstance(d,list) else d.get('chunks') or d.get('rows'); print(collections.Counter(surface_of(r.get('payload') or {}) for r in rows if r.get('kind')=='catalog_item'))"` should print about 54 road / 30 trail / 17 both / 0 unknown.

- [ ] **Step 5: Write the failing integration test** (append to `tests/unit/test_gear_planner.py`)

```python
def test_road_request_sends_only_road_capable_catalog_entries(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key")
    fake_client = _mock_gemini_client(GEAR_JSON)
    chunks = [{"title": f"Road {i}", "payload": {"brand": "Nike", "terrain": ["Road"]}} for i in range(12)] + [
        {"title": "Speedgoat 7", "payload": {"brand": "Hoka", "terrain": ["Technical trail"]}}
    ]
    with (
        patch("db.get_kb_chunks", return_value=chunks),
        patch("google.genai.Client", return_value=fake_client),
    ):
        asyncio.run(gp.gear_planner.generate_plan("", GearParams(surface="road")))
    prompt_sent = fake_client.models.generate_content.call_args.kwargs["contents"]
    assert "Road 0" in prompt_sent
    assert "Speedgoat 7" not in prompt_sent
```

- [ ] **Step 6: Run to verify it fails**

Run: `pytest tests/unit/test_gear_planner.py -q -k road_capable`
Expected: FAIL (`"Speedgoat 7" in prompt_sent`)

- [ ] **Step 7: Wire it in** (`gear_planner.py`, `_generate_with_gemini`)

```python
        from services.gear_catalog import filter_catalog
```

Replace `catalog_context = render_catalog_context(chunks, "gear")` with:

```python
        sent = filter_catalog(chunks, params.surface, params.preferred_brands)
        catalog_context = render_catalog_context(sent, "gear")
```

and change the two `"catalog_entries": len(chunks)` (trace metadata and the `prompt_sent` log) to `len(sent)`. Leave `quality_signals.score_recommendations(..., [c["title"] for c in chunks], ...)` on the full `chunks`.

- [ ] **Step 8: Run unit tests**

Run: `pytest tests/unit -q`
Expected: all PASS

- [ ] **Step 9: Golden compare after**

Run: `python scripts/golden_eval.py compare --service gear`
Expected: `[gate] PASS gear`. Compare with the Step 0 report: per-fixture latency, and that each fixture's recommendations still fit its criteria (brand, surface, budget). Record median latency before/after for the PR.

- [ ] **Step 10: Commit**

```bash
git add backend/services/gear_catalog.py backend/services/gear_planner.py backend/tests/unit/test_gear_catalog.py backend/tests/unit/test_gear_planner.py
git commit -m "perf(gear): send only surface- and brand-relevant catalog entries"
```

---

### Task 2: Drop restating prose fields (measured; keep only if quality holds)

**Files:**
- Modify: `backend/services/gear_catalog.py`, `backend/services/gear_planner.py`
- Test: `backend/tests/unit/test_gear_catalog.py`

**Interfaces:**
- Produces: `slim_entry(chunk: dict) -> dict` (same chunk with `overview` and `highlights` removed from its payload); `DROPPED_FIELDS = ("overview", "highlights")`.

`overview` (15%) and `highlights` (7%) are free-text summaries of what the structured fields (`intended_use`, `best_for`, `suitability`, `pros`, `cons`, `terrain`, `cushioning`) already say. `pros`/`cons` stay: the answer's own pros/cons are written from them.

- [ ] **Step 1: Write the failing test** (append to `tests/unit/test_gear_catalog.py`)

```python
def test_slim_entry_drops_only_the_restating_prose():
    from services.gear_catalog import slim_entry

    chunk = {"title": "X", "payload": {"brand": "Hoka", "overview": "long", "highlights": "long", "pros": "p", "cons": "c"}}
    slim = slim_entry(chunk)
    assert slim["payload"] == {"brand": "Hoka", "pros": "p", "cons": "c"}
    assert chunk["payload"]["overview"] == "long"  # input not mutated
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest tests/unit/test_gear_catalog.py -q -k slim`
Expected: `ImportError: cannot import name 'slim_entry'`

- [ ] **Step 3: Implement** (append to `gear_catalog.py`)

```python
DROPPED_FIELDS = ("overview", "highlights")


def slim_entry(chunk: dict[str, Any]) -> dict[str, Any]:
    payload = {k: v for k, v in _payload(chunk).items() if k not in DROPPED_FIELDS}
    return {**chunk, "payload": payload}
```

In `gear_planner.py`: `from services.gear_catalog import filter_catalog, slim_entry` and
`catalog_context = render_catalog_context([slim_entry(c) for c in sent], "gear")`.

- [ ] **Step 4: Run unit tests**

Run: `pytest tests/unit -q`
Expected: all PASS

- [ ] **Step 5: Golden compare**

Run: `python scripts/golden_eval.py compare --service gear`
Expected: `[gate] PASS gear`. Keep this task only if, versus Task 1's report, recommendations still match each fixture's criteria and pros/cons stay specific to the shoe. If quality drops, revert this task's commit and ship Task 1 alone.

- [ ] **Step 6: Commit**

```bash
git add backend/services/gear_catalog.py backend/services/gear_planner.py backend/tests/unit/test_gear_catalog.py
git commit -m "perf(gear): drop overview and highlights from the prompt catalog"
```

---

### Task 3: PR, production deploy, measure

**Files:** none.

- [ ] **Step 1: Open the PR** with the `llm-change-process` checklist, before/after golden latency and gate results, and the baseline table above.

- [ ] **Step 2: Deploy by hand** (user runs). Files: `services/gear_catalog.py` (new), `services/gear_planner.py`. Check production's `gear_planner.py` matches `main` first, back up it and `backend/.env`, copy both files, set `LANGFUSE_RELEASE` to the PR head SHA, `docker compose restart backend`, wait for `/api/health` 200, diff env keys.

- [ ] **Step 3: Smoke test:** run Gear Finder in the app 4 times with different inputs: trail + no brand, road + budget, trail + one brand (e.g. Salomon), mixed surface. Each must return 5 recommendations that exist in the catalog.

- [ ] **Step 4: Measure** (Langfuse, `environment = production`, `traceName = gear_finder`, release = deployed SHA): input tokens p50, `GenerateContent` and `gear_finder` latency p50/p95, `catalog_entries`; and the `catalog_valid` score stays 1. Post before/after on the PR.

  Success: input tokens down at least 30% for road/trail requests, Gemini call p50 below 10s, `catalog_valid` unchanged.
