# Scheduler follow-up evaluations — 2026-10-05

**Release HOLD.** Code review approves the fixes; v11 live acceptance is blocked by the configured Gemini project's monthly spending cap. Production v1 and staging v4 remain unchanged.

The eight v9 paired arms completed. V9 fails the full suite: beginner generation error and scheduled Taper mismatch. All 15 candidate repeat cases pass. V10 and v11 have no candidate runs: followup5 and followup6 are completed production-only baselines stopped before candidate dispatch because review found code gaps. The later baseline also hit provider quota. These unpaired runs establish no candidate comparison.

| Directory / arm | Langfuse run name | Cases | Mean / P95 seconds | Harness failures | Engines primary/retry/error-or-rules | Known generation USD | Unknown costs |
|---|---|---:|---:|---:|---|---:|---:|
| [reliability-followup4-production-1](reliability-followup4-production-1/results.json) | `eval_scheduler_1791157336824589000` | 25 | 17.808 / 30.4 | 3 | 25/0/0 | 0.569956 | 0 |
| [reliability-followup4-production-repeat-1](reliability-followup4-production-repeat-1/results.json) | `eval_scheduler_1791157846491687000` | 5 | 34.840 / 61.3 | 1 | 5/0/0 | 0.164866 | 0 |
| [reliability-followup4-production-repeat-2](reliability-followup4-production-repeat-2/results.json) | `eval_scheduler_1791158056322129000` | 5 | 25.760 / 29.3 | 0 | 5/0/0 | 0.136853 | 0 |
| [reliability-followup4-production-repeat-3](reliability-followup4-production-repeat-3/results.json) | `eval_scheduler_1791158311420492000` | 5 | 29.640 / 41.9 | 0 | 5/0/0 | 0.155474 | 0 |
| [reliability-followup4-v9-1](reliability-followup4-v9-1/results.json) | `eval_scheduler_1791157639065328000` | 25 | 10.680 / 17.2 | 4 | 19/5/1 | 0.523465 | 0 |
| [reliability-followup4-v9-repeat-1](reliability-followup4-v9-repeat-1/results.json) | `eval_scheduler_1791157915695917000` | 5 | 11.920 / 18.1 | 0 | 5/0/0 | 0.090405 | 0 |
| [reliability-followup4-v9-repeat-2](reliability-followup4-v9-repeat-2/results.json) | `eval_scheduler_1791158151141832000` | 5 | 16.960 / 23.7 | 0 | 3/2/0 | 0.140139 | 0 |
| [reliability-followup4-v9-repeat-3](reliability-followup4-v9-repeat-3/results.json) | `eval_scheduler_1791158375332962000` | 5 | 10.960 / 13.4 | 0 | 5/0/0 | 0.092307 | 0 |
| [reliability-followup5-production-1](reliability-followup5-production-1/results.json) | `eval_scheduler_1791189990588070000` | 25 | 20.200 / 32.8 | 1 | 25/0/0 | 0.571278 | 0 |
| [reliability-followup6-production-1](reliability-followup6-production-1/results.json) | `eval_scheduler_1791191427959840000` | 25 | 18.712 / 35.3 | 9 | 15/1/9 | 0.372733 | 19 |


V9 full mean: 10.680 versus 17.808 seconds (-40.03%). Combined repeats: 13.280 versus 30.080 seconds (-55.85%). Faster output does not override the failed full gate. Legacy quality regresses only on the beginner full-suite case; repeats have no regressions. VI ban scan covers 77 full-suite workouts and 56 per repeat, with zero hits. Structure/access is known for 24/25 full cases and all repeats; unavailable checks remain unavailable. Full manual coaching acceptance is not claimed.

The three identity files record each baseline/code/prompt/model/date/KB snapshot. All runs use `gemini-3.8-flash`, as-of `2026-10-05`, metadata-only export and `--push-langfuse --synthetic-only`. Code/model/KB match within every completed v9 pair. No reference, healthy tier band or volume band was loosened.

Followup6 has nine rule-based-or-unknown cases after model failures. The provider reports `429 RESOURCE_EXHAUSTED: monthly spending cap exceeded`; see [provider error metadata](v11-provider-blocker.json). Its error records include duplicate logging, not unique request counts. Do not use fallback output or this unpaired baseline to approve v11 quality/latency.

Known generation cost across these ten arms: **$2.817476**. Costs are unavailable for 19 generation observations, including provider failures; embeddings excluded. Attribution matches metadata-only generations to logged synthetic attempts within two seconds. Nonmatching observations are excluded without claiming they all belong to unrelated sessions. No prompts/replies exported.

Compact outputs preserve all scores. Privacy scan: zero matches in these ten runs; raw SHA256 values are in [privacy metadata](privacy-filter.json). Earlier experiments and filtering records remain under [historical evidence](../follow-up-evals/README.md).

## Corrected code and remaining gate

Reviewed code: `0b012b5`; backend tree `159b808de76c09bea308486391849aa78ffc9d58`. Fixes cover explicit/bilateral hold targets, native async attempt cancellation, typed starting-load guards, pace-based fallback conservation, goal/tier fallback priorities, explicit equipment/default single-filler access, consistent weekly phases and contextual live scores excluding unavailable results. Full **1,289 unit tests pass**, with 23 existing warnings. The reviewer independently passes 15 fallback tests and approves the corrected code. [Review record](final-code-review.md).

V11 SHA256: `c64cea13c20a4f3e1a171bbceff8f3abeda5eb9f11eca0ed38da47cad3df4c1e`. Experiment label only, plus service-managed `latest`. Production v1, staging v4 and snapshot-exp v4 are unchanged; [final label identities](final-label-identities.json). V10 adds goal/load/phase scope corrections; v11 clarifies separate left/right hold targets. Neither candidate has completed acceptance. The local fallback remains the prior template with parser-contract corrections; deliberate synchronization is required before a future approved promotion.

After provider access is restored, freeze a new same-code environment and run production/v11 full 25-case suites, then three paired repetitions of the four Vietnam cases and healthy sequence. All 40 candidate cases must pass: no rule fallback, applicable legacy nonregression, known structure/access, unchanged volume bands, paired mean latency increase at most 20% separately for full/repeats, and manual coaching/VI acceptance. Retain every output, cost and retry. Stop again for the owner staging checkpoint.

Running screenshots preserve Execution/About: [hold targets](../hold-targets/README.md), [goal-specific walk/run](../goal-safety/README.md). Scratch `uphill_ai_test` only; temporary data and preview resources cleaned up.
