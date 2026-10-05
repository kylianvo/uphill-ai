# V12 completed paired evaluation

Decision: HOLD. The full candidate run falls back to rules for the Vietnamese 42 km fixture after primary and retry both fail volume_fit. All repeats pass, but they do not erase that failure. The original error did not record the rejected distance, so whether it was under or over the band is unknown.

| Arm | Run | Cases | Mean seconds | Engines | Failures |
|---|---|---:|---:|---|---:|
| reliability-followup8-production-1 | eval_scheduler_1791195561288411000 | 25 | 18.792 | {'gemini': 25} | 2 |
| reliability-followup8-production-repeat-1 | eval_scheduler_1791196062705584000 | 5 | 31.160 | {'gemini': 5} | 0 |
| reliability-followup8-production-repeat-2 | eval_scheduler_1791196281614000000 | 5 | 27.560 | {'gemini': 5} | 0 |
| reliability-followup8-production-repeat-3 | eval_scheduler_1791196518271796000 | 5 | 29.080 | {'gemini': 5} | 0 |
| reliability-followup8-v12-1 | eval_scheduler_1791195873038209000 | 25 | 11.092 | {'gemini': 21, 'gemini_retry': 3, 'rule-based-or-unknown': 1} | 1 |
| reliability-followup8-v12-repeat-1 | eval_scheduler_1791196132428105000 | 5 | 12.060 | {'gemini': 5} | 0 |
| reliability-followup8-v12-repeat-2 | eval_scheduler_1791196362028619000 | 5 | 14.100 | {'gemini': 5} | 0 |
| reliability-followup8-v12-repeat-3 | eval_scheduler_1791196597653736000 | 5 | 13.500 | {'gemini': 5} | 0 |

Candidate: 36 primary / 3 retry / 1 rules across 40 cases. Full mean 11.092 s vs production 18.792 s; repeated mean 13.220 s vs 29.267 s. All 40 arithmetic/access/intensity-accounting checks are available and True; advanced readiness remains unavailable. No paired legacy regression. VI ban scan: 245 workouts, zero hits. Manual review found no additional concrete-movement/access blocker; fallback remains a release blocker.

Matched metadata-only model cost: $1.790376, 102 logged attempts matched to 102 observations, all costs known; embeddings excluded. Frozen code 40c169b54395f0199e8831f32ebe50eefeb5dddd, backend tree 3e041e5b432bd0ab55eee7feb7f4594c530b874a. Prompt v12; production v1 and staging v4 unchanged. Same model, fixed as-of date and KB as identity.json.

The next correction supplies the existing bounded retry with actual resolved distance and the unchanged allowed band. Loggable errors stay generic; quantities stay in local model feedback. No scaling, fixture relaxation, new training dose, public workout-format change or deployment. V13 requires a fresh full paired gate. Raw output hashes and zero privacy replacements are recorded in privacy-filter.json.
