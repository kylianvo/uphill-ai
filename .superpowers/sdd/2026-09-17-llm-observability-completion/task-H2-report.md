# Task H2 report — one billable record per model invocation

Date completed: 2026-09-19 (Australia/Sydney)

Baseline: branch `feat/llm-observability`, commit `a274612bc2a07147b5978e59610041ab48e97bc2`. The task was resumed from an existing uncommitted H2 RED/GREEN implementation after its original sandbox could not bind localhost sockets. Existing valid work was preserved and reviewed against the H2 brief and checklist before the focused follow-up below.

## Result

`services.observability.generation(name, *, feature, model, user_id=None, metadata=None)` now represents one explicit provider invocation. It yields a `GenerationRecorder` whose `set_usage(usage, *, known=True)` accepts cumulative usage snapshots. The recorder keeps each token counter monotonic, measures elapsed time with `time.monotonic()`, and emits exactly one Prometheus call/latency/token/cost update when the context exits. Exceptions produce an `error` call; missing, invalid, or explicitly withheld usage increments the bounded-label `llm_unknown_usage_calls_total{feature,status}` metric and does not create zero-cost native usage.

When Langfuse is enabled, the explicit generation owns the native model, usage, and cost detail attributes. A private context-variable invocation identity, authenticated with the existing per-process proof mechanism, is attached to spans by the tracer provider. At the final H1 exporter boundary, nested auto-instrumented spans with that identity retain safe timing and operation fields but lose native model, usage, and cost attribution. The canonical generation keeps those native fields. Invocation identity and proof attributes are removed before transport, unrelated auto-instrumented calls retain their previous attributes, and concurrent threads receive distinct identities.

The existing `Usage`, `cost_usd`, and `record_generation` interfaces remain available. The new internal cost-detail calculation preserves the existing cached-input subtraction and bills output plus thinking tokens at the output rate. Repeated cumulative stream snapshots are consolidated before accounting so stale or duplicate snapshots neither undercount nor double-count.

`LLM_PRICES_JSON` parsing now distinguishes an unset value from a valid explicit `{}`. Malformed or structurally invalid tables log only a fixed, content-free warning and fall back to verified defaults. Rates must be numeric but not boolean, finite, and nonnegative; invalid dates and missing required rates are rejected. The bounded feature vocabularies now include `embeddings` and `evaluation`; no judge accounting was added.

## TDD evidence

The resumed tree contained the original H2 tests and implementation. The handoff records that they were developed with strict RED/GREEN TDD; their raw pre-implementation command output was not stored in the worktree, so this report does not reconstruct or invent it. On takeover, the first fresh non-network H1+H2 run produced `61 passed, 2 deselected`, confirming the inherited state before further edits.

Checklist review found one concrete uncovered requirement: cumulative streaming updates had to be monotonic/idempotent. The existing recorder replaced its prior snapshot, so a late stale snapshot could undercount the invocation.

- RED: `cd backend && .venv/bin/python -m pytest tests/unit/test_observability_metrics.py::test_generation_reports_monotonic_cumulative_stream_usage_once -q` failed because the final stale snapshot recorded 90 input tokens instead of the earlier cumulative 100.
- GREEN: after changing `GenerationRecorder.set_usage` to keep the per-counter maximum, the identical command passed (`1 passed in 0.07s`).
- Final: every non-network observability unit test passed (`73 passed, 2 deselected in 3.94s`).

The H2 coverage includes normal calls, retry attempts, exception paths, cached and thinking usage, missing/withheld usage, cumulative streaming snapshots, zero trace sampling, nested synthetic and real direct-Google-SDK spans, native Langfuse usage/cost fields, unrelated automatic spans, and concurrent invocation identity isolation.

## Pricing verification

Official source: [Google Gemini Developer API pricing](https://ai.google.dev/gemini-api/docs/pricing), accessed 2026-09-19 (Australia/Sydney).

The current standard paid-tier row for `gemini-3.8-flash` matches the repository seed exactly:

- Through 2026-12-31: input $0.75, cached input $0.075, output $3.75 per 1M tokens.
- From 2027-01-01: input $1.50, cached input $0.15, output $7.50 per 1M tokens.
- Google explicitly states that output pricing includes thinking tokens.

Decision: retain the existing default seed values and date windows. No price-table value changed.

## Verification

- All non-network H1+H2 observability units:
  `cd backend && .venv/bin/python -m pytest tests/unit/test_observability_accounting.py tests/unit/test_observability_contract.py tests/unit/test_observability_cost.py tests/unit/test_observability_export_boundary.py tests/unit/test_observability_instrumentation.py tests/unit/test_observability_langfuse.py tests/unit/test_observability_latency.py tests/unit/test_observability_metrics.py tests/unit/test_observability_policy.py -q --deselect tests/unit/test_observability_export_boundary.py::test_real_otlp_transport_serializes_only_sanitized_metadata --deselect tests/unit/test_observability_latency.py::test_unresponsive_exporter_adds_no_request_latency`
  → `73 passed, 2 deselected in 3.94s`.
- `/Users/vietvo/miniconda3/bin/ruff check` over all H2 Python files → passed.
- `/Users/vietvo/miniconda3/bin/ruff format --check` over all H2 Python files → passed after formatting the new accounting test.
- `git diff --check` → passed before commit.

The two deselected existing H1 tests are the only cases that bind a localhost socket: the real OTLP transport serialization test and the unresponsive-exporter latency test. Per the handoff, no socket permission was requested; the unrestricted controller must run those two tests, or the complete observability suite, after this commit.

## Files changed

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
- The two localhost-binding H1 tests remain for the unrestricted controller to execute. Their omission here is environmental, not a claimed pass.
- Feature and model allowlists intentionally fail closed. A future feature or configured model needs an explicit reviewed allowlist and price-table update.
- H2 provides the canonical per-invocation API. Tasks 11–13 remain responsible for wrapping each real provider call and must not also call `record_generation` for the same invocation.
