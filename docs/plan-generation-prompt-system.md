# Plan Generation Prompt System

How Coach Uphill turns an athlete's profile and a race goal into a structured, week-by-week
training plan — and how it adapts that plan as the athlete trains.

**Diagrams** (interactive HTML, open in a browser):
- [`diagrams/prompt-assembly-pipeline.html`](diagrams/prompt-assembly-pipeline.html) — the shared tier-aware prompt pipeline
- [`diagrams/flow-new-plan.html`](diagrams/flow-new-plan.html) — generating a new plan
- [`diagrams/flow-adapt-week.html`](diagrams/flow-adapt-week.html) — adapting one week in place
- [`diagrams/flow-next-block.html`](diagrams/flow-next-block.html) — generating the next 2-week block

---

## Context and goals

Three separate user actions all end up producing the same thing — a batch of `workouts` rows —
by calling the same core function, `PlanGenerator.generate_plan_workouts()`
([plan_generator.py](../backend/services/plan_generator.py)):

| Action | Entry point | What it regenerates |
|---|---|---|
| Start a new plan | `POST /api/auth/onboarding` or `POST /api/coach/generate-plan` | Block 1 (weeks 1–2) |
| Adapt a week in progress | `POST /api/coach/adapt-week` | One specific week |
| Generate the next block | `POST /api/coach/generate-next-block` | The next 2-week block |

Until September 2026, that shared function assembled **one prompt**, written for a mountain
ultrarunner, and served it to every athlete regardless of experience. A beginner on a
walk-to-run plan was told to respect the 48-hour Muscular Endurance buffer before her weekend
long run; a novice runner's rules withheld all quality work even though nothing in the training
philosophy says novices can't do a tempo run. A production incident — a beginner's week 2 came
back *shorter* than week 1 despite her reporting very light effort and asking to run longer —
traced back to six defects in that single-prompt design (see
[`prompt-audit-2026-09.md`](prompt-audit-2026-09.md) for the full audit).

The fix wasn't a patch to that one prompt. It was making **athlete tier a first-class dimension**
the prompt is assembled *from*, so the next athlete served the wrong rules — the sub-elite
reading a recreational runner's caps — never happens either.

## High-level design

### The tier model

Five tiers — `beginner`, `novice`, `recreational`, `sub_elite`, `elite` — each carry a
`TierProfile` ([athlete_tier.py](../backend/services/athlete_tier.py)) with the numbers that
actually vary by training level: weekly progression cap, weekday session band, long-run share,
Zone 2 pace defaults, and whether intensity, Muscular Endurance blocks, and walk-run structure
apply at all.

**Tier is derived, not asked.** `resolve_tier()` picks from signals ordered by how much each can
be trusted:

1. An **explicit override** on the plan (`plans.athlete_tier`) always wins.
2. A `start_running` goal is beginner regardless of any stale volume number — `current_weekly_km`
   defaults to 30.0 on a profile that's never been filled in, which would otherwise read as
   recreational.
3. Someone who can't jog 10 minutes unbroken (`max_continuous_jog_min`) is a beginner whatever
   else their profile claims.
4. Weekly volume selects a band (0–15 / 15–40 / 40–80 / 80–160 / 160+ km/week — KB-grounded,
   not guessed).
5. A proven long run can **promote**, never demote (8 km/week but a completed 30K → novice, not
   beginner).
6. A measured **AeT/AnT threshold spread** can **demote**, never promote — weekly volume is
   self-reported and often aspirational, while the spread is measured. 90 km/week with a 35%
   spread is an aerobic deficiency, not a sub-elite engine. Demotion stops at `recreational`;
   the athlete demonstrably runs the volume, they're just not competitive.

Unknown volume falls back to `recreational`, not `beginner` — defaulting everyone to the easiest
tier would hand a walk-run plan to a trained runner who simply hasn't filled in their profile.

### Prompt assembly: rules *and* schema are both tier-conditional

See [`diagrams/prompt-assembly-pipeline.html`](diagrams/prompt-assembly-pipeline.html).

Fixing only the **rules block** ([plan_rules.py](../backend/services/plan_rules.py)) was the
first pass, and it wasn't enough on its own — the JSON **schema** section of the prompt is
generic template text that used to fire unconditionally too. A beginner's assembled prompt
stated *"NO Muscular Endurance sessions of any kind"* a few hundred characters after the schema
handed the model the Summit Water Dump protocol and 8–10 g/kg race-day carb loading, because the
schema examples weren't gated the same way the rules were. A prompt that contradicts itself is
worse than one that's uniformly wrong — the model resolves the conflict however it likes,
differently each run.

Both are gated on the same `TierProfile` now:

- `build_rules_block()` returns walk-run rules for `beginner`, or the performance rules with
  Muscular Endurance / intensity / fueling tiers interpolated from the profile for every other
  tier.
- The schema's ME circuit format, per-duration fueling tiers, and the steep hill-sprint incline
  exception are each wrapped in `if tier_profile.allows_me_blocks` / `allows_intensity` checks
  before they're written into the prompt at all.

A beginner's assembled prompt is measurably shorter than a recreational runner's — every
dropped character was apparatus that contradicted the rules sitting next to it.

### Grounding: the knowledge base has to cover the whole tier range

`kb_chunks` (the `scheduler` domain, retrieved via Qdrant — [kb_retrieval.py](../backend/services/kb_retrieval.py))
grounds the prompt in *Training for the Uphill Athlete* doctrine. Before September 2026 all 29
rows were pitched at one audience — a trained mountain athlete — so retrieval for a beginner's
plan surfaced gym Muscular Endurance protocols and 14-week progressions: grounding was making
the plan *worse*, not better.

The KB now carries 40 principles, including walk-to-run progression, connective-tissue
adaptation timelines, and effort regulation without pace data at the beginner end; and
double-threshold day spacing, the Zone 4 weekly cap, and readiness/overreaching markers at the
sub-elite/elite end. **Beginner rules-block content is deliberately hardcoded, not
retrieved** — retrieval is top-k over one collection, and a beginner query competing with 29+
advanced rows for the same slots risks a retrieval miss on exactly the doctrine that matters
most, which fails silently and reads as a plausible plan.

### The fallback chain

Identical across all three flows, because it lives inside the shared function, not in any one
flow's endpoint code:

```
Gemini (grounded) → Gemini retry (reduced prompt, no KB context, shorter output) → rule-based schedule
```

The reduced retry exists to recover the single most common failure — a truncated or
unparseable response — without a second AI vendor. It drops the KB grounding block specifically
because that's the easiest thing to cut to shorten the prompt.

**The rule-based fallback is not tier-aware.** It's a deterministic, phase-based schedule
(`Base → Build → Peak → Taper → Race Week → Recovery`) that respects the requested week/block
*scoping* — `target_week` or `block_number` — but has no walk-run concept, no ME gating, nothing
from `TierProfile` at all. It's also the schedule a beginner is statistically most likely to
land on if Gemini fails twice, which is why the retry tier exists: to make that fallback rare,
not to make it safe.

### `post_process_workouts()`: never trust the model's own numbers

Regardless of which tier of the fallback chain produced the workout list, the same
post-processing step recomputes `distance_km` from `duration_minutes` and the athlete's
**resolved** pace zone (never the model's own guess), derives `treadmill_incline`/`speed`
deterministically from that same resolved pace and grade, and clamps `week_number` to the
requested scope. This is the same pattern the tier fix generalizes: anything the model might
get wrong in a way that silently mismatches the athlete's real numbers is computed in code
instead, using `resolve_pace_zones()` — a measured threshold pace wins, then the athlete's
stored Zone 2 bounds, then the tier default. Before this consolidation, the generator called a
lower-level pace function directly and silently dropped a measured threshold pace even when one
was on file, so the *app* showed one set of zones while the *plan* was built on another.

## The three flows

### 1. New plan generation

See [`diagrams/flow-new-plan.html`](diagrams/flow-new-plan.html).

`POST /api/auth/onboarding` (or `/api/coach/generate-plan` for an additional plan) saves the
profile, creates the `plans` row, and returns a `job_id` immediately — generation happens in a
background `asyncio` task, polled via `GET /api/coach/plan-status/:job_id`. The background task
calls `generate_plan_workouts(block_number=1, weeks_per_block=2)`: only the first block
generates up front, so `goal_type=start_running` alone is enough to resolve the beginner tier
before a single workout exists.

### 2. Adapt week

See [`diagrams/flow-adapt-week.html`](diagrams/flow-adapt-week.html).

`POST /api/coach/adapt-week` is where the original production defect lived, and where three of
the six audit findings were fixed:

- **The anchor is planned volume, in minutes** — not completed volume, and not kilometers. The
  old code anchored on *completed* volume, so adapting a week *because you were busy* — the most
  common reason to adapt — shrank the next week while telling the model it was a 2–8% increase.
  Kilometers were also a disguised minutes bound, since distance is recomputed from duration
  downstream.
- **Adherence is a signal, not a punishment.** Below 80% completion, the target week *holds*
  near the prior plan (0.95–1.02×) instead of progressing off an incomplete week or shrinking as
  a penalty — and the model is told explicitly to frame a held week as a repeat, not a setback.
- **Explicit precedence.** The prompt used to state a 5-tier RPE table as prose *above* a
  `MUST … DO NOT exceed` numeric ceiling with nothing saying which wins — the number always won,
  so an athlete reporting very light effort while asking for more work got less. The bounds are
  now stated as a safety cap, not a target: light effort plus a request for more places the week
  at the top of the band.

`target_week` scopes the regeneration to exactly one week; `save_workouts(preserve_completed=True)`
keeps any session in that week already marked complete or matched to a synced activity, rather
than overwriting it.

### 3. Generate next block

See [`diagrams/flow-next-block.html`](diagrams/flow-next-block.html).

`POST /api/coach/generate-next-block` gates on the previous block being at least 70% complete by
training hours (`get_block_completion()`), with `override_gate=true` as an explicit athlete
confirmation to bypass it — never a silent default. Coach evaluation and athlete feedback from
prior blocks are folded into the prompt as free text, newest block first, since that's the
context most likely to survive if it's ever truncated. Otherwise this flow is a thin wrapper:
`block_number`/`weeks_per_block` scope the request the same way `target_week` does for
adapt-week, and it shares the identical tier resolution, prompt assembly, and fallback chain.

## Key decisions and trade-offs

- **Tier is a dimension, not a beginner exception.** A `start_running`-only special case would
  have relocated the original bug rather than fixed it — the next athlete served the wrong
  rules would have been the sub-elite reading a recreational runner's progression cap.
- **Weekly progression is uniform across tiers (7–10%); the annual rate is what differentiates
  them** (25%/year for a beginner, down to 10%/year once trained). An earlier draft of the tier
  table guessed elites progress more slowly week-to-week — the doctrine says otherwise, and the
  KB sweep caught it.
- **The AeT/AnT gap only demotes.** Promoting on a narrow gap would let a detrained former
  athlete's old threshold numbers claim a tier their current training doesn't support.
- **Beginner doctrine is hardcoded, advanced doctrine is retrieved.** The walk-run rules, the
  connective-tissue rationale, and the injury guardrails are stable and small enough to state
  directly; retrieval is reserved for the parts of the doctrine large enough that hardcoding all
  of it in the prompt would be impractical.
- **One resolver for pace zones, one resolver for tier — never duplicated per call site.** Both
  bugs this system replaced were the same shape: a value computed correctly in one place and
  incorrectly (or via a stale hardcoded default) in another, so the athlete saw one thing and the
  plan used another.

## Data flow and integration points

**Reads**, per generation:

- `users` — age, gender, height/weight, current_weekly_km, max_hr/resting_hr/aet_hr/ant_hr,
  zone2_pace_min/max, threshold_pace, pace_zone_model, goal_type, injury_history,
  max_continuous_jog_min
- `plans` — race details, goal_type, athlete_tier (override), preferred/double-session days,
  training_environment, athlete_notes
- `workouts` — prior weeks' planned vs. actual volume, completion state, missed-ME detection
  (adapt-week and next-block only)
- `kb_chunks` via Qdrant — top-6 scheduler-domain principle chunks, embedded with
  `gemini-embedding-2`

**Writes**: `workouts` rows via `save_workouts()`, either replacing a week/block wholesale or
preserving already-completed sessions (adapt-week).

**External call**: Gemini 2.5 Flash, via `google-genai`, with `thinking_config` set from
`settings.GEMINI_THINKING_LEVEL`.

## Related documents

- [`prompt-audit-2026-09.md`](prompt-audit-2026-09.md) — the original scored audit, the six
  defects, and the KB grounding gap that motivated this system
- [`services/athlete_tier.py`](../backend/services/athlete_tier.py) — tier derivation and profiles
- [`services/plan_rules.py`](../backend/services/plan_rules.py) — the tier-conditional rules text
- [`services/plan_generator.py`](../backend/services/plan_generator.py) — prompt assembly, the
  fallback chain, and `post_process_workouts()`
- [`kb_seed/scheduler.json`](../backend/kb_seed/scheduler.json) — the 40 committed KB principles
- [`scripts/distill_principles.py`](../backend/scripts/distill_principles.py) — how new KB
  principles are swept and reviewed before landing in the seed file
