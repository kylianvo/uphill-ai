# Scheduler reliability grounded in Training for the Uphill Athlete

Date: 2026-10-03 (Australia/Sydney)
Status: Proposed design for owner review; no implementation authorized by this document.

## Intent and scope

Improve the existing scheduler for recreational and sub-elite urban Vietnamese
runners while preserving the principles of Training for the Uphill Athlete.
The owner approved a backend-first scope: diagnose sequential weekly-volume
loss, make workout accounting and instructions consistent, improve quality
checks, and validate through synthetic evaluation and staging. Flat weekday
outdoor training, optional incline treadmills and weekend mountains are central
constraints. A new terrain-availability UI is outside this change.

Success is a feasible, internally consistent training prescription grounded in
verified coaching rules, not merely a distance sum that passes a fixture.
Production remains on HOLD. The existing staging override experiment does not
establish how ordinary completed-week progression behaves.

## Evidence and source hierarchy

The repository's scheduler seed is a distillation, not the full book. Its chapter
labels and numbered references are not sufficient proof of every claim. Do not
state that the entire book was independently verified in this work.

Use the book where a verifiable passage is available. Record edition and page
only after inspection. Author-published excerpts can establish the principles
they actually cover. Official supplementary workouts are labeled supplements,
not silently represented as exact book prescriptions. App choices and numeric
release gates must be labeled engineering policy. Unresolved source conflicts
block the affected coaching-rule change; they do not block reproducing software
bugs or correcting arithmetic.

Primary sources inspected for this design:

- Scott Johnston's [published book excerpt on continuity, gradualness and
  modulation](https://www.trainingpeaks.com/blog/training-for-the-uphill-athlete-continuity-gradualness-and-modulation/).
  It supports adaptation to actual training and interruptions, individual
  progression, and recovery between loads. It does not establish a universal
  per-tier long-run percentage or automatic weekly mileage increase.
- [Official Uphill Athlete ME workout](https://www.uphillathlete.com/wp-content/uploads/2020/03/ME-Uphill-Athlete-Workout-.pdf),
  pages 1–2. It describes gradual introduction, individual progression and
  recovery, and prescribes completing an exercise's sets before moving on.
  Its later use of “circuit” is not a basis for a universal ban on straight sets.
- [Official strength-training guidance](https://uphillathlete.com/strength-training/strength-training-for-the-mountain-athlete/)
  is a supplementary reference for distinguishing general strength and specific
  training; exact protocols require verification before adoption.

Local evidence:

- `backend/kb_seed/scheduler.json`: especially chunks titled Gym-Based ME Workout
  Design; Recovery and Core Training Principles; Weekly Volume Share of Aerobic
  Base Training and Intensity Distribution; Treadmill & Gym Machine Substitutions;
  Training Volume, Terrain Specificity, and Session Structure.
- `docs/superpowers/evidence/fitness-snapshot/vietnam-urban-eval.md` and its samples.
- `docs/runbooks/2026-10-fitness-snapshot-release.md`: repeated runs and the staging
  no-COROS next-block result of 110.2 km against the unchanged 115–150 km band.

## Coaching-rule audit comes first

Create a reviewed rule-to-source register before changing coaching behavior.
Each entry records source location, population/event, prerequisites, phase,
measurement units, implementation location and disposition: supported,
engineering policy, or disputed. Audit only scheduler rules affected here.

Known conflicts and ambiguities:

1. `plan_generator.py` demands ME circuits and never straight sets; the official
   workout and the stored gym-ME chunk do not support that universal prohibition.
2. Stored intensity-distribution text inconsistently describes Zone 1/2 as below
   AeT and below AnT. Resolve threshold definitions and denominators before using
   those chunks to enforce intensity percentages. Preserve measured-source
   requirements; estimated thresholds must not become a diagnosis.
3. `plan_rules.py` says long-run share of weekly volume without units. The
   beginner rule uses time. Tier-specific 33%/30% and combined weekend 50% limits
   are existing app policy, not verified universal book rules.
4. The prompt's short-runway override can start ME immediately regardless of
   strength history. A nearby event must not manufacture the prerequisites for
   advanced work. Audit this against athlete history and the relevant source.
5. Hill sprints, sustained uphill intervals and gym ME are distinct stimuli.
   Title keywords must not force them into one treadmill prescription. Stored
   treadmill advice also requires source review before becoming app guidance.

Do not silently re-distill or import the full knowledge base. Any scoped seed
correction has a reviewed source diff; prompt, seed and fallback contradictions
must be reconciled before candidate evaluation. No broad medical claims or
unverified recovery formulas should be added to generated coaching guidance.

## Design decisions

### 1. Diagnose before changing weekly load

Reproduce the same synthetic athlete through initial and next-block generation
with completed training, unlogged training, explicitly missed training, an
illness/fatigue report and an explicit completion override. Separate calendar
coverage from completion percentage. Unknown activity is not confirmed inactivity;
confirmed missed training must not be treated as completed work.

Capture local synthetic-only inputs and outputs at the prompt, raw generation
and normalization boundaries. Explain the contribution of adaptation and
arithmetic separately. No real prompt content enters Langfuse. An override grants
access to generation; it does not assert readiness or invalidate feedback.

The weekly snapshot is a baseline input, not an unconditional quota. Normal
healthy full weeks retain existing fixture bands. Recovery, taper and verified
interruptions require separately specified scenarios with expected adaptations.
Never add mileage to rest days or raise intensity just to satisfy a test.

### 2. One prescription feeds totals and instructions

Use a small internal structured segment representation for newly generated
mixed sessions. Distinguish running, hiking, strength/ME, recovery and rest;
include duration, intensity, setting and applicable pace/incline information.
Pure circuits remain zero running distance; genuine running warm-ups/cool-downs
contribute once. Do not infer machine-readable segments by parsing prose.

Validate segments, then derive the existing workout fields and numerical
instruction text from the same resolved values. The LLM supplies coaching
rationale and exercise selection within the supported protocol; it does not
independently invent a second numerical prescription in prose. The design must
cover EN and VI, all generation paths and the rule-based fallback.

Keep public workout fields compatible. Persisting segments is not required for
the first release if existing fields and generated descriptions retain the
complete prescription. If durable segments prove necessary, bring the schema
change back for design review before implementation; do not slip in a migration.
Legacy workouts remain readable and are not retroactively reinterpreted.

Report running distance, hiking distance/time, aerobic time, strength/ME time
and ascent separately in internal accounting. Indoor ascent is an estimate from
resolved movement and grade, not measured outdoor elevation. Strength minutes
must not inflate running kilometers or mask long-run concentration.

### 3. Explicit context for validation

Quality checks consume resolved workouts plus week coverage, tier, phase and
available terrain/equipment. Do not derive these facts from workout titles.

- Arithmetic: segment durations and totals reconcile within documented rounding;
  each movement appears once; treadmill fields match numerical instructions.
- Access: weekday outdoor work is flat; incline sessions require treadmill
  access that day; mountains occur only on permitted days. Default to supported
  activity when access is unknown, not assumed equipment.
- Intensity: distinguish actual work/recovery portions; an interval session's
  single Zone 2 label must not make every minute easy. Apply verified,
  context-dependent rules from the source register.
- Progression: compare complete, comparable weeks. A partial week is explicitly
  not comparable for a full-week growth ratio; still validate its daily load and
  recovery. Do not relabel missing workouts as partial calendar coverage.
- Long-run distribution: proposed accounting uses locomotion time (running and
  hiking, including their warm-ups/cool-downs), excluding strength and passive
  rest. Report distance share separately. Approve the applicable numerical
  policy in the source register before using it as a new hard gate.
- Disclosure: internal snapshot/tier/scoring implementation wording stays out of
  athlete-facing text, while useful explanations of recent training remain.

Inconsistent output must be identified before storage. Arithmetic repairs may
recompute derived fields; they must not silently rewrite the physiological
stimulus. Use a bounded existing retry/fallback path for invalid prescriptions,
with explicit metadata. A fallback must pass the same structural/access checks;
otherwise surface generation failure. Do not add an unbounded repair loop.

### 4. Focused module boundaries

- `services/plan_generator.py`: generation integration and existing fallback.
- A focused workout-prescription helper: segment validation, accounting and
  numerical instruction assembly; extract only the code this change requires.
- `services/plan_rules.py` and `services/athlete_tier.py`: sourced coaching rules
  and clearly identified app policy.
- `services/plan_checks.py`: independent checks with explicit context.
- `main.py` next-block core: preserve completion/readiness distinctions and pass
  context; avoid an unrelated router refactor.
- `scripts/golden_eval.py`: deterministic evaluation dates, contextual checks,
  comparable baselines and individual failure reporting.
- Existing scheduler fixtures plus focused synthetic sequential scenarios.

## Validation and release gates

First pin regressions with deterministic unit tests. Test pure circuits, mixed
ME, hiking, treadmill grade, rounding, unavailable equipment, contradictory
numeric instructions, malformed segment output, legacy workouts and fallback.
Test completed, unlogged and missed weeks separately, including partial starts,
recovery and taper. All data is invented.

Freeze the start date for reproducible golden comparisons; keep named partial-
week fixtures rather than eliminating partial-week coverage. Preserve historical
references as evidence and create versioned new baselines when output contracts
or metrics change. Never overwrite a failed run to make the report appear green.

Evaluate all 19 current fixtures and the new sequential cases against production
v1 and a reviewed candidate on identical code, dates and knowledge versions.
Repeat the four urban cases and the sequential blocker three times. Report each
case's numeric gates, source-based checks, retry engine, latency and failure.
Keep existing tier/volume bands and +20% latency gate. New quality criteria must
be approved before the run, not selected after seeing its results.

All pushes use `--synthetic-only`; Langfuse remains metadata-only. This is a new
experiment cycle: the earlier two refinements are exhausted, and this design is
not permission to create another prompt version or move labels. Agree a bounded
candidate/refinement budget in the implementation plan before execution.

Run `cd backend && pytest tests/unit -q -m "not kafka"`. Integration tests may
run only against the verified scratch database `uphill_ai_test`. If generated
instruction rendering changes, capture local EN/VI screenshots per the UI
screenshot-evidence skill as well as backend tests.

After offline gates, deploy only to staging using the existing checksum/stop/
rsync/start/health/stamp/smoke runbook. Verify prompt version on every smoke trace.
Exercise completed-week progression and override progression separately. Save
synthetic evidence and remove test accounts/plans afterward. Production deploy,
production prompt label, merge and readiness remain owner-controlled.

## Review checkpoints

1. Owner reviews this written design, including the proposed accounting units.
2. Write the implementation plan: source audit first, then isolated failing tests,
   minimal code changes, evaluation and staging. One logical commit per item;
   every commit ends with the required Codex co-author trailer.
3. Resolve disputed coaching rules from primary material before changing them.
   If the needed book passage cannot be verified, ask for the relevant excerpt
   or owner adjudication; do not invent an attribution or substitute a universal
   percentage.
4. Review candidate experiment budget and release gates before execution.
5. Report offline and staging results at the production HOLD checkpoint.

Do not change requirements, deploy scripts, environment files or dashboards.
Scan the complete diff and external text against the existing private denylist
without reproducing it in files. No code, remote prompts or labels were changed
while preparing this design.
