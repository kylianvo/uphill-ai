# Task H2 report — one billable record per model invocation

Date completed: 2026-09-19 (Australia/Sydney)

Original H2 baseline: branch `feat/llm-observability`, commit `a274612bc2a07147b5978e59610041ab48e97bc2`. The task was resumed from an existing uncommitted H2 RED/GREEN implementation after its original sandbox could not bind localhost sockets. Existing valid work was preserved and reviewed against the H2 brief and checklist before the focused follow-up below.

Fix-round-1 baseline: `dbccc13f7441f9604f53cab04722409839cd8560` on `feat/llm-observability`.

## Result

`services.observability.generation(name, *, feature, model, user_id=None, metadata=None)` now represents one explicit provider invocation. It yields a `GenerationRecorder` whose `set_usage(usage, *, known=True)` accepts cumulative usage snapshots. The recorder keeps each token counter monotonic, measures elapsed time with `time.monotonic()`, and emits exactly one Prometheus call/latency/token/cost update when the context exits. Exceptions produce an `error` call; missing, invalid, or explicitly withheld usage increments the bounded-label `llm_unknown_usage_calls_total{feature,status}` metric and does not create zero-cost native usage.

When Langfuse is enabled, the explicit generation owns the native model, usage, and cost detail attributes. A private context-variable invocation identity, authenticated with the existing per-process proof mechanism, is attached to spans by the tracer provider. At the final H1 exporter boundary, nested auto-instrumented spans with that identity retain safe timing and operation fields but lose native model, usage, and cost attribution. The canonical generation keeps those native fields. Invocation identity and proof attributes are removed before transport, unrelated auto-instrumented calls retain their previous attributes, and concurrent threads receive distinct identities.

The existing `Usage`, `cost_usd`, and `record_generation` interfaces remain available. The new internal cost-detail calculation preserves the existing cached-input subtraction and bills output plus thinking tokens at the output rate. Repeated cumulative stream snapshots are consolidated before accounting so stale or duplicate snapshots neither undercount nor double-count.

Fix round 1 corrected the native Langfuse usage buckets to the pinned SDK's mutually exclusive convention: `input` is uncached prompt input, `cached_input` is cached prompt input, `output` is candidate output, and `output_reasoning` is thinking output. `total` is the sum of those four buckets and therefore remains equal to the provider total without double-counting cached input. The canonical Langfuse generation still exports the full allowlisted model name.

Prometheus model labels now use the explicit finite vocabulary `gemini-3.8-flash` plus `other`. This normalization applies to calls, tokens, latency, cost, and unpriced calls; arbitrary configured or provider-returned model strings therefore cannot create new metric series. Pricing still uses the full model string before label normalization, so a configured price entry continues to calculate the right cost even when its metric label is `other`.

The public `record_generation` status parameter now uses a closed compatibility vocabulary: `ok`, `error`, `attempt`, `success`, `used`, and `fallback`; every other value maps to `other`. Repository history established `error` on `record_generation` itself and `attempt`/`success`/`error`/`used` in the adjacent generation-attempt telemetry. `fallback` is retained as the existing fallback telemetry concept. Unknown and error-like strings are never silently reported as `ok`, and invalid runtime values cannot escape the metrics safety boundary.

Price-table validation now treats both date boundaries as inclusive, models omitted `from`/`until` values as negative/positive infinity, rejects an individual window whose start is after its end, and rejects sorted windows whose inclusive intervals overlap. Consecutive windows ending on one day and starting the next remain valid; a single fully open window remains valid; `{}` remains an intentional empty override.

`LLM_PRICES_JSON` parsing now distinguishes an unset value from a valid explicit `{}`. Malformed or structurally invalid tables log only a fixed, content-free warning and fall back to verified defaults. Rates must be numeric but not boolean, finite, and nonnegative; invalid dates and missing required rates are rejected. The bounded feature vocabularies now include `embeddings` and `evaluation`; no judge accounting was added.

## TDD evidence

The resumed tree contained the original H2 tests and implementation. The handoff records that they were developed with strict RED/GREEN TDD; their raw pre-implementation command output was not stored in the worktree, so this report does not reconstruct or invent it. On takeover, the first fresh non-network H1+H2 run produced `61 passed, 2 deselected`, confirming the inherited state before further edits.

Checklist review found one concrete uncovered requirement: cumulative streaming updates had to be monotonic/idempotent. The existing recorder replaced its prior snapshot, so a late stale snapshot could undercount the invocation.

- RED: `cd backend && .venv/bin/python -m pytest tests/unit/test_observability_metrics.py::test_generation_reports_monotonic_cumulative_stream_usage_once -q` failed because the final stale snapshot recorded 90 input tokens instead of the earlier cumulative 100.
- GREEN: after changing `GenerationRecorder.set_usage` to keep the per-counter maximum, the identical command passed (`1 passed in 0.07s`).
- Final: every non-network observability unit test passed (`73 passed, 2 deselected in 3.94s`).

The H2 coverage includes normal calls, retry attempts, exception paths, cached and thinking usage, missing/withheld usage, cumulative streaming snapshots, zero trace sampling, nested synthetic and real direct-Google-SDK spans, native Langfuse usage/cost fields, unrelated automatic spans, and concurrent invocation identity isolation.

### Fix round 1 RED/GREEN evidence

The four review findings were replayed independently against the pre-fix behavior. Production mutations used for the RED checks were reverted immediately after each expected failure.

- Native usage buckets:
  - SDK inspection: pinned Langfuse `4.15.3` flattens output detail key `reasoning` to `output_reasoning` and subtracts detail values from the parent `output` bucket. Its legacy usage schema documents `total` as defaulting to `input + output`. Pinned OpenInference Google GenAI `1.4.7` reports prompt tokens with cached tokens included, completion as candidates plus thoughts, and reasoning as a completion detail.
  - RED: `backend/.venv/bin/python -m pytest backend/tests/unit/test_observability_accounting.py::test_generation_exports_native_usage_and_cost_on_canonical_child_only -q` failed because the export contained `thinking_tokens` instead of the pinned `output_reasoning` key (`1 failed`). After renaming the production key alone, the test still failed because the default-deny export policy rejected it, proving the policy boundary also needed the schema update.
  - GREEN: after updating both the usage builder and export-policy allowlist, the identical command passed (`1 passed`). The expected provider total is calculated independently from the fixture, and both the native `total` and the sum of mutually exclusive exported buckets must equal it.
- Bounded model labels:
  - RED: with raw model labels temporarily restored, `test_arbitrary_models_share_bounded_other_metric_labels` and `test_unpriced_model_counts_as_unpriced_and_adds_no_cost` both failed because neither arbitrary priced models nor an arbitrary unpriced model incremented the bounded `other` series (`2 failed`).
  - GREEN: restoring the explicit vocabulary and `other` fallback made the identical two-test command pass (`2 passed`). The regression checks calls, tokens, latency, cost, and unpriced metrics and confirms no raw arbitrary-model series exist.
- Status compatibility:
  - RED: with the previous `error`-else-`ok` coercion restored, the compatibility/unknown-status command produced `5 failed, 1 passed`: `attempt`, `success`, `used`, and `fallback` were collapsed to `ok`, and an unknown error-like value failed to reach `other`.
  - GREEN: the closed compatibility vocabulary made that command pass (`6 passed`). A subsequent test-first extension for empty, null, and non-string values produced the expected RED (`1 failed, 3 passed`) because an unhashable list raised `TypeError`; the `isinstance(status, str)` guard then made the full status regression pass (`9 passed`).
- Pricing windows:
  - RED: with the old syntax-only date validation restored, the adjacent/inverted/overlap command produced `4 failed, 1 passed`; all invalid interval arrangements were accepted.
  - GREEN: after inclusive interval validation was restored, the complete cost test module passed (`17 passed`). This includes adjacent valid windows, inverted and overlapping intervals (including open-ended cases), malformed/invalid rates and boundaries inherited from H2, and the valid `{}` override.

The first combined affected-suite run after these cycles passed: `60 passed in 0.97s` across accounting, cost, metrics, and policy tests.

## Pricing verification

Official source: [Google Gemini Developer API pricing](https://ai.google.dev/gemini-api/docs/pricing), accessed 2026-09-19 (Australia/Sydney).

The current standard paid-tier row for `gemini-3.8-flash` matches the repository seed exactly:

- Through 2026-12-31: input $0.75, cached input $0.075, output $3.75 per 1M tokens.
- From 2027-01-01: input $1.50, cached input $0.15, output $7.50 per 1M tokens.
- Google explicitly states that output pricing includes thinking tokens.

Decision: retain the existing default seed values and date windows. No price-table value changed.

## Verification

- Full H1+H2 observability suite, including the real localhost OTLP transport and unresponsive-exporter latency tests:
  `backend/.venv/bin/python -m pytest backend/tests/unit/test_observability_accounting.py backend/tests/unit/test_observability_contract.py backend/tests/unit/test_observability_cost.py backend/tests/unit/test_observability_export_boundary.py backend/tests/unit/test_observability_instrumentation.py backend/tests/unit/test_observability_langfuse.py backend/tests/unit/test_observability_latency.py backend/tests/unit/test_observability_metrics.py backend/tests/unit/test_observability_policy.py -q`
  → `90 passed in 5.00s`.
- `/Users/vietvo/miniconda3/bin/ruff check` over all H2 Python files → `All checks passed!`.
- `/Users/vietvo/miniconda3/bin/ruff format --check` over all H2 Python files → `8 files already formatted`.
- `git diff --check` → passed immediately before commit.

## Files changed

Fix round 1 changed:

- `backend/config.py`
- `backend/services/observability.py`
- `backend/services/observability_policy.py`
- `backend/tests/unit/test_observability_accounting.py`
- `backend/tests/unit/test_observability_cost.py`
- `backend/tests/unit/test_observability_metrics.py`
- `.superpowers/sdd/2026-09-17-llm-observability-completion/task-H2-report.md` (this report)

The complete H2 task changed:

- `backend/config.py`
- `backend/services/observability.py`
- `backend/services/observability_policy.py`
- `backend/telemetry.py`
- `backend/tests/unit/test_observability_accounting.py` (new)
- `backend/tests/unit/test_observability_cost.py`
- `backend/tests/unit/test_observability_metrics.py`
- `backend/tests/unit/test_observability_policy.py`
- `.superpowers/sdd/2026-09-17-llm-observability-completion/task-H2-report.md` (this report)

No prompts, production call sites, coach copilot, week review, schemas, frontend, dependencies, or user-owned untracked files were changed.

## Remaining concerns and later gates

- Foundation F6 must run the real `ChatGoogleGenerativeAI` plus Google GenAI nested-instrumentation canary as an H3 release gate. H2 intentionally did not install LangChain/ChatGoogleGenerativeAI dependencies; its direct SDK and synthetic nested-span tests establish the current boundary without expanding dependencies.
- Feature and model allowlists intentionally fail closed. A future feature or configured model needs an explicit reviewed allowlist and price-table update.
- H2 provides the canonical per-invocation API. Tasks 11–13 remain responsible for wrapping each real provider call and must not also call `record_generation` for the same invocation.
