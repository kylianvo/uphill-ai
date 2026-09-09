# Plan-generation prompt audit — September 2026

**Scope:** the four prompt surfaces that produce and adapt training plans.
**Trigger:** a production complaint from a beginner athlete (`hoangmaipham2005@gmail.com`) whose week 2 came back *shorter* than week 1 after she reported very light effort and asked to run longer.

**Headline:** the prompts are strong on doctrine and weak on enforcement. Averaged across 20 aspects, **doctrine scores 6.9/10 and engineering scores 5.2/10**. The reported failure is not caused by bad coaching knowledge — it is caused by three code defects and one prompt regression that no amount of prompt wording would fix.

---

## 1. What actually happened to this athlete

Six defects compound. Five are confirmed by reading code; one needs a database check that is still outstanding (see §6).

### D1 — Adapt-week anchors on *completed* volume, so being busy shrinks your next week
`main.py:2490` builds the progression reference:

```python
prior_ref_km = (
    actual_km if (prev_wos and actual_km > 0)
    else (planned_km if ...)
)
```

`actual_km` sums only workouts where `is_completed == 1` (or synced wearable activities). She adapted week 2 **because she was busy** — the exact situation where week 1 is under-completed. The bounds are then derived from that shrunken number:

```python
target_floor_km = prior_ref_km * 1.02   # "very light" branch
target_ceil_km  = prior_ref_km * 1.08
```

A 40 % under-completed week 1 produces a week 2 that is ~40 % smaller — **while telling the model this is a 2–8 % increase**. The system is confidently progressing off a false baseline.

> **This is the single defect most likely to explain her complaint.** It is also the one still pending verification: if her week-1 workouts *were* all marked complete, this is not the cause and the ranking below changes. See §6.

### D2 — Her free-text request loses to a numeric ceiling
Her input reaches the prompt as prose:

```
Athlete notes: "..."
Feeling Very Light: ... IMPORTANT: Increase training stimulus by adding 5-10% weekly volume...
```

…and then, further down, as a hard number:

```
Remaining N Sessions Target: MUST total between X km and Y km.
DO NOT exceed Y km across the remaining sessions.
```

There is **no precedence rule** telling the model which wins. `MUST` and `DO NOT exceed` are the strongest tokens in the section, so the ceiling wins and her stated wish is decoration. A model asked to both "increase stimulus" and "not exceed 11.4 km" will satisfy the number.

### D3 — Volume is bounded in kilometres for an athlete whose plan is governed by time
`post_process_workouts` discards whatever distance the model produced and recomputes it:

```python
wo["target_pace"], wo["distance_km"] = pace_and_distance_for_zone(zone, dur, est_zones)
# distance_km = duration_minutes / zone_pace_mid
```

So `distance` is a *pure function of duration and her pace zone*. A km bound is therefore a disguised **minutes** bound, converted at a pace she cannot run. For a walk-run beginner this is doubly wrong: her real moving pace is perhaps 9–10 min/km, but the conversion uses her configured Zone 2.

### D4 — She has the wrong pace zones entirely
The slow beginner default exists, but only in the onboarding handler (`main.py:801`):

```python
if request.goal_type == "start_running":
    zone2_min = ... or "8:30"
    zone2_max = ... or "7:30"
```

Her card shows **6:30 – 5:45 /km** — the generic default. Every derived number inherits the error:

| Quantity | Shown | With correct beginner zones | Plausible reality |
|---|---|---|---|
| 23 min session | ~3.7 km | ~2.9 km | ~2.4 km |
| Pace target | 6:30–5:45 /km | 8:30–7:30 /km | ~9–10 min/km |

The maths checks out exactly: zone-2 mid of 6:30–5:45 is ≈ 6:07/km; 23 ÷ 6.07 = **3.79 km**, matching the "~3.7km" on her card. She is being shown a distance she did not run at a pace she cannot hold.

### D5 — The red "Zone 4–5" badge is a title-string collision
`useWorkoutTypes.ts:76` resolves a workout's identity by **scanning the title first**:

```ts
const titleMatch = dbTypes.find(
  (t) => t.type_key.length > 5 && titleLower.includes(t.type_key.replace(/_/g, " "))
);
```

Her session is titled *"Aerobic Base: Progressive Walk-Jog **Intervals**"*. The substring `interval` matches the `interval` type, which carries `zone: "hard"` (rendered **"Zone 4–5"**) and `color: "#ef4444"` (**red**). The workout's own `type: "Easy"` field is never consulted. Any easy session with "interval" in its title is mislabelled as maximal-intensity work — the most dangerous possible mislabel for a beginner.

### D6 — The prompt contains a duplicated, half-truncated schema block *(new finding)*
`plan_generator.py:1131–1156` emits three schema fields **twice**:

- `interval_reps` / `interval_rep_value` / `interval_rep_unit` — twice
- `elevation_gain_m` / `grade_percent` — twice
- `description` — **once truncated mid-sentence**, then once in full

The first `description` entry simply stops at `…NEVER wrap them in a label like 'Main Circuit: ...'. ` and the duplicate block begins. Introduced in `cc8f4d9` ("integrate unified 5-feeling RPE scale … Muscular Endurance framework"), verified present inside `_ai_prompt` alone (not the old NotebookLM block) and shipped to production. ~1,900 wasted characters and a dangling instruction in the most load-bearing part of the prompt.

---

## 2. Scored aspect matrix

**Doctrine** — is the *Training for the Uphill Athlete* principle encoded correctly?
**Engineering** — is it unambiguous, non-contradictory, and actually enforceable?

`—` means the axis does not apply. A **0 means the prompt never mentions it**, which is itself the finding.

| # | Aspect | Doctrine | Engineering | Note |
|---|---|:---:|:---:|---|
| 1 | Output contract / JSON schema | — | **4** | D6: duplicated block, one copy truncated mid-instruction |
| 2 | Periodization phases | 8 | **5** | Peak/Taper/Race Week still instructed for goals that have no race |
| 3 | Volume progression cap | 9 | **3** | Stated in 3 places with 3 different numbers, no precedence |
| 4 | 80/20 polarization | 9 | 6 | Vacuous for walk-run (already 100 % Z1–2); the "≤15–20 % hard" clause *invites* intensity |
| 5 | Long-run cap & weekday durations | 8 | 7 | "Weekday runs 45–75 min" is actively wrong for 20-min beginners |
| 6 | Muscular Endurance directives | **9** | 6 | Best doctrine in the prompt; ~1,400 chars fire unconditionally at beginners |
| 7 | Deload / 3:1 cycles | 8 | 5 | Never reconciled with the adapt-week bounds that can contradict it |
| 8 | ADS rule | 8 | 6 | Well-derived from AeT/AnT spread; no beginner interaction |
| 9 | Equipment / terrain constraints | 7 | **8** | Has a *code* backstop (`hill_sprint_eligible`) — the right pattern |
| 10 | Scheduling / preferred days | — | 7 | Clear, honoured, with a post-process filter |
| 11 | Feedback / RPE loop | 7 | **3** | D2: 5-tier prose table loses to the numeric ceiling below it |
| 12 | Adapt-week volume bounds | **4** | **2** | D1+D3: wrong anchor, wrong unit, contradicts #11 |
| 13 | **Beginner / walk-run handling** | **1** | **0** | §3 — three sentences, no schema, no type, no progression model |
| 14 | Interval structure & rendering | 6 | 3 | D5 + structured fields gated on `type == "Interval"` |
| 15 | Treadmill realism | **9** | **9** | Deterministic, code-derived, never trusts the model — **the model to copy** |
| 16 | Elevation & grade | 8 | 8 | Also code-resolved |
| 17 | Fueling | 8 | 7 | Quantitative and tiered by duration |
| 18 | Localization (vi) | — | 8 | Specific, with named anti-patterns |
| 19 | KB grounding (Qdrant) | **3** | 6 | Retrieval works; **0 of 29 rows** mention beginners (§4) |
| 20 | Single-workout co-create prompt | 6 | 5 | No Process/Overall/Reason/Benefit/Warning contract → coach-added workouts render differently |
| | **Average** | **6.9** | **5.2** | |

**Read of the matrix:** the two aspects scoring 8–9 on *both* axes (#15 treadmill, #16 elevation) are the two that are resolved **in code and never trusted to the model**. Every aspect scoring ≤4 on engineering is one where the prompt states a rule in prose and hopes. That is the pattern to generalise from.

---

## 3. Beginner handling: the 1/0

`goal_type == "start_running"` receives exactly this:

```
Goal: Start Running / Learn to run. Build a safe, injury-free aerobic base
starting with walk-to-run progressions. Do NOT assign high-intensity threshold
or anaerobic intervals. Volume must start low and increase very slowly.
```

Three sentences. They then compete with roughly **6,000 characters** of rules written for a mountain ultrarunner: ME circuit design, the 48-hour ME buffer, Peak-phase back-to-back vert weekends, eccentric quad conditioning, weighted-pack step-ups, Summit Water Dump, race-day carb loading at 8–10 g/kg. Nothing switches any of it off.

The word **"walk"** appears in the entire generation prompt exactly once — in the sentence above.

Consequences, all visible in her plan:

- **No walk-run schema.** The `type` enum has no walk-run value, so the model picks `Easy` (and titles it "Intervals" → D5).
- **`resolve_interval_summary` discards the structure.** It returns `(None, None, None)` unless `type == "Interval"`, so a walk-run session's rep structure can *never* reach the structured fields — which is why "5 × 2 min jog / 1 min walk" survives only as free text and cannot render as a collapsed chip.
- **`current_weekly_km` defaults to 30.0** — a marathoner's base, applied to someone who cannot yet run 3 minutes.
- **The rule-based fallback has no beginner path at all.** If both Gemini attempts fail, she gets a generic phase-based plan with no walk-run concept.

---

## 4. The knowledge base has no beginner content

All **29** rows in `kb_seed/scheduler.json` are advanced-athlete doctrine:

> ME vs conventional strength · Gym-Based ME Design · Progressive 14-Week Gym ME Protocol · Transition/Base/Build/Peak periods · AeT vs AnT · ADS · Carbohydrate & Fluid Intake · Tapering · Hill Sprints & Gradient Matching · Treadmill Substitutions · Double Sessions · Overtraining · Race-Day Pacing · Course-Specific Preparation …

Zero rows on beginners, walk-run, couch-to-5k, or first-time-runner injury risk. So the Qdrant retrieval that is supposed to *ground* her plan actively injects **gym ME protocols and 14-week progressions** on top of an already mis-targeted prompt. Grounding is making it worse, not better.

---

## 5. Overlooked entirely

Ranked by how much each would have changed her outcome.

| | Missing | Why it matters here |
|---|---|---|
| 1 | **Walk-run as a first-class workout type** | No schema, no enum value, no rendering path (D5) |
| 2 | **A beginner progression metric** | Nothing tracks "longest unbroken jog"; progression has no knob except km |
| 3 | **Precedence between athlete request and numeric bounds** | D2 — her explicit ask silently lost |
| 4 | **Time-governed plans** | Everything is km, derived from a pace she cannot run (D3) |
| 5 | **Session-duration floor** | Nothing prevents a 20-minute "long run" |
| 6 | **Adherence/consistency as an objective** | Beginners need streaks; the prompt only optimises load |
| 7 | **The talk test** | AeT/AnT are meaningless to someone with no pace sense |
| 8 | **Beginner-specific injury gating** | Bone stress / too-much-too-soon is the #1 new-runner risk; unmentioned |
| 9 | **Cadence and form cues** | Absent from every prompt |
| 10 | **Detraining / missed-week handling** | Only ME has a missed-session rule |
| 11 | **Expectation setting** | Nothing tells her what improvement should look like week to week |
| 12 | **Cap on week-over-week session *count*** | Only volume is capped; going 3 → 5 days is unconstrained |

---

## 6. Outstanding verification

**D1 is ranked first but is not yet confirmed.** It depends on whether her week-1 workouts were marked complete. The queries below are read-only and scoped to her account. If they show week 1 fully completed, D1 is *not* the cause and D2/D3 move to the top.

```sql
-- 1. profile: confirms D4 (expect 6:30 / 5:45 rather than 8:30 / 7:30)
SELECT id, age, current_weekly_km, zone2_pace_min, zone2_pace_max, aet_hr, ant_hr
FROM users WHERE email = 'hoangmaipham2005@gmail.com';

-- 2. plan shape
SELECT id, goal_type, total_weeks, start_date, days_per_week, preferred_run_days
FROM plans WHERE user_id = <id>;

-- 3. THE DECIDING QUERY for D1 — completion flags drive prior_ref_km
SELECT week_number, day_of_week, type, title,
       duration_minutes, distance_km, target_zone, is_completed
FROM workouts WHERE plan_id = <plan_id> AND week_number IN (1,2)
ORDER BY week_number, id;
```

The audit was written without these because every other finding is established from source. This section is the one claim still carrying a caveat.

---

## 7. Recommendations

**Fix in code, not in the prompt** — the three that no wording can reach:

1. **D4 — move the beginner pace default out of the onboarding handler** so any path that creates a `start_running` plan gets slow zones. Then backfill her row.
2. **D5 — consult `type` before scanning the title** in `resolveWorkoutInfo`, or drop the title scan for workouts whose `type` is already unambiguous.
3. **D1/D3 — anchor adapt-week on *planned* volume, in minutes**, and treat under-completion as a separate signal rather than a smaller baseline.

**Fix in the prompt:**

4. **D6 — delete the duplicated schema block.** Mechanical, zero risk, ~1,900 characters recovered.
5. **D2 — add an explicit precedence line**: an athlete's stated request plus a very-light RPE raises the ceiling rather than losing to it.
6. **Build the separate beginner prompt builder** (agreed design): share the output contract and schema, replace the ME/periodization/race-fueling rules block wholesale for `start_running` / `return` / `recovery`. Hardcode walk-run doctrine in the builder rather than retrieving it — §4 shows retrieval would have to compete with 29 advanced rows for the same top-k slots, and a retrieval miss on "when do I stop walking" fails silently.
7. **Headline metric: longest unbroken jog.** Store it as `max_continuous_jog_min` on the profile, fed by an explicit adapt-week question rather than parsed out of the model's own prose. This is a schema change and needs both `db.py:init_db()` and an Alembic migration per the `db-migration` skill.

**Generalise the pattern that already works:** aspects #15 and #16 score 8–9 on both axes because they are computed in code and the model's numbers are discarded. Walk-run structure belongs in that category — deterministic, derived from the athlete's own stated ability, never the model's guess.
