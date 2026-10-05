# V14 completed paired evaluation

Decision: HOLD. Full vertical-kilometer no-gym case: primary hold timing rejection, retry volume_fit rejection, then rules. First repeat recreational no-gym case: primary unsupported kind/setting, retry volume_fit rejection, then rules with unavailable access. The rejected drafts were not retained; specific malformed fields/quantities are unknown. All original results and scores remain retained.

| Arm | Run | Cases | Mean seconds | Engines | Failures |
|---|---|---:|---:|---|---:|
| reliability-followup11-production-1 | eval_scheduler_1791210182527713000 | 25 | 29.860 | {'gemini': 23, 'gemini_retry': 2} | 2 |
| reliability-followup11-production-repeat-1 | eval_scheduler_1791210768814478000 | 5 | 32.000 | {'gemini': 5} | 2 |
| reliability-followup11-production-repeat-2 | eval_scheduler_1791211006178852000 | 5 | 30.840 | {'gemini': 5} | 0 |
| reliability-followup11-production-repeat-3 | eval_scheduler_1791211268556069000 | 5 | 33.940 | {'gemini': 5} | 0 |
| reliability-followup11-v14-1 | eval_scheduler_1791210575599595000 | 25 | 14.256 | {'gemini': 20, 'gemini_retry': 4, 'rule-based-or-unknown': 1} | 1 |
| reliability-followup11-v14-repeat-1 | eval_scheduler_1791210841037384000 | 5 | 12.380 | {'gemini': 4, 'rule-based-or-unknown': 1} | 2 |
| reliability-followup11-v14-repeat-2 | eval_scheduler_1791211089282914000 | 5 | 14.720 | {'gemini': 5} | 0 |
| reliability-followup11-v14-repeat-3 | eval_scheduler_1791211346740322000 | 5 | 13.560 | {'gemini': 5} | 0 |

Known metadata-only model cost: $1.787677, 106 logged attempts, 2 observation costs unavailable; embeddings excluded. The earlier disk-interrupted baseline's $0.154222 is separate and excluded from this paired gate. Same frozen code/backend/model/date/KB across all eight arms; identities and raw hashes retained. Production v1/staging v4 unchanged. No manual/UI acceptance is claimed for V14.

Next correction: give the existing validation retry the rejected draft as explicitly delimited untrusted data, captured before normalization. Request minimal repair and validate the entire returned block. Keep data local, never exception/log/span metadata; parse/transport retries remain unchanged. No extra attempts, scaling, fixture/check relaxation, new dose or format change. Review approved the design; code/tests require review and a fresh full gate for V15. See review.json for paired legacy and VI scans.
