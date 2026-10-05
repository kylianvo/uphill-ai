# Fresh scheduler follow-up evaluation

**Decision: HOLD. Do not deploy or promote v8.**

V8 passes the complete 25-case automated suite and two of three five-case repeats. Repeat 2 fails the unchanged healthy-sequence week-2 volume band: 156.5 km, maximum 150. Manual coaching review finds rep-only Plank/Side Plank targets without hold units. Full paired mean latency fails the allowed +20% growth gate. These failures remain retained; no assertion, reference or result was loosened.

## Latest same-code pair

| Measure | Production v1 | Candidate v8 |
|---|---:|---:|
| Full mean latency | 16.992 s | 89.372 s |
| Full p95 latency | 26.6 s | 13.7 s |
| Three-repeat combined mean | 26.080 s | 14.873 s |
| Full automated failures | 1 volume failure | 0 |
| Repeat automated failures | 4 volume failures across 3 batches | 1 volume failure |
| Full primary / retry / rules | 25 / 0 / 0 | 21 / 4 / 0 |
| Paired legacy-check regression | Baseline | None in full or repeats |
| Arithmetic / access / intensity accounting | Unavailable legacy precision | Known and passing in all 40 cases |
| Manual coaching acceptance | Not certified by legacy precision | FAIL: ambiguous hold targets |

Full mean changes by +425.97%; repeated-subset mean by -42.97%. Do not mix these populations. The full suite retains the beginner case's **2013.3-second** transport-timeout/retry outlier. Its cause is not established; p95 does not erase the mean failure. A per-read HTTP timeout does not prove an end-to-end wall-clock deadline.

Known generation cost for this continuation: **$4.878681**, including the two interrupted attempts. Three failed/interrupted generation costs are unknown, not zero; embeddings are excluded. Historical earlier experiment cost $3.479029 is separate. All attributed generation counts match attempt logs; two overlapping unrelated observations were excluded using this task's request start times. Langfuse returned one HTTP 429 during cost collection; resumed only the remaining reads after backoff.

## What changed

- Local constraints now append on fixtures without explicit day access; the previous import-scope error is fixed.
- Undeclared short maximal uphill efforts cannot bypass recognised power-readiness validation. Sustained easy climbing remains distinct. The 15-second recognition boundary is software policy, not a book-prescribed dose.
- Scheduler HTTP transport uses a 120-second read timeout and one SDK attempt; the existing primary plus one application retry remains. Evaluation saves completed cases before later calls/publishing. A partially completed sequence still lacks block-level checkpoints.
- Progression uses structured locomotion minutes, preserving the existing 15% limit; exact +15% passes, +16% fails. Previous legacy-score regressions remain recorded rather than rescored.
- Non-Race structured fueling is rendered from complete session duration and existing application bands/quantities, without the invented metabolic-threshold claim. Race-specific policy is preserved.
- The existing athlete-facing Execution/About timeline remains. Complete machine ranges, exact resolved climb estimates and actual main-set quantities are shown; whole-session distance stays on the card.

The source register remains authoritative: numerical fueling/progression/recognition policies are existing or explicitly identified application choices, not universal claims from Training for the Uphill Athlete. No knowledge-base import or source rewrite occurred.

## Manual and Vietnamese review

All candidate VI titles/instructions/fueling retain technical vocabulary, quantities and estimated-ascent caveats. The scan covers 77 VI workouts in the full run and 56 in each repeat, with zero banned wording hits. Real EN/VI [desktop/mobile evidence](ui/README.md) verifies the preserved format and corrected ranges/fueling. Generated evidence is retained, including unclear isometric instructions; the scan is not a substitute for coaching review.

Representative unresolved case: full v8 recreational Treadmill Thursday uses Plank/Side Plank as `3 x 1` without a hold duration. Other cases use rep-only hold numbers without units. Review details are in [manual hold targets](manual-hold-target-review.json). Per-session minutes cannot define each hold. Free-form access/preparation and complete semantic readiness remain unavailable; absence of recognised advanced methods is not proof of preparation.

Starting-load gap: the failed healthy sequence uses typed current weekly volume without a watch snapshot; contextual volume-fit is unavailable. Passing progression is not evidence of passing its independent golden band. Review typed-volume enforcement without relaxing that band.

## Every completed run

Each candidate is paired with production on its own frozen backend. V6, v7 and v8 backend versions differ, so their raw times are not a single controlled cross-version comparison. The v6/v7 manual failures and original legacy-score flags remain recorded.

| Artifact directory | Langfuse run name | Cases | Mean / p95 (s) | Primary / retry / rules | Harness failures | Known cost (USD) |
|---|---|---:|---:|---:|---:|---:|
| [reliability-followup-production-2](reliability-followup-production-2/results.json) | `eval_scheduler_1791119207250470000` | 25 | 18.744 / 32.1 | 25 / 0 / 0 | 1 | 0.565591 |
| [reliability-followup-v6-2](reliability-followup-v6-2/results.json) | `eval_scheduler_1791119554772748000` | 25 | 12.640 / 22.9 | 23 / 2 / 0 | 0 | 0.561222 |
| [reliability-followup2-production-1](reliability-followup2-production-1/results.json) | `eval_scheduler_1791120861701881000` | 25 | 19.236 / 28.9 | 25 / 0 / 0 | 0 | 0.565566 |
| [reliability-followup2-production-repeat-1](reliability-followup2-production-repeat-1/results.json) | `eval_scheduler_1791121354349158000` | 5 | 28.020 / 30.6 | 5 / 0 / 0 | 0 | 0.151153 |
| [reliability-followup2-production-repeat-2](reliability-followup2-production-repeat-2/results.json) | `eval_scheduler_1791121590569825000` | 5 | 27.960 / 33.9 | 5 / 0 / 0 | 0 | 0.137126 |
| [reliability-followup2-production-repeat-3](reliability-followup2-production-repeat-3/results.json) | `eval_scheduler_1791121838574868000` | 5 | 28.120 / 29.9 | 5 / 0 / 0 | 1 | 0.139429 |
| [reliability-followup2-v7-1](reliability-followup2-v7-1/results.json) | `eval_scheduler_1791121184629768000` | 25 | 11.684 / 18.5 | 22 / 3 / 0 | 0 | 0.531385 |
| [reliability-followup2-v7-repeat-1](reliability-followup2-v7-repeat-1/results.json) | `eval_scheduler_1791121440816621000` | 5 | 15.240 / 16.1 | 5 / 0 / 0 | 0 | 0.113194 |
| [reliability-followup2-v7-repeat-2](reliability-followup2-v7-repeat-2/results.json) | `eval_scheduler_1791121686950732000` | 5 | 17.260 / 25.6 | 4 / 1 / 0 | 0 | 0.132895 |
| [reliability-followup2-v7-repeat-3](reliability-followup2-v7-repeat-3/results.json) | `eval_scheduler_1791121924742210000` | 5 | 15.420 / 17.5 | 5 / 0 / 0 | 0 | 0.102976 |
| [reliability-followup3-production-1](reliability-followup3-production-1/results.json) | `eval_scheduler_1791148177110016000` | 25 | 16.992 / 26.6 | 25 / 0 / 0 | 1 | 0.562342 |
| [reliability-followup3-production-repeat-1](reliability-followup3-production-repeat-1/results.json) | `eval_scheduler_1791150629955807000` | 5 | 29.000 / 43.5 | 5 / 0 / 0 | 2 | 0.167036 |
| [reliability-followup3-production-repeat-2](reliability-followup3-production-repeat-2/results.json) | `eval_scheduler_1791150857721683000` | 5 | 23.920 / 32.5 | 5 / 0 / 0 | 1 | 0.134710 |
| [reliability-followup3-production-repeat-3](reliability-followup3-production-repeat-3/results.json) | `eval_scheduler_1791151062823996000` | 5 | 25.320 / 27.6 | 5 / 0 / 0 | 1 | 0.139406 |
| [reliability-followup3-v8-1](reliability-followup3-v8-1/results.json) | `eval_scheduler_1791150453798549000` | 25 | 89.372 / 13.7 | 21 / 4 / 0 | 0 | 0.473804 |
| [reliability-followup3-v8-repeat-1](reliability-followup3-v8-repeat-1/results.json) | `eval_scheduler_1791150728209459000` | 5 | 17.760 / 27.7 | 3 / 2 / 0 | 0 | 0.136987 |
| [reliability-followup3-v8-repeat-2](reliability-followup3-v8-repeat-2/results.json) | `eval_scheduler_1791150926277835000` | 5 | 11.900 / 17.2 | 5 / 0 / 0 | 1 | 0.103774 |
| [reliability-followup3-v8-repeat-3](reliability-followup3-v8-repeat-3/results.json) | `eval_scheduler_1791151146518025000` | 5 | 14.960 / 21.1 | 3 / 2 / 0 | 0 | 0.128325 |

Run names verified in retained [Langfuse dataset metadata](https://cloud.langfuse.com/project/cmu6scbt0004gad0c9z4e9kmx/datasets/cmunujh7n00omad0c2w0kxohy). Deprecated detailed reads return HTTP 410; replacement listing does not expose these legacy-SDK runs. Complete local results are committed, rather than claiming replacement-API visibility. Every external push used `--synthetic-only`; generated output is not exported to Langfuse.

## Identity, verification and deviations

Latest pair frozen at code `0b9adcb153bf7a1cae1a40241492a99dabed0656`, backend tree `67e39f5f669eae2a34a852cf5f5fe16a3a4db79e`, model `gemini-3.8-flash`, as-of `2026-10-05`. [Hashes](identity.json) record seed, principles and Qdrant identity. [Remote labels](verified-labels.json) reverified: production v1, staging v4, snapshot-exp v4; experiment v8 only. No environment promotion or deploy.

Backend: 1232 unit tests passed, 23 existing warnings. Frontend: 462 tests passed; static build passed; lint 0 errors/131 existing warnings. The absent `.venv/bin/pytest` hook was skipped only after equivalent conda verification. No integration tests/TRUNCATE, requirements/deploy/env edits, dashboard changes, merge or ready-for-review action. Owned UI test data/servers/tab were cleaned up.

The owner explicitly waived the earlier experiment spend/one-refinement limit. Two interrupted attempts are separately recorded, never counted as completed cases or latency passes. Five incidental substring matches in romanized generated baseline prose were replaced with `[privacy-filtered]` in committed text; scores and all other values are unchanged. [Filtering counts and original raw hashes](privacy-filter.json) disclose those substitutions. Private denylist scan remains zero in the final diff/new text.

## Next correction before another release gate

Make isometric hold units explicit and reject ambiguous targets; render supplied values in the current timeline without inventing a hold dose. Investigate/reproduce the extreme request duration and verify a real end-to-end deadline. Review typed starting-load enforcement, keeping the golden bands unchanged. Then rerun the same-code paired gate. Keep staging/production labels and deployment unchanged pending the owner's go-ahead.
