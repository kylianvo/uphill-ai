# race_courses KB seed

`race_courses.json` is a new KB domain (35 races: Vietnam, Australia, ASEAN, and Asia trail + road races) built to give the Scheduler and Gear Finder course-specific context — distances, elevation gain/loss, terrain, key climbs, climate, and runner reviews — matched against a user's race name + distance input.

It follows the same `{"domain", "chunks": [{"domain", "kind", "title", "content", "payload", "source_label"}]}` shape as `gear.json` / `nutrition.json` / `scheduler.json`, so it loads through the existing `kb_distiller.load_seed()` / `db.replace_kb_chunks()` path unchanged. Each chunk's `payload` carries structured fields (`race_name`, `aliases`, `distances[]`, `terrain[]`, `key_climbs[]`, `climate`, `runner_reviews[]`, `matching_hints`) in the same style as a `gear` catalog_item, so `services/kb_context.py:render_catalog_context()` can inject it into a prompt exactly like the gear/nutrition catalogs (full-catalog injection — only 29 rows, no retrieval-miss risk).

**This file is data only.** To actually wire it into the app, the following code changes are still needed (not done here — these are product/engineering decisions for you to make):

1. **Add `"race_courses"` to `DOMAINS`** in `services/kb_distiller.py` and register it with `db.replace_kb_chunks` / `load_seed` (no NotebookLM notebook needed for this domain — it's hand-curated, so you'd add a `load_seed("race_courses")` call at startup/import time rather than a `_distill_race_courses` sweep function).
2. **Capture race name + distance from the user.** Neither `PlanGenerator` (`services/plan_generator.py`) nor `GearParams` (`services/gear_planner.py`) currently store a race *name* — `GearParams.race_distance` is a free-text string only. You'll want a `race_name` (and maybe `race_location`) field on the onboarding/profile data and on `GearParams`/plan-generation params.
3. **Matching logic.** With only 29 rows, simplest is fuzzy string matching in Python (e.g. check `race_name`/`aliases`/`matching_hints.name_keywords` against the user's free-text race name, and `distances[].distance_km` against the user's stated distance) rather than embedding/Qdrant retrieval — Gemini can also be handed the injected catalog and asked to pick the closest match itself, mirroring how Gear/Nutrition let the model filter the full injected catalog.
4. **Prompt injection point.** Once matched, feed the single matched chunk's `content` (dense prose) into the Scheduler's plan-generation prompt (for terrain/climate-aware workout design — e.g. heat acclimation, technical-descent conditioning, vert-matched hill repeats) and into the Gear Finder prompt (terrain/climate → shoe traction, drainage, and toe-box needs).
5. **Freshness**: elevation/distance figures for UTMB-affiliated races (Thailand, Malaysia, Amazean, Vietnam Highlands) can shift between seasons as courses get re-routed — worth re-verifying before a season's onboarding cohort relies on them, same caveat that applies to any hand-curated seed.

## Coverage (35 races)

Vietnam trail: VMM (Sa Pa), Dalat Ultra Trail, Vietnam Trail Marathon (Mộc Châu), Vietnam Jungle Marathon (Pù Luông), Vietnam Ultra Marathon (Mai Châu), Vietnam Highlands Trail by UTMB (Đà Lạt), Prenn Trail (Đà Lạt), Lâm Đồng Trail (Đà Lạt), Phong Nha Wild Trail/Quảng Bình Discovery Marathon, Cúc Phương Jungle Paths, Ultra Trail Cao Bằng, Mù Cang Chải Ultra Trail.
Vietnam road: Techcombank HCMC Marathon, VnExpress Marathon (Quy Nhơn/Huế/Hải Phòng), VnExpress Marathon Đà Nẵng.
Australia trail: UTA (Blue Mountains/Furber Steps), Ultra-Trail Kosciuszko, Buffalo Stampede, Six Foot Track.
Australia road: Sydney Marathon, Great Ocean Road Marathon, Melbourne Marathon, Gold Coast Marathon.
ASEAN/Asia trail: Thailand by UTMB (Chiang Mai), Malaysia by UTMB, Amazean Jungle Thailand by UTMB (Betong), Rinjani 100 (Lombok), HK100, TNF100 (Philippines), UTMF (Mt. Fuji), Hasetsune Cup (Japan), Bromo Marathon (Java), XTERRA Zhangjiajie (China).
ASEAN road: Angkor Wat International Half Marathon (Cambodia), Standard Chartered Singapore Marathon.

## `results` block schema (past-results benchmarks)

Optional per-race, hand-verified (or verified-scrape) past results consumed by
the Pace Strategy benchmark markers and the Goal Determiner field curve. One
entry per year × distance:

```json
"results": [{
  "year": 2025,
  "distance_label": "UTA100", "distance_km": 100.4,
  "finishers": 1282, "finishers_men": 1013, "finishers_women": 269,
  "winner_time": "9:26:02", "winner_time_women": "10:55:19",
  "top_times": {
    "overall": {"top3": "h:mm:ss", "top5": "…", "top10": "…", "top20": "…"},
    "men": {"…"}, "women": {"…"}
  },
  "percentiles": {
    "overall": {"p5": "h:mm:ss", "p10": "…", "p25": "…", "p50": "…", "p75": "…", "p90": "…"},
    "men": {"…"}, "women": {"…"}
  },
  "cutoff_clock": "optional free text",
  "conditions_note": "optional free text",
  "source": "where the numbers were verified"
}]
```

Conventions (keep scrapers consistent with these):
- `topN` = the finish time of the rank-N finisher **within that group** (so
  `women.top3` is the 3rd woman). Omit `topN` keys when the group has fewer
  than N finishers.
- `pN` = the finish time of the finisher at rank `ceil(N% × group size)`.
- Times are `h:mm:ss` strings; groups are exactly `overall`/`men`/`women`;
  omit any group or field you could not verify — the UI degrades gracefully,
  and **no value may ever be estimated or interpolated at curation time**.
- Store per-year entries; don't average across years (weather and course
  changes make the variance informative).
