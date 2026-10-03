# Fitness snapshot release record

**Current recommendation, 2026-10-03: HOLD production promotion.** Repeated
offline v4 evaluations pass, but the trace-verified staging no-COROS next block
misses its unchanged volume band. Staging code is deployed and its prompt label
is v4; production remains v1. See the follow-up section below.

## Decision at the owner checkpoint

2026-10-02: Task 11 **PASS**. `plan_generation` v4 at `snapshot-exp` is eligible
for staging promotion only after the owner authorizes Task 13 and the staging
code deployment and smoke test succeed. Production and staging still resolve
to v1. No deployment or environment-label promotion has been performed.
The draft PR remains a draft.

The final elite snapshot case produces 120.6 km in week 2, closer to its 136 km
snapshot than the production baseline's 100.4 km (absolute errors 15.4 vs 35.6 km).
All three snapshot tier and volume gates pass. These are single stochastic runs,
not confidence intervals. The volume gate bands admit 80–90% in some cases;
the stronger 90–100% prompt guidance is not fully met by every final case.
No gate or assertion was relaxed.

## Runs and prompt versions

Every published run used all 15 synthetic scheduler fixtures, `--push-langfuse
--synthetic-only`, and `LANGFUSE_ENVIRONMENT=development`. Content export stayed
false. Credentials were read from the operator's existing backend environment;
no environment file was created or edited. No real athlete records were exported.

| Run | Template / label | Gate | Change |
|---|---|---|---|
| `eval_scheduler_1790937733` | v1 / production | FAIL | Baseline: two snapshot volume failures |
| `eval_scheduler_snapshot-exp_1790937966` | v2 / snapshot-exp | FAIL | Exact FITNESS SNAPSHOT RULES paragraph from Task 11, directly after `{{user_summary}}` |
| `eval_scheduler_snapshot-exp_1790938206` | v3 / snapshot-exp | FAIL | First refinement: explicitly sum week-2 distances and allocate sufficient aerobic minutes |
| `eval_scheduler_snapshot-exp_1790938547` | v4 / snapshot-exp | PASS | Second refinement: retain the snapshot budget through build modifiers and partial-week proration; recheck distance after pace conversion |

The two permitted refinements are exhausted. All 17 original template variables,
config and tags were preserved. Creation requests supplied only the custom label
`snapshot-exp`; Langfuse automatically also attaches its `latest` label.
Neither `staging` nor `production` was supplied or moved. Re-read on
2026-10-02 after the final run: production v1, staging v1, snapshot-exp v4.

## Snapshot comparison

Week-2 distances in km; values outside the fixture band are marked FAIL.

| Fixture | Expected tier | Allowed km | Production v1 | v2 | v3 | Final v4 |
|---|---|---|---|---|---|---|
| elite_no_coros | sub_elite | 115–150 | 107.1 FAIL | 117.2 | 134.8 | 117.2 |
| elite_unmeasured_thresholds | sub_elite | 110–145 | 100.4 FAIL | 108.1 FAIL | 107.7 FAIL | 120.6 |
| recreational_field_thresholds | recreational | 55–78 | 61.2 | 63.8 | 65.6 | 65.0 |

All snapshot `tier_match` scores are true in every run.

## Promotion conditions

| Check | Final evidence | Result |
|---|---|---|
| Scheduler gate | `[gate] PASS scheduler`; 15/15 Gemini, no rule fall-through | PASS |
| Snapshot fixtures | 3/3 tier matches and week-2 bands; elite absolute error falls from 35.6 to 15.4 km | PASS |
| Other fixtures | No `plan_checks` score is lower on any fixture; no `gemini_retry` in any run | PASS |
| Cost / latency | Mean 10.567s → 9.693s (-8.26%); limit 12.680s | PASS |

Mean latencies v1/v2/v3/v4: 10.567s, 10.020s, 9.720s, 9.693s.

### All-fixture comparison

Each cell shows `plan_checks / latency_s`, in run order. Every engine is Gemini.
The three snapshot cases remain at 2/3 checks: the existing progression check
compares the partial first week with a full second week. This behavior exists
in the baseline and no candidate worsens it. The other 12 cases score 1.0.

| Fixture | Baseline v1 | v2 | v3 | Final v4 |
|---|---|---|---|---|
| beginner_start_running | 1.000 / 9.5s | 1.000 / 9.5s | 1.000 / 8.4s | 1.000 / 8.2s |
| elite_utmb | 1.000 / 9.4s | 1.000 / 9.6s | 1.000 / 10.4s | 1.000 / 8.5s |
| masters_trail_50k | 1.000 / 7.5s | 1.000 / 7.5s | 1.000 / 8.4s | 1.000 / 6.9s |
| novice_10k | 1.000 / 7.3s | 1.000 / 6.5s | 1.000 / 6.2s | 1.000 / 6.7s |
| recreational_50k | 1.000 / 7.4s | 1.000 / 7.2s | 1.000 / 6.4s | 1.000 / 7.3s |
| return_from_injury | 1.000 / 7.7s | 1.000 / 9.1s | 1.000 / 6.8s | 1.000 / 7.4s |
| short_block_4wk | 1.000 / 8.4s | 1.000 / 7.4s | 1.000 / 6.6s | 1.000 / 7.7s |
| snapshot_elite_no_coros | 0.667 / 20.1s | 0.667 / 16.3s | 0.667 / 18.9s | 0.667 / 17.6s |
| snapshot_elite_unmeasured_thresholds | 0.667 / 19.1s | 0.667 / 20.0s | 0.667 / 16.1s | 0.667 / 15.1s |
| snapshot_recreational_field_thresholds | 0.667 / 20.6s | 0.667 / 20.5s | 0.667 / 21.5s | 0.667 / 20.9s |
| subelite_100k | 1.000 / 10.6s | 1.000 / 6.6s | 1.000 / 7.3s | 1.000 / 9.6s |
| time_goal_marathon | 1.000 / 8.9s | 1.000 / 8.0s | 1.000 / 7.0s | 1.000 / 6.8s |
| trail_8wk | 1.000 / 6.9s | 1.000 / 6.7s | 1.000 / 6.3s | 1.000 / 6.7s |
| vertical_km_no_gym | 1.000 / 6.6s | 1.000 / 7.3s | 1.000 / 6.9s | 1.000 / 6.9s |
| vi_trail_42k | 1.000 / 8.5s | 1.000 / 8.1s | 1.000 / 8.6s | 1.000 / 9.1s |

## Execution evidence and deviations

- Requested backend unit suite: **1133 passed**, 23 warnings, 35.39 s:
  `cd backend && pytest tests/unit -q -m "not kafka"`. The synthetic-value
  replacement alone passed 1131 tests; the runner correction adds two cases.
  No integration suite was run in this continuation. UI seeding used only the
  scratch database named `uphill_ai_test`, without truncation.
- [UI screenshots and synthetic seed details](../superpowers/evidence/fitness-snapshot/README.md):
  Profile EN/VI, both onboarding paths, planner COROS prefill. Registration
  was used because email session restore does not open onboarding. The race
  onboarding native select clips its long English value; recorded, not changed.
- [Score configs and owner widget step](2026-10-fitness-snapshot-score-configs.md):
  both required configs created and re-fetched; no dashboard changed.
- The code defaults to one-week blocks, while the spec gates week 2. An initial
  baseline attempt was stopped before publication. The offline runner now
  explicitly requests at least two weeks only for cases with a week-2 gate.
  Its regression test failed before the fix (2 failures) and passes after it
  (7 tests). Production block sizing was not changed.
- The requested production capture command ran. Its new references initially
  contained only week 1; one also failed the literal privacy scan in generated
  prose. All three were authentically recaptured against production v1 using
  the corrected two-week runner, accepting only Gemini outputs that pass the
  scan before saving. The baseline commit contains only the three new refs.
  Reference captures are separate stochastic calls from the published baseline
  experiment; their week-2 totals are 120.4, 95.4 and 45.7 km respectively.
  Baseline volume failures are retained rather than edited.
- Langfuse's legacy Dataset Runs read API returns HTTP 410
  `LEGACY_API_UNAVAILABLE_FOR_NEW_ORGANIZATION` for this project. The current
  Experiments listing returned no native experiment rows for the existing
  legacy exporter. Comparison therefore used the current Scores API, retrieving
  the deterministic trace IDs for each run and confirming all 15 score sets.
  The run names above are published legacy-exporter names, not verified native
  Runs UI rows. A separate exporter migration is needed for native Experiments
  UI grouping; dependencies and the exporter were not changed here.
- No explicit ADS-based intensity reduction was observed in the inspected elite
  outputs. Raw ADS prompt wiring remains a potential follow-up if future traces
  show it overriding the unmeasured-threshold rule; no ADS code change was made.
- The worktree lacks the hook's `.venv/bin/pytest`; the hook also omits the
  requested Kafka exclusion. Backend hook execution was skipped after the
  requested suite passed manually; other applicable pre-commit checks ran.
- Whole diff against `origin/main`: case-insensitive owner denylist scan **zero
  hits**. Requirements, deploy scripts and environment files are unchanged.
  No real identities are recorded in this runbook. Each deferred item has one
  commit ending in the requested Codex co-author line.
- Independent read-only review found no critical or important issue in the
  synthetic substitutions, runner correction and local evidence. Remote prompt
  provenance and score-config state were operator-verified, not independently
  verified by the reviewer.

## Staging procedure recorded at the original checkpoint (2026-10-02)

Target: `/opt/uphill-ai-backend-staging`, backend port 8001, Postgres port 5434.
At the original checkpoint no step below had run. Actual UTC execution
timestamps and outcomes are in the follow-up section below. Record command/output evidence
in each row after authorization. User instructions authorize the PR checkout
for staging after the checkpoint; do not wait for or merge main.

| Step | UTC timestamps | Status / evidence |
|---|---|---|
| Checksum dry-run and inspect changes | — | PENDING owner go-ahead |
| Stop staging backend | — | PENDING |
| Rsync staging backend with `.env*` excluded | — | PENDING |
| Start staging backend; wait for health | — | PENDING |
| `alembic stamp head` | — | PENDING |
| Test-account Profile/plan smoke; stored snapshot and `plan_tier` trace | — | PENDING |
| Move staging label to v4 only after successful smoke; generate another plan and verify prompt version | — | PENDING; experiment PASS |

Run from the reviewed PR worktree. Checksum dry-run:

```bash
rsync -rnc --itemize-changes --exclude '.env*' --exclude 'venv*' --exclude '__pycache__' --exclude 'qdrant_storage' backend/ root@45.119.215.120:/opt/uphill-ai-backend-staging/backend/
```

After inspecting the dry-run, stop only the staging service with
`cd /opt/uphill-ai-backend-staging && docker compose stop backend` on the server.
Run the same rsync with `-rc` instead of `-rnc`. Start the same staging service
with `docker compose start backend`, wait for
`curl -fsS localhost:8001/api/health`, then run
`docker compose exec backend alembic stamp head`. Startup `init_db` creates the
additive objects; do not run `alembic upgrade` over those objects.
Migration head: `b4f1c2d3e5a6` (parent `43dfcba89eff`).

With a staging test account, save the threshold source and generate a plan.
Inspect only that account's new plan for `fitness_snapshot` tier and
`weekly_km_source`; confirm the staging trace's `plan_tier` score. Since the
experiment passed, then move only `staging` to v4, generate a second test plan
and verify the candidate prompt version on its trace. Keep `production` on v1.
Production deployment, release tagging, dashboards and production prompt
promotion belong to the owner and are outside this continuation.

## Follow-up: repeated evaluations and staging — 2026-10-03

The owner authorized three additional paired baseline/v4 evaluations and the
staging initial-plan/next-block validation. No new prompt version, fixture,
assertion or gate was introduced. `production` stays v1; `snapshot-exp` stays v4.

### Repeated evaluation results

All six runs used the full 15-case set with `--push-langfuse --synthetic-only`.
All 90 score sets were re-read through the current Scores API and matched the
local evaluation results. Native legacy Runs grouping remains unavailable.
These runs occurred on Saturday UTC; the original experiment ran Friday.
The paired runs share the same calendar context, but their partial first-week
size differs from the original experiment. These are three repetitions of
three fixed cases, not nine independent athlete populations.

Each distance cell is baseline → v4, in km. Bands are unchanged:
no-COROS 115–150, elite snapshot 110–145, recreational 55–78.

| Pair | Baseline v1 run | Candidate v4 run | No COROS | Elite snapshot | Recreational | Mean latency |
|---|---|---|---|---|---|---|
| 1 | `eval_scheduler_production_1791029636` | `eval_scheduler_snapshot-exp_1791029781` | 107.3 → 120.9 | 113.0 → 130.5 | 59.2 → 62.1 | 8.080 → 8.593s (+6.35%) |
| 2 | `eval_scheduler_production_1791029926` | `eval_scheduler_snapshot-exp_1791030069` | 116.1 → 132.5 | 84.1 → 125.0 | 51.9 → 65.9 | 8.500 → 8.400s (-1.18%) |
| 3 | `eval_scheduler_production_1791030211` | `eval_scheduler_snapshot-exp_1791030352` | 130.6 → 128.4 | 93.9 → 127.0 | 64.8 → 65.7 | 8.093 → 8.300s (+2.55%) |

- Production passes 5/9 snapshot volume checks; v4 passes **9/9**, with **3/3
  scheduler gates PASS**. All snapshot tiers match in every run.
- All 90 outputs use Gemini; no retries or rule fall-through. No fixture's
  `plan_checks` is lower than its paired baseline.
- Mean across all baseline cases: 8.224 s; candidate: 8.431 s (**+2.51%**).
  Every paired mean is below its baseline +20% ceiling. This is a latency
  comparison, not a measurement of token cost.
- Elite snapshot volume: baseline mean 97.0 km (range 84.1–113.0), candidate
  mean 127.5 km (125.0–130.5), versus a measured 136 km. Candidate absolute
  error averages 8.5 km, compared with 39.0 km for the baseline.
- Final repeated offline outputs contain tempo work, with 81.9–84.9% of run
  minutes easy. The measured elite/recreational tempo paces are 4:30–4:07 and
  5:16–4:49 per km, consistent with their threshold-derived Zone 3 bands.
  These checks do not independently establish the athlete's physiology.
- All final offline cases assign 0 m ascent because fixture terrain access
  defaults to flat. That is a coverage limitation for snapshot vert: the
  staging smoke explicitly uses mixed terrain instead.
- The prompt's 90–100% guidance is still not perfectly obeyed: the no-COROS
  case retains 86.4%, 94.6%, 91.7% across repeats. Its gate allows this range.

### Staging sequential-path results

The staging service was deployed from PR head `7492069`, using the reviewed
checksum dry-run → stop → rsync excluding `.env*` → start sequence. Startup
health took several minutes. `init_db` created the additive objects and the
confirmed Alembic head is `b4f1c2d3e5a6`. No integration suite, truncation,
requirements change, deploy-script change or environment-file edit occurred.

Three newly created synthetic accounts used the fixture profiles. COROS cases
received four complete weeks of synthetic runs and a fresh synthetic assessment;
no live COROS credentials or activity fetch was used. Profile source was saved
through the API and re-read. Initial generation and block 2 were invoked through
the authenticated application endpoints. The documented `override_gate=true`
was used because these synthetic accounts had no completed first-week workouts;
this exercises the next-block path with zero completion, not a completed-week
athlete. Consequently, the offline and staging contexts are not identical.

| Case / attempt | Initial km (partial week) | Full week-2 km / band | Week-2 ascent | Prompt versions initial → next | Result |
|---|---|---|---|---|---|
| Elite COROS baseline | 47.8 | 82.0 / 110–145 | 1,900 m | v1 → v1 | Volume FAIL |
| No-COROS first candidate attempt | 37.5 | 124.2 / 115–150 | 5,070 m | v1 → v4 | Mixed-version attempt; retained, not the final v4 pair |
| No-COROS trace-verified recheck | 45.6 | **110.2 / 115–150** | 3,770 m | v4 → v4 | **Volume FAIL** |
| Elite COROS candidate | 48.9 | 123.2 / 110–145 | 5,200 m | v4 → v4 | PASS |
| Recreational COROS candidate | 24.5 | 71.7 / 55–78 | 805 m | v4 → v4 | PASS |

The no-COROS recheck was required to establish prompt provenance after the first
initial generation still used cached v1 despite waiting 305 seconds after label
promotion. The actual configured cache TTL is 300 seconds; exact cause of the
extra delay was not established. Both attempts remain in this record; the second
was not a retry to turn a gate failure into a pass. All six final candidate
initial/next-block traces explicitly carry `plan_generation` v4 and environment
`staging`, with Gemini engine and the expected tier.

Measured elite `plan_volume_fit` improves from 0.603 on staging v1 to 0.906 on v4;
recreational v4 scores 0.990. No-COROS has no `plan_volume_fit` score because the
metric deliberately requires measured COROS volume. The tier score still appears.
All single-week staging `plan_checks` are 1.0; they do not enforce the snapshot
volume band, which is why this independent distance check matters.

Mixed-terrain elite v4 retains the full 5,200 m measured ascent; recreational v4
assigns 805 m versus its 650 m snapshot (+23.8%). There is no existing hard vert
band. Elite week 2 is 81.6% easy running with Zone 3 tempo at 4:30–4:07/km;
recreational is 100% easy in this early-base week. The no-COROS recheck includes
hill sprints and tempo, so unknown-provenance thresholds did not eliminate all
intensity. Its pace bands are estimated from stored profile defaults, not a
measured threshold. No snapshot/source/tier disclosure was found in the inspected
athlete-facing workout text. These observations are checks of generated output,
not validation of physiological measurements.

[Trace-verified synthetic plan samples](../superpowers/evidence/fitness-snapshot/staging-plan-samples.json)
retain both generated weeks for the three final v4 cases, with sources, pace,
vert, intensity and initial/next-block trace IDs. Database user/plan/workout IDs
and credentials are omitted. The earlier cache-mixed attempt remains summarized
above. Remote tracing was verified through bounded Observations API v2 queries
and Scores API v3; no prompt/reply content was exported. See the
[Langfuse public API documentation](https://langfuse.com/docs/api-and-data-platform/features/public-api).

### Follow-up decision

**HOLD production promotion.** Repeated offline gates pass, and the measured
COROS staging cases improve substantially, but the no-COROS sequential path
produces 110.2 km: below its 115 km band and below 80% of the 140 km typed load.
Its stored snapshot still says 140 km, `self_reported`, `sub_elite`, with no
readiness exception. The zero-completion override context may influence the
response; the cause is not established and should not be silently treated as
an injury/fatigue exception.

A follow-up should distinguish incomplete-week adaptation from ordinary
completed-week progression and verify that the planned weekly budget survives
minute-to-distance conversion on the sequential path. Keep the gate unchanged.
The original two prompt refinements remain exhausted; no v5 was created.
Staging stays on v4 for investigation; production stays on v1. Production code,
label promotion and fallback synchronization remain owner-owned.

### UTC execution log

Timestamps below mark completed actions unless noted. The early stamp attempt
was submitted before health confirmation, contrary to the required order; the
stamp was repeated and verified after health. No `alembic upgrade` ran.

| UTC | Step | Evidence / result |
|---|---|---|
| 2026-10-03T12:12:56.319124+00:00 | checksum dry-run | 194 changed/new paths inspected; env and requirements excluded/unchanged; staging older than PR |
| 2026-10-03T12:13:24.044658+00:00 | backup and stop | staging-only code backup; backend stopped |
| 2026-10-03T12:13:45.676796+00:00 | rsync and start | code synced excluding .env*; existing staging container started |
| 2026-10-03T12:18:37.104749+00:00 | health check | HTTP200 healthy on localhost:8001; initial resets during startup |
| 2026-10-03T12:18:37.105085+00:00 | early stamp deviation | stamp submitted before health confirmed; corrected by repeating after health, no upgrade run |
| 2026-10-03T12:19:14.298502+00:00 | post-health stamp and seed | stamp head re-run; synthetic accounts seeded; inspect seed log for success |
| 2026-10-03T12:23:54.937119+00:00 | staging prompt promotion | staging v1 -> v4 after code/profile/snapshot/trace smoke; production remains v1 |
| 2026-10-03T12:36:08.592889+00:00 | candidate smoke and trace verification | all six final generation traces staging v4/Gemini/tier match; measured cases pass; no-COROS next block110.2km fails115km minimum; first cached-v1 attempt retained separately |
| 2026-10-03T12:39:42.416772+00:00 | cleanup and final health | five synthetic plans and three test accounts removed; initial user-only cleanup rolled back on created-by FK; staging HTTP200 healthy |
| 2026-10-03T12:21:35.268779+00:00 | baseline: Profile + initial/next-block APIs, elite_unmeasured_thresholds | Completed; distances and prompt provenance recorded above |
| 2026-10-03T12:29:38.329577+00:00 | candidate: Profile + initial/next-block APIs, elite_no_coros | Completed; distances and prompt provenance recorded above |
| 2026-10-03T12:30:23.704651+00:00 | candidate: Profile + initial/next-block APIs, elite_unmeasured_thresholds | Completed; distances and prompt provenance recorded above |
| 2026-10-03T12:30:57.328105+00:00 | candidate: Profile + initial/next-block APIs, recreational_field_thresholds | Completed; distances and prompt provenance recorded above |
| 2026-10-03T12:33:32.849342+00:00 | candidate-recheck: Profile + initial/next-block APIs, elite_no_coros | Completed; distances and prompt provenance recorded above |

The synthetic accounts and all five associated test plans were removed after
saving the samples. Cleanup used exact test emails and owned plan rows, without
truncating any table. Final staging health is HTTP 200.
