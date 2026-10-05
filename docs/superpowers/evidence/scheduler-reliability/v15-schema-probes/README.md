# Structured-output diagnostic probes

Decision: HOLD. These14 synthetic diagnostic requests are not release evaluations. Exact production-v1 beginner prompt, model, code, as-of date and six retrieved KB chunks are held fixed; promptSHAe08da79235f484d0a3b0bfac80d9ee54fdffc87a2b621112ad1b2f6164d82577. Schema/mime mode varies by arm, with reverse-order repeats. Diagnostic deadlines are30seconds; the actual generator's120-second deadline is unchanged. Metadata-only export, explicit --push-langfuse --synthetic-only. Generated responses are retained locally after privacy filtering; never exported.

| Arm | Repeat | Outcome | Seconds | Workout rows |
|---|---:|---|---:|---:|
| no_schema | 1 | response | 10.601 | 7 |
| flat_legacy | 1 | ServerError | 29.749 | — |
| nested_legacy | 1 | TimeoutError | 30.468 | — |
| nested_legacy | 2 | response | 2.306 | 1 |
| flat_legacy | 2 | response | 2.339 | 1 |
| no_schema | 2 | response | 9.104 | 7 |
| json_mime_only | 1 | response | 12.202 | 7 |
| typed_flat | 1 | response | 2.649 | 1 |
| typed_nested | 1 | response | 2.681 | 1 |
| raw_flat_min7 | 1 | ServerError | 29.779 | — |
| raw_flat_min7 | 2 | response | 6.883 | 7 |
| typed_nested | 2 | response | 2.786 | 1 |
| typed_flat | 2 | ServerError | 29.720 | — |
| json_mime_only | 2 | response | 15.139 | 7 |

Known model cost$0.091231; 14 matching generations, 4 unknown observation costs, 0 unmatched attempts. Setup embeddings excluded. No_schema and JSON MIME-only responses each include seven rows. Fast raw/typed schemas with minItems1 return only one row, violating the requested full block. Raw flat minItems7 produces one seven-day response and one504deadline failure. Timeouts, errors and incomplete replies remain retained; their underlying provider cause is not established. A faster incomplete reply is not a quality/latency improvement.

Next proposed correction: keep the legacy schema scalar; derive provider minimum row count from existing block/date coverage; locally reject missing or unexpected calendar days, preserving legitimate double sessions and first-week exclusions. Enforce the existing complete-block contract without inventing training load. Final independent review of that proposal was interrupted by reviewer usage limits; no implementation/release approval claimed. A fresh full paired gate and manual/UI acceptance remain required.

Cost matching uses canonical model/development observations within two seconds of owned probe starts. The API returned unavailable trace names for these custom-root traces; no other paid requests ran during the probes. Empty-model instrumentation observations are excluded.
