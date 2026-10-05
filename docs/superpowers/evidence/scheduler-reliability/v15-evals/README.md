# V15 completed paired evaluation

Decision: HOLD. The full elite/no-COROS fixture rejected an unsupported segment kind or setting on both primary and retry, then used rules. Exact offending fields and values were not persisted; no inference is made about them. The completed healthy sequence repaired its primary schema rejection successfully. All four Vietnam fixtures passed in the full arm and each repeat (16 observations total).

| Arm | Run | Cases | Mean seconds | Engines | Failures |
|---|---|---:|---:|---|---:|
| reliability-followup12-production-1 | eval_scheduler_1791212187759589000 | 25 | 20.348 | {'gemini': 25} | 1 |
| reliability-followup12-production-repeat-1 | eval_scheduler_1791212689432667000 | 5 | 30.840 | {'gemini': 5} | 0 |
| reliability-followup12-production-repeat-2 | eval_scheduler_1791212937590537000 | 5 | 32.000 | {'gemini': 5} | 1 |
| reliability-followup12-production-repeat-3 | eval_scheduler_1791213184150458000 | 5 | 30.960 | {'gemini': 5} | 1 |
| reliability-followup12-v15-1 | eval_scheduler_1791212498265736000 | 25 | 10.836 | {'gemini': 23, 'gemini_retry': 1, 'rule-based-or-unknown': 1} | 1 |
| reliability-followup12-v15-repeat-1 | eval_scheduler_1791212765239263000 | 5 | 13.140 | {'gemini': 5} | 0 |
| reliability-followup12-v15-repeat-2 | eval_scheduler_1791213018282531000 | 5 | 13.500 | {'gemini': 5} | 0 |
| reliability-followup12-v15-repeat-3 | eval_scheduler_1791213265761583000 | 5 | 14.060 | {'gemini': 5} | 0 |

Known metadata-only model cost: $1.711382; 100 logged attempts matched, 0 observation costs unavailable. Embeddings excluded. All eight arms retain original scores/failures, frozen code/backend/model/as-of date/KB identities and original raw hashes. Privacy filtering happens before evidence copies are written; see privacy-filter.json. No legacy-score regressions; 245 VI workouts scanned with zero banned-word hits. Production v1/staging v4/snapshot-exp v4 unchanged. The full and repeat latency comparisons pass, but cannot override the fallback gate. No full manual/UI acceptance is claimed.

Next correction approved by the owner: provider structured output with the existing workout array and segment enums. Select the structured contract from the trusted raw prompt template's exact marker; require segments locally too. Preserve production-v1 legacy generation, the existing two attempts, coaching validators, numeric bands, persistence and Execution/About. Independent architectural review supports this scope; exact failed field/value and paid effectiveness remain unknown. A fresh paired gate is required.

Backend units for frozen v15: 1,304 passed, 23 warnings. The Docker scratch database was unavailable for screenshots; created isolated native localhost:5432 uphill_ai_test instead. No v15 test-user accounts/plans were seeded and no UI acceptance screenshot was claimed.
