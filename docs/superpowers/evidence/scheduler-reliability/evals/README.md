# Paired scheduler reliability results

Decision: **HOLD**. Both allowed candidates fail. No further candidate, staging deploy or environment-label promotion is authorized by this result.

Metrics v2, fixed date 2026-10-05, model gemini-3.8-flash. Full suite = 25 cases; repeats = four urban Vietnam cases plus healthy sequential blocker, three runs per arm. All pushes synthetic-only. References were not recaptured.

| Arm | Cases | Mean latency s | Primary / retry / fallback cases | Reported gate failures | Paired legacy regressions | VI wording violations | Cost USD |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| reliability-candidate-1 | 25 | 20.948 | 16 / 7 / 2 | 5 | 4 | 4 | 0.857275 |
| reliability-candidate-repeat-1 | 5 | 25.180 | 4 / 1 / 0 | 0 | 0 | 2 | 0.198703 |
| reliability-candidate-repeat-2 | 5 | 25.600 | 4 / 1 / 0 | 0 | 0 | 3 | 0.191766 |
| reliability-candidate-repeat-3 | 5 | 29.660 | 3 / 2 / 0 | 0 | 0 | 3 | 0.217600 |
| reliability-production-1 | 25 | 17.152 | 25 / 0 / 0 | 2 | baseline | 20 | 0.561512 |
| reliability-production-repeat-1 | 5 | 30.740 | 5 / 0 / 0 | 2 | baseline | 6 | 0.170836 |
| reliability-production-repeat-2 | 5 | 30.940 | 5 / 0 / 0 | 1 | baseline | 9 | 0.158453 |
| reliability-production-repeat-3 | 5 | 26.120 | 5 / 0 / 0 | 1 | baseline | 18 | 0.135558 |
| reliability-refinement-1 | 25 | 12.912 | 24 / 0 / 1 | 3 | 0 | 0 | 0.566841 |
| reliability-refinement-repeat-1 | 5 | 19.260 | 4 / 1 / 0 | 0 | 0 | 0 | 0.158611 |
| reliability-refinement-repeat-2 | 5 | 17.320 | 5 / 0 / 0 | 0 | 0 | 0 | 0.131797 |
| reliability-refinement-repeat-3 | 5 | 18.560 | 5 / 0 / 0 | 0 | 0 | 0 | 0.130077 |

Latency comparison:

- candidate, full: 20.948 vs 17.152 s; +22.13% (limit +20%).
- candidate, repeat: 26.813 vs 29.267 s; -8.38% (limit +20%).
- refinement, full: 12.912 vs 17.152 s; -24.72% (limit +20%).
- refinement, repeat: 18.380 vs 29.267 s; -37.20% (limit +20%).

Run identities ([Langfuse dataset `uphill_scheduler_golden`](https://cloud.langfuse.com/project/cmu6scbt0004gad0c9z4e9kmx/datasets/cmunujh7n00omad0c2w0kxohy)):

- `reliability-candidate-1` → `eval_scheduler_1791105181774260000` ([results](reliability-candidate-1/results.json), [report](reliability-candidate-1/report_scheduler.md)).
- `reliability-candidate-repeat-1` → `eval_scheduler_1791105944540430000` ([results](reliability-candidate-repeat-1/results.json), [report](reliability-candidate-repeat-1/report_scheduler.md)).
- `reliability-candidate-repeat-2` → `eval_scheduler_1791106080890444000` ([results](reliability-candidate-repeat-2/results.json), [report](reliability-candidate-repeat-2/report_scheduler.md)).
- `reliability-candidate-repeat-3` → `eval_scheduler_1791106237639172000` ([results](reliability-candidate-repeat-3/results.json), [report](reliability-candidate-repeat-3/report_scheduler.md)).
- `reliability-production-1` → `eval_scheduler_1791055948650762000` ([results](reliability-production-1/results.json), [report](reliability-production-1/report_scheduler.md)).
- `reliability-production-repeat-1` → `eval_scheduler_1791105428512507000` ([results](reliability-production-repeat-1/results.json), [report](reliability-production-repeat-1/report_scheduler.md)).
- `reliability-production-repeat-2` → `eval_scheduler_1791105590895352000` ([results](reliability-production-repeat-2/results.json), [report](reliability-production-repeat-2/report_scheduler.md)).
- `reliability-production-repeat-3` → `eval_scheduler_1791105730909093000` ([results](reliability-production-repeat-3/results.json), [report](reliability-production-repeat-3/report_scheduler.md)).
- `reliability-refinement-1` → `eval_scheduler_1791106644091611000` ([results](reliability-refinement-1/results.json), [report](reliability-refinement-1/report_scheduler.md)).
- `reliability-refinement-repeat-1` → `eval_scheduler_1791106819554970000` ([results](reliability-refinement-repeat-1/results.json), [report](reliability-refinement-repeat-1/report_scheduler.md)).
- `reliability-refinement-repeat-2` → `eval_scheduler_1791106914360079000` ([results](reliability-refinement-repeat-2/results.json), [report](reliability-refinement-repeat-2/report_scheduler.md)).
- `reliability-refinement-repeat-3` → `eval_scheduler_1791107018485201000` ([results](reliability-refinement-repeat-3/results.json), [report](reliability-refinement-repeat-3/report_scheduler.md)).

All reported failures, retained verbatim:

- reliability-candidate-1: scheduler_fixture_elite_utmb: fell through to the rule-based-or-unknown tier
- reliability-candidate-1: scheduler_fixture_elite_utmb: access failed or unavailable
- reliability-candidate-1: scheduler_fixture_snapshot_elite_unmeasured_thresholds: fell through to the rule-based-or-unknown tier
- reliability-candidate-1: scheduler_fixture_snapshot_elite_unmeasured_thresholds: access failed or unavailable
- reliability-candidate-1: scheduler_fixture_snapshot_elite_unmeasured_thresholds: week-2 volume 174.5 km outside the expected range
- reliability-production-1: scheduler_sequence_unknown_override: week-2 volume 96.4 km outside the expected range
- reliability-production-1: scheduler_fixture_snapshot_elite_unmeasured_thresholds: week-2 volume 108.6 km outside the expected range
- reliability-production-repeat-1: scheduler_fixture_vietnam_urban_recreational_no_gym: week-2 volume 74.7 km outside the expected range
- reliability-production-repeat-1: scheduler_fixture_vietnam_urban_sub_elite_treadmill: week-2 volume 89.4 km outside the expected range
- reliability-production-repeat-2: scheduler_fixture_vietnam_urban_sub_elite_treadmill: week-2 volume 88.6 km outside the expected range
- reliability-production-repeat-3: scheduler_fixture_vietnam_urban_sub_elite_no_gym: week-2 volume 119.5 km outside the expected range
- reliability-refinement-1: scheduler_sequence_fatigue: recovery intensity failed or unavailable
- reliability-refinement-1: scheduler_sequence_recovery: fell through to the rule-based-or-unknown tier
- reliability-refinement-1: scheduler_fixture_snapshot_recreational_field_thresholds: week-2 volume 79.8 km outside the expected range

Interpretation and limitations:

- V5 full-suite latency exceeds the unchanged limit; four old easy-share scores regress. Repeated successes do not erase fallback, volume or VI failures.
- V6 resolves the observed schema errors and has no full-suite legacy score regression or banned VI wording. Manual review still finds unnatural VI titles (including Tiến Lực and Tái Nạp ATP) and advanced hill/power work without documented preparation; copy/coaching acceptance fails despite a clean ban scan. Its recovery sequence rejects inaccessible prescriptions on both attempts, then falls back. The fatigue sequence adds Zone 5 strides despite the explicit maximum Zone 2 adaptation. Snapshot recreational field-threshold volume is 79.8 km, below the unchanged band. These defects keep HOLD regardless of faster latency.
- Production v1 has no segment precision: arithmetic, access, intensity-accounting and progression are unavailable, never counted as passes. Candidate progression remains unavailable for noncomparable weeks. Detailed counts, component minutes and locomotion-time/distance shares are in results/diagnostics; no new long-run percentage gate was introduced.
- Costs are actual Langfuse recorded plan-generation costs, including retries, filtered by model/feature/development environment and exact sequential log windows. Blank-model wrapper observations are excluded. No embedding cost is included, and no zero-cost claim is made for embeddings. Recorded generation counts match model-attempt logs.
- VI ban scan is paired with manual review of all v6 VI titles/rationale and deterministic instructions: quantities, units, estimates and stop conditions derive from the same segments. Screenshots demonstrate EN/VI parity for seeded accounting examples; independently generated EN translations of every VI plan were not requested. Title-level wording and unverified physiological claims remain unacceptable; a clean numeric translation does not establish overall meaning/source parity. Historical and v5 failures remain unedited in evidence.
- Source coverage: continuity/readiness tested with six sequences; flat/gym/day access with four Vietnam cases; component geometry/accounting and stop conditions by exact unit tests. ME order and preparation follow inspected author supplements, not a new universal dosage. Existing intensity/growth and long-run caps remain explicitly app policy; disputed attribution is deferred. No seed sweep/import.
- UI and persistence evidence are distinct: seven local screenshots, exact synthetic cleanup, frontend checks passed. No integration truncations or staging smoke in this phase. Production/staging labels remain v1/v4. Local plan fallback remains v5; v6 is experimental only, and requires a deliberate sync before any later promotion.

Total recorded model generation cost across these runs: **$3.479029**.

Langfuse read verification: all 12 run names exist in the retained dataset run metadata. Detailed deprecated run reads return HTTP 410; replacement experiment listing returns no rows for these legacy-SDK runs. Push acceptance and dataset membership are verified, but replacement-API item retrieval is unavailable. Preserve local results as the complete review record. Migrating experiment ingestion is a separate follow-up; no dependency or observability change was made to work around it.
