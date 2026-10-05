# V13 completed paired evaluation

Decision: HOLD. The full Vietnamese sub-elite treadmill case fails volume_fit on the primary attempt, then strength_readiness on the retry and falls back to rules. Its fallback access is unavailable. The rejected draft is not retained, so the exact advanced method is unknown. The Vietnamese 42 km volume rejection recovered through retry. All outputs, scores and failed history remain retained.

| Arm | Run | Cases | Mean seconds | Engines | Failures |
|---|---|---:|---:|---|---:|
| reliability-followup9-production-1 | eval_scheduler_1791207810056860000 | 25 | 19.772 | {'gemini': 25} | 1 |
| reliability-followup9-production-repeat-1 | eval_scheduler_1791208376368851000 | 5 | 32.620 | {'gemini': 5} | 1 |
| reliability-followup9-production-repeat-2 | eval_scheduler_1791208632031978000 | 5 | 30.260 | {'gemini': 5} | 2 |
| reliability-followup9-production-repeat-3 | eval_scheduler_1791208890729893000 | 5 | 30.880 | {'gemini': 5} | 0 |
| reliability-followup9-v13-1 | eval_scheduler_1791208179562741000 | 25 | 13.172 | {'gemini': 21, 'gemini_retry': 3, 'rule-based-or-unknown': 1} | 2 |
| reliability-followup9-v13-repeat-1 | eval_scheduler_1791208470217078000 | 5 | 17.080 | {'gemini': 4, 'gemini_retry': 1} | 0 |
| reliability-followup9-v13-repeat-2 | eval_scheduler_1791208726203151000 | 5 | 16.480 | {'gemini': 4, 'gemini_retry': 1} | 0 |
| reliability-followup9-v13-repeat-3 | eval_scheduler_1791208993958856000 | 5 | 18.460 | {'gemini': 5} | 0 |

Matched metadata-only model cost: $1.844510, 104 logged attempts; matching details and unavailable costs, if any, remain explicit in costs.json. Embeddings excluded. Frozen identity is in identity.json; same model, fixed as-of date and KB across all arms. Production v1/staging v4 unchanged.

V14 makes the existing trusted readiness restriction explicit during volume retries. Independent review approved the focused wording and found no code blocker, but declined to infer the unknown rejected exercise or paid effectiveness. No dose, threshold, fixture band, public workout-format change or deployment. V14 requires a fresh full paired gate. Raw hashes and privacy replacements are recorded in privacy-filter.json; legacy-score and VI scans in review.json. V13 is not claimed manually/UI accepted.
