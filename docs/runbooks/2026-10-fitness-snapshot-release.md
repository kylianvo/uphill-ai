# Fitness snapshot release record

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

## Staging execution log — pending owner go-ahead

Target: `/opt/uphill-ai-backend-staging`, backend port 8001, Postgres port 5434.
No step below has run. Record UTC start/end times and command/output evidence
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
