# Scheduler reliability release record

Status: offline Tasks 1–7 complete; release HOLD. Both permitted candidates failed. Staging and production unchanged.

## Frozen release contract

Plan: `docs/superpowers/plans/2026-10-04-scheduler-reliability.md`.
Source register: `docs/research/2026-10-04-scheduler-rule-register.md`.
Owner authorized execution after requiring the Vietnamese-copy skill. Apply R1–R6 to every changed/generated VI sample.

- One candidate plus at most one refinement. Stop after a failed refinement.
- All 19 existing scheduler fixtures plus invented sequential cases, same code/model/date/KB for each paired arm.
- Fixed evaluation date: 2026-10-05; keep named partial-start cases.
- Repeat four Vietnam cases and healthy sequential blocker three times per arm.
- Preserve healthy volume/tier bands and existing references. Report unavailable metrics explicitly.
- Zero new-output structure/access failures; no rule-based golden fallback; retries reported; no regression in applicable existing checks.
- Paired mean latency increase ≤20%, full suite and repeated subset reported separately.
- Long-run shares are diagnostics with explicit units; new caps are not verified or introduced.
- No lost EN/VI caveats, added claims, banned new VI wording or visible overflow.
- Every external eval push includes `--synthetic-only`; metadata-only Langfuse export.

## Execution evidence

2026-10-04: source register and plan contract created. Environment labels and live KB unchanged. Run identity (code SHA, model, prompt versions, seed hash, retrieval snapshot) will be recorded from verified values before paid execution; no guessed versions are accepted.

## Results and decisions

Experiment in progress. Production v1 and candidate v5 complete-suite results are HOLD. The one permitted refinement follows all scheduled v5 repeats; no environment label is promoted. Historical fitness results do not establish this release's gate.

2026-10-04 Task 2 diagnosis: synthetic next-block core reproduced `Actual 0.0km/0.0h` for missing logs and no watch data. Changed to `Known logged volume`, explicit unknown/missed counts, calendar coverage and override/readiness distinction. Four failing regressions became green; original gate behavior stayed green. This establishes misleading context, not proof that it alone caused the historical stochastic 110.2 km result. The paired sequential evaluation remains required.

2026-10-04 Task 3: 21 accounting tests passed; full suite 1165 passed. Indoor ascent explicitly uses belt-path geometry and stays estimated. Repeated intervals count as distinct segments; only repeated explicit IDs are invalid.

2026-10-04 Task 4: structured output derives public totals and instructions together. Added structured exercise set/rest data to retain execution detail. Legacy prompt output keeps compatibility with precision unavailable; candidate missing precision will fail its gate. Source-supported corrections remove the universal straight-set ban and short-runway readiness bypass. Fallback lacks documented advanced readiness, so it uses conservative general bodyweight Strength (existing 3x12 app choice, 90s rest) instead of advanced ME/power. The fallback's 15 min/km hiking estimate is app policy. Updated description-format tests retain exact minute sums; default-flat access now asserts zero course-inferred climbing. No seed correction was needed for already consistent ME set-order text; disputed intensity seed rules remain unchanged pending primary evidence.

2026-10-04 Task 5: contextual checks cover comparable full weeks, interval portions, prior healthy baseline after down weeks, day access, treadmill capacity, equipment and public treadmill fields. Structural/access failures are rejected before storage; policy checks are reported without silently repairing load. Limitation: free-form notes are coaching input, not independently verified structured day permissions. The four golden cases provide explicit day access; runtime mixed access without such facts remains unavailable, never a passing score. A future availability UI is outside this release.

2026-10-04 Task 6: added fixed-date, fixture filter and exclusive output-directory options; synthetic pushes now enforce the explicit privacy flag. Sequential cases call the real next-block core with stubbed persistence and omit the optional narrative call. Attribution records the worst block engine so later fallback cannot hide behind an earlier Gemini success. Candidate `--context-gates` requires known arithmetic/access, preserves internal-disclosure checks, and adds explicit planned recovery/taper and recovery-intensity expectations. Historical production precision is reported unavailable rather than called passing. No healthy mileage floor applies to illness/recovery/taper scenarios.

Verified remote prompt identities before experiment: production v1; staging v4; snapshot-exp v4. Model: `gemini-3.8-flash`. Seed file hashes: `{"backend/kb_seed/scheduler.json": "401fb69936edddefdff442d338baa01f1371fc47f5ca1a688d8a191dda55c7e0"}`. No environment label changed.

2026-10-03 19:25 UTC: experiment frozen at code `f07a82bfb8697f7d1eed9da33648b968753f143f`, model `gemini-3.8-flash`, as-of `2026-10-05`. Production v1 SHA256 `a0eab967a172a094ee5b524486b643497df24fae81406a7c1d0d2cfbf309ee4e`; candidate v5 SHA256 `44f819b730b96020caf189bc8bcd995b783db0acce2ca1c0df601d984b4eaa95`, labeled `scheduler-reliability-exp` and service-managed `latest` only. Staging remains v4; production remains v1.

Frozen read-only local scheduler KB: 37 principles, canonical SHA256 `15aaa37cb372f44fb5aecaf57ba2f7f6510a0f33585b4f42b654c0ddfc546563`; Qdrant 29 points including payload/vectors, SHA256 `60001d3f78fa26e2f8b6a9a8860fae96504cc213f38e41abea5f3088117f77b0`. Seed unchanged. Runtime free-form notes cannot prove access, so structured cases provide independent day permissions. No KB import/sweep.

Review: six Important defects reproduced and fixed (mixed legacy access bypass, recovery hike, race-course totals, coach pace, missing-week rebound, unknown positive machine incline). Deterministic single fallback also resolved; coach-authored opaque details and old remote responses remain explicitly precision unavailable. Unit suite 1206 passed, 23 existing warnings. Hook backend runtime `.venv/bin/pytest` is absent; equivalent conda pytest ran before skipping that hook alone.

UI preparation: initial local port-5432 role could not create a scratch DB. Reused existing Docker port-5433 `uphill_ai_test`; no integration tests or truncations. Worktree dependency symlink broke Turbopack; use Next's webpack dev option without changing dependencies/configuration.

2026-10-04 offline observations: production full suite has two volume failures; v5 has two rule fallbacks, two unavailable access checks, one volume failure, four paired legacy easy-share regressions and +22.13% full-suite mean latency. VI wording review also finds banned generated wording, retained as a release failure rather than rewritten evidence. Full generation costs read from Langfuse v2 observations: production 31 known-cost model generations, $0.561512; v5 40, $0.857275. These exclude embedding calls; repeated-arm costs remain pending. Deprecated traces read returned HTTP 410, so used cursor-paginated v2 generation observations, never athlete content fields.

2026-10-04 09:32 UTC: created the sole refinement, plan_generation v6 SHA256 `7a19da8c7e374c0247484ad22bc29703f5b88a3ed345899bec520b580ae36de7`, retaining all 17 variables. Only experiment/latest labels changed. Schema roles, named exercises, passive fields, redundant totals and VI wording addressed; unchanged tier/volume bands and parser. Read-only KB hashes reverified unchanged. Backend tree remains `268b52e84e71769d7dedfe272ac2ca6d55a64ad9`; later frontend commit does not change tested backend.

2026-10-04 09:38 UTC: v6 complete suite finished, run `eval_scheduler_1791106644091611000`. Mean 12.912 s vs production 17.152 s (-24.72%); no full-suite legacy score regression; all returned rows have known arithmetic/access. HOLD: recovery sequence initial block rejects inaccessible output on both attempts and falls back; fatigue next block contains Zone 5 Strides despite explicit maximum Zone 2; recreational field-threshold snapshot totals 79.8 km outside its unchanged band. Ban scan finds zero terms in 79 VI workouts, but manual review finds unnatural titles and unsupported advanced power readiness. Thus VI/coaching acceptance still fails. Required repeated subset runs continue, no further version or policy loosening.

## Final offline checkpoint

All 12 planned run batches are retained in [paired results](../superpowers/evidence/scheduler-reliability/evals/README.md), including every failed case, missing-data count, run name and model cost. All three v5 and all three v6 repeated subsets passed automated gates, but neither full candidate passes the complete acceptance contract. Decision: HOLD; recommend no staging deploy or label promotion. Next separately approved improvement: enforce recovery intensity and strength/power prerequisites, constrain VI titles to the vocabulary contract, then obtain a new evaluation budget. Do not patch failures by relaxing tier/volume bands or recapturing references.

Seven [EN/VI screenshots](../superpowers/evidence/scheduler-reliability/README.md) show exact mixed and Treadmill accounting in the running UI. Temporary synthetic user 8 and plan 1 deleted; sessions removed, preview servers stopped, viewport reset. Frontend 456 tests passed, build passed, lint 0 errors/131 existing warnings. Backend final verification is recorded below. No integration tests/TRUNCATE, KB import, requirements/deploy/env edits, dashboards, merge, ready-for-review action or staging/production label move.

Local fallback stays at the tested v5 candidate contract. Experimental v6 is not promoted; its required future fallback sync is explicitly deferred. Production v1 and staging v4 remain unchanged. The earlier fitness-snapshot staging validation does not establish readiness for these new changes.

Final verification: `pytest tests/unit -q -m "not kafka"` → 1206 passed, 23 existing warnings. Every recorded model-cost observation count matches the paid attempt log; total $3.479029 excludes embeddings. Complete diff against origin/main and all new textual evidence: zero private denylist hits. All failed/unknown results preserved; no baselines loosened.

Langfuse deviation: all 12 run names verified in retained dataset metadata after successful synthetic pushes. Detailed old run-read API returns HTTP 410; new experiment listing is empty for legacy-SDK runs. Linked dataset and committed complete local results; did not misrepresent replacement-API visibility or change dependencies.

## Approved local follow-up — 2026-10-04

The owner approved local fixes while preserving the existing athlete-facing format. This phase adds no paid run, remote prompt version, environment-label move or deployment.

Implemented: recovery limits inspect every run/hike segment, including brief Strides; latest block RPE and confirmed missed sessions are structured inputs, with overrides preserving those facts. Declared advanced ME/max-strength/power methods require trusted preparation, and recognised jump/bound exercises cannot bypass the power check with a generic Strength label. The conservative fallback names bodyweight equipment. Independent day permissions still apply to every segment, with race-course permission separate.

Resolved weekly distance is checked against explicit bounds. Automatic healthy snapshot bounds reuse the existing 80% prompt floor and tier's 10% growth cap; initial full weeks 1/2 and the first full subsequent-block week are checked. These are application policy, not claimed book percentages. Recovery/Taper/Race Week and partial weeks are exempt; reported hard fatigue/readiness flags and confirmed missed training suspend automatic healthy bounds. A rejected output receives its check failure in the existing single retry. No silent mileage scaling or weakened golden assertions.

Presentation: familiar Execution/About tabs and timeline restored; generic library quantities do not replace resolved instructions. Missing phases are not invented. Strength's Main Set contains only its duration/exercise targets, while the card retains total session locomotion distance. Fractional warm-up/cool-down minutes are preserved. Rationale is stored as the existing Reason section. VI uses short canonical workout titles and English technical terms. Seven [new screenshots](../superpowers/evidence/scheduler-reliability/local-follow-up/README.md) document the running synthetic UI.

Verification: backend `pytest tests/unit -q -m "not kafka"` — 1217 passed, 23 existing warnings. Frontend final verification is recorded in the follow-up PR update. UI used only `uphill_ai_test`; no integration tests or TRUNCATE. Temporary users/plans/sessions deleted, servers stopped and viewport reset. Backend hook runtime remains absent; skip only that hook after the equivalent conda suite passes.

Decision: **HOLD**. This follow-up changes local request constraints and deterministic checks, so old model quality/latency measurements cannot establish its release readiness. Remote production v1/staging v4 and experiment v6 are untouched. A fresh paired synthetic model evaluation, coaching/VI review and latency gate require a separately approved budget. Do not deploy or promote from unit-test success. Free-form access/preparation and complete semantic readiness validation remain unavailable; no new availability/readiness UI is introduced here.

2026-10-04 12:43 UTC final local verification: backend 1217 passed/23 existing warnings; frontend 460 passed; static build passed; lint 0 errors/131 existing warnings. All seven final screenshots retained. Synthetic users 9/10 and plans 2/3 plus sessions were verified deleted from `uphill_ai_test`; no truncation. Full origin/main diff, new textual evidence and PR description: zero private denylist hits. Current model gate remains HOLD; no new model results or latency claims.
