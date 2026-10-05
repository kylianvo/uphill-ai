# V11 completed paired evaluation

Decision: HOLD. All 40 candidate cases pass automated gates, but manual review rejects a category-only recovery exercise and a bodyweight-only Step-up declaration in a no-gym repeat. Originals and every score remain retained; V12 will receive a fresh full gate.

| Arm | Run | Cases | Mean seconds | Engine counts | Gate failures |
|---|---|---:|---:|---|---:|
| reliability-followup7-production-1 | eval_scheduler_1791193647755663000 | 25 | 19.220 | {'gemini': 25} | 2 |
| reliability-followup7-production-repeat-1 | eval_scheduler_1791194139525006000 | 5 | 30.480 | {'gemini': 5} | 1 |
| reliability-followup7-production-repeat-2 | eval_scheduler_1791194353791956000 | 5 | 27.400 | {'gemini': 5} | 1 |
| reliability-followup7-production-repeat-3 | eval_scheduler_1791194611487988000 | 5 | 31.660 | {'gemini': 5} | 2 |
| reliability-followup7-v11-1 | eval_scheduler_1791193956789568000 | 25 | 10.620 | {'gemini': 22, 'gemini_retry': 3} | 0 |
| reliability-followup7-v11-repeat-1 | eval_scheduler_1791194207735357000 | 5 | 11.820 | {'gemini': 5} | 0 |
| reliability-followup7-v11-repeat-2 | eval_scheduler_1791194443117098000 | 5 | 15.960 | {'gemini_retry': 3, 'gemini': 2} | 0 |
| reliability-followup7-v11-repeat-3 | eval_scheduler_1791194683541547000 | 5 | 12.460 | {'gemini': 5} | 0 |

Candidate full mean 10.620 s vs production 19.220 s; repeated mean 13.413 s vs 29.847 s. Candidate 34 primary / 6 retry, zero fallback. All 40 arithmetic/access/intensity-accounting checks are available and True; unavailable advanced readiness stays None. No paired legacy-quality regression. VI ban scan: 245 workouts, zero hits. Manual EN/VI coaching review identified the two explicit failures in manual-findings.json; the automated access score validates declared equipment and therefore does not excuse missing declarations.

Matched metadata-only model cost: $1.826797; 104 logged generation attempts, 104 matched observations, all costs known. Embeddings excluded. See costs.json for per-arm amounts and matching boundaries.

Frozen identity: c0163daca2b588a0d7bc371371955ccdc857e6f5; backend tree 159b808de76c09bea308486391849aa78ffc9d58; production v1, candidate v11. Same model/date/KB. Production v1 and staging v4 unchanged. Provider spending-cap access restored by owner before this batch.

Raw output hashes and privacy filtering are recorded in privacy-filter.json. No references, volume bands, dose policies or athlete-facing format changed.
