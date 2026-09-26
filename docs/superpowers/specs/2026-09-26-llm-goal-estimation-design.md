# LLM Goal Estimation — Design

Date: 2026-09-26
Status: approved in brainstorming, pending implementation plan

## Problem

1. The plan page shows an "After this block: scenario" block (`RaceHistoryPlanInfo.tsx`, backed by
   `race_history.scenarios()`). It computes its own prediction — nearest-distance trail result, synthetic
   uniform-grade course, no terrain, no GPX, no percentile blend, flat 0.25%/week improvement — so it
   disagrees with both the Goal Determiner and the plan's own Time Target (e.g. "8:28" shown directly above
   "Time Target (7h 40m)"), with nothing explaining the gap. It looks unlike the rest of the plan card.
2. The Goal Determiner (`main.py:_goal_estimate_core` + `services/race_estimator.py`) is purely local maths
   over a single reference result. It ignores most of what we now know about the athlete: full race
   history, UTMB index, physiology, watch trends, and training-block execution.

## Decisions (from brainstorming)

| # | Decision |
|---|----------|
| Q1 | Output is A/B/C goals (ambitious / realistic / safe) chosen by the LLM with visible reasoning. **No accuracy claim** in product copy. |
| Q2 | **Hybrid, LLM-as-judge**: deterministic engine computes numeric anchors; Gemini weighs anchors + qualitative context and picks A/B/C; code validates; deterministic A/B/C is the fallback. |
| Q3 | Runs at two moments: **pre-plan** (Goal Determiner → fills Time Target) and **during plan** (on demand + at most once per completed week). Drift >3% from Time Target produces a suggestion; the target never changes without athlete confirmation. |
| Q4 | Thin data → still estimate, `confidence: low`, wider spread, explicit "missing" hints, capped by field range. |
| Q5 | Green block removed. Plan header gets a **Goal pill** next to "Coach notes", opening a panel in the same style. |
| Q6 | Goal Determiner becomes **context-first with overrides** when signed in; manual inputs remain for signed-out / pre-signup onboarding. |
| Q7 | Launch gated by a **backtest** on real `race_results`; live hit rate tracked after launch. |

Defaults taken without asking (overrule in review): coach mode mirrors the athlete flow; reasoning is
generated in the athlete's `lang`; the athlete's own Gemini key takes precedence (as in chat); manual
re-assess is limited to 3/day.

## Architecture

```
goal_context.gather(user, race, plan?, exclusions)
    profile · physiology · race_results · UTMB index
    watch trends (activities, daily_metrics)
    block progress (matching/block_evaluator, plan only)
    race KB profile + field benchmarks + GPX course profile
        │
        ▼
goal_anchors.compute(ctx) → anchors[]
        │
        ▼
goal_judge.assess(ctx, anchors) → Gemini JSON → validate → 1 reduced retry → deterministic fallback
        │
        ▼
goal_assessments row → Goal Determiner modal / plan-header Goal pill
```

### Units

- **`services/goal_context.py`** — gathers and trims all inputs into one typed structure; applies the
  athlete's exclusions (result ids / source keys). No LLM, no maths. Each source is fetched independently;
  a failing source is skipped and recorded in `missing`.
- **`services/goal_anchors.py`** — the numeric engine, moved out of `main.py:_goal_estimate_core`
  (race matching, GPX/terrain, percentile transfer, rank transfer, variant filtering). Changes vs today:
  - one **physics anchor per usable result** (not just one reference);
  - percentile/rank-transfer anchors per result when benchmarks exist for both races;
  - a **field-position prior** anchor for thin-data athletes (field percentile from weekly volume and
    experience, mapped onto the target race's curve);
  - each anchor carries `id`, `method`, `source_result_id`, `minutes`, and `quality_notes`
    (age, distance gap, road-vs-trail, synthetic vs GPX profile).
  `RaceEstimator` is reused unchanged. The existing `/api/coach/goal-estimate` endpoints keep working on
  top of this module until the frontend has moved.
- **`services/goal_judge.py`** — prompt build, Gemini call (temperature 0, JSON schema), validator, one
  reduced-prompt retry, deterministic fallback. Telemetry `engine = gemini | gemini_retry | rules`
  through `services/observability.py` (metadata only, per `LANGFUSE_EXPORT_CONTENT=false`).
- **`goal_assessments` table** (new; `init_db()` + Alembic, per the `db-migration` skill):
  `id, user_id, plan_id NULL, race_name, race_date, distance_km, elevation_gain_m, input_hash,
  context_summary JSONB, anchors JSONB, output JSONB, engine, confidence, lang, trigger
  ('pre_plan'|'manual'|'weekly'), plan_week NULL, actual_finish_sec NULL, created_at`.
  Replaces `plans.prediction` (column kept, no longer written).

### Removed

- `race_history.scenarios()`, `store_plan_scenario()`, `_store_plan_scenario()` and the `scenarios` key
  in `GET /api/race-history`.
- The scenario branch of `RaceHistoryPlanInfo.tsx`. Its "Link a past race result" prompt becomes a
  low-confidence hint inside the goal panel; the component is deleted if nothing else remains.

### Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/goal/assess` | Pre-plan assessment. Body: race name/distance/gain/date, `exclusions`, optional manual reference result, `lang`. Works signed out with manual inputs only. |
| GET | `/api/plans/{id}/goal` | Latest assessment for a plan (+ pill status). |
| POST | `/api/plans/{id}/goal/reassess` | Manual (rate-limited) or weekly trigger. Returns stored row if `input_hash` unchanged. |
| POST | `/api/plans/{id}/goal/apply` | Set `plans.target_time_hours` to a chosen goal after athlete confirmation. |

Mirrored under `/api/coaching/athletes/{athlete_id}/…` with the existing coach-access checks.

## Gemini call

### Input (JSON)

- `race`: name, date, distance, gain, terrain tags, key climbs, climate, cutoff, profile source
  (gpx/synthetic), field curve (winner, p5–p90 per curated year).
- `athlete`: age, sex, HR zones, VO2max, UTMB index, weekly km + vert (8-week trend), HRV / load ratio
  when a watch is connected.
- `history`: included results newest first, max 15 (date, race, distance, gain, time, rank/percentile, DNF).
- `block` (plan only): weeks done / total, completion %, volume and vert vs plan, quality grade, RPE trend,
  coach notes.
- `anchors`: as produced by `goal_anchors`.
- `current_target_mins` when a plan exists.

### Instructions

Reason as Coach Uphill. Weigh the given anchors; do not invent new arithmetic. Recent, similar trail
results outweigh old road PRs; block execution moves the goal less than race evidence. A = great day,
B = realistic, C = safe. Every reasoning bullet cites a specific input. Write reasoning in `lang`
(Vietnamese copy follows the `uphill-ai-vietnamese-copy` skill).

### Output schema

```json
{
  "goals": {"a": 452, "b": 470, "c": 505},
  "confidence": "high | medium | low",
  "reasoning": ["3–5 bullets"],
  "anchors_weighted": [{"id": "phys_r12", "weight": 0.5}],
  "missing": ["watch", "recent_trail_result"]
}
```

### Validator

1. `a < b < c`; `c / a ≤ 1.35` when confidence is low, `≤ 1.20` otherwise.
2. `a ≥ 0.97 ×` fastest curated winner time for the race; `c ≤` cutoff when known.
3. `b` within the anchors' span widened 15% each side; with no anchors, `b` within the field's p10–p95.
   With neither anchors nor a field curve: only rules 1–2 and 4 apply, confidence forced to `low`.
4. 3–5 reasoning bullets; enum values valid; `anchors_weighted` ids exist.

### Fallback chain

1. Gemini, full context.
2. One retry: history capped at 5, climate/reviews dropped, validator error appended.
3. Deterministic: median of anchors × 0.95 / 1.00 / 1.08 (current `AMBITIOUS_FACTOR`/`SAFE_FACTOR`),
   labelled "Calculated estimate", no LLM reasoning. Also used when `GOAL_LLM_ENABLED=false`, no Gemini
   key is available, or quota is exhausted.

### Consistency

Temperature 0, fixed schema, and `input_hash` over the canonicalised context + anchors: an unchanged
input returns the stored row without a new call.

## UI

### Goal Determiner modal

Signed in:
1. Target race (existing `RaceNameField`) + race date.
2. **What we used** — checklist from the gathered context (e.g. `VMM 70K 2025 · 8:02`, `UTMB index 512`,
   `Watch: 42 km/wk, 1,650 m vert/wk`, `VO2max 54`), each toggleable; "+ Add a result that isn't linked"
   reveals today's reference inputs.
3. Result — A/B/C tiles (B preselected, A or C selectable), confidence label, reasoning bullets,
   missing-data hints, the existing field curve with all three goals marked.
4. **Use as target** — fills Time Target as today.

Signed out / pre-signup onboarding: step 2 is today's manual inputs; the result section is identical.

### Plan header Goal pill

Placed after `Coach notes (n)`, same pill style. Status from the latest assessment's B vs Time Target:

| Status | Rule | Dot |
|---|---|---|
| On track | \|B − target\| ≤ 3% | green |
| Ahead — consider X | B faster by > 3% | blue |
| Behind — consider X | B slower by > 3% | amber |
| Not assessed | no assessment for this plan | grey |

The panel (coach-notes panel style) shows A/B/C tiles with the one matching Time Target outlined,
reasoning, confidence, "Assessed <date> · after week N", **Re-assess with my training** (disabled with
"Already up to date" when `input_hash` is unchanged), and on Ahead/Behind **Update target to X** behind a
confirmation.

### Weekly re-assess

When the plan's week has ended (its last day has passed) and no `weekly` assessment exists for that week,
the next `GET /api/plans/{id}/goal` schedules a background re-assess and returns the previous row. No cron.
Failures are logged; the pill keeps the previous assessment.

## Error handling

- No KB match for the race: distance/gain only, no field curve (validator rule 3 degrades as above).
- Context source failure: skipped, listed in `missing`, never fails the request.
- Weekly re-assess failure never blocks the plan page.
- Manual re-assess: 3/day per user; hash hits don't count.

## Testing

- Unit: `goal_anchors` (port `test_race_estimator.py` + goal-estimate tests; per-result anchors;
  field prior), `goal_judge` validator (each rule), retry and fallback with mocked Gemini, `goal_context`
  exclusions and failing sources.
- API: the four endpoints + coach mirror, auth and plan ownership, rate limit, hash short-circuit.
- Frontend: vitest for pill status mapping; screenshot evidence (en + vi) of the modal and the pill panel
  per `ui-screenshot-evidence`.

## Evaluation gate

`scripts/golden_eval.py capture|compare --service goal`:
- Cohort: athletes with ≥ 2 trail finishes in `race_results`.
- For each, hold out the latest finish; build context from data dated **before** it (watch and block data
  excluded — not available historically).
- Run old engine and new path. Metrics: A–C hit rate, median |B − actual| %, both split by confidence.
- Ship when the new path is ≥ the old engine on both metrics.

After launch: fill `goal_assessments.actual_finish_sec` when an imported result matches the assessed race
and date; Metabase panel for live hit rate and error by confidence.

## Rollout

1. Backend behind `GOAL_LLM_ENABLED` (off → deterministic engine, same UI and API).
2. Staging: run the backtest against staging data; review Langfuse traces (metadata only).
3. Prod: enable after the gate passes.

## Resolved during implementation

- Changing `target_time_hours` does **not** recalculate existing workouts; it is read when a block or
  week is generated (race pace, next block, week rebuild). The "Update target" confirmation says so.
- Field-position prior: weekly km ≥70 → p40, ≥50 → p55, ≥30 → p70, else p85; any ultra finish −10
  (`goal_anchors._VOLUME_PERCENTILE`). An explicit flat pace (signed-out input) is always an anchor.
- Each result also yields a `field_rank` anchor from its own UTMB rank/total mapped onto the target curve.
- Orchestration and persistence live in `services/goal_service.py`; the old `/api/coach/goal-estimate`
  endpoints and `_goal_estimate_core` are left in place (unused by the new UI) rather than moved.
- `goal_judge.PROMPT_VERSION` is part of `input_hash`, so a prompt change is never answered from an
  older stored row.
- Weekly re-assess dedupe: an in-process in-flight set plus a partial unique index
  `uq_goal_assessments_weekly (plan_id, plan_week) WHERE trigger = 'weekly'`.
- `POST /api/goal/assess` is unauthenticated, so signed-out estimates are rules-tier only (never Gemini).
  Signed-in users get `LLM_DAILY_LIMIT` (20) non-weekly assessments per day on Gemini; past that the rules
  tier answers. Changing exclusions or the reference defeats hash reuse, so the budget is what bounds cost.
  `lang` is normalised to en/vi.
- New plans are assessed in a background thread at creation (`GOAL_ASSESS_ON_PLAN_CREATE`, off in tests).
- The race-history panel's scenario cards (same inconsistent number, plus road PR scenarios) were
  removed along with `race_history.scenarios()`.
- Backtest: `scripts/goal_backtest.py`, reachable as `golden_eval.py compare --service goal`; the target's
  field curve excludes the held-out year (`resolve_course(before_year=...)`).

## Out of scope

- Changing how the Scheduler consumes Time Target.
- Per-segment pacing (Pace Strategy unchanged).
- Year-variable routes (tracked separately).
- Dropping the `plans.prediction` column.
