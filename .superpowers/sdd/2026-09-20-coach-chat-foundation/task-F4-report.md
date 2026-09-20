# Task F4 Report: Persist exactly-once call accounting

## Summary
Task F4 implements durable exactly-once LLM call accounting (`chat_llm_calls`) and multi-call turn aggregation (`chat_turn_totals`) in `backend/db.py`, as well as call tracking orchestration in `backend/services/coach_chat.py`. It integrates with `services.observability` (`Usage`, `cost_usd`, `generation()`) while strictly respecting the privacy/observability boundaries (no Langfuse or OpenTelemetry imports outside `services/observability.py`, no athlete IDs in Prometheus labels, and no athlete prompt content stored in accounting tables).

## Components & Contracts Implemented
1. **Durable Call Accounting**:
   - `reserve_chat_call(call_id, request_id, feature, model)`: Inserts a pending call row with `status='reserved'`, `usage_known=False`, and zero tokens.
   - `finish_chat_call(call_id, status, usage_known, input_tokens, output_tokens, thinking_tokens, cached_tokens, cost_usd, latency_ms)`: Executes a pending-to-terminal conditional update (`WHERE call_id = :cid AND status = 'reserved'`). Exactly-once transition guarantee: only the first completion succeeds; subsequent calls return False.
   - `chat_turn_totals(request_id)`: Aggregates `total_calls`, `total_input_tokens`, `total_output_tokens`, `total_thinking_tokens`, `total_cached_tokens`, `total_cost_usd`, and boolean `usage_known` across all calls for a given turn.
2. **Call Tracking Orchestration (`services/coach_chat.py`)**:
   - `track_chat_call(call_id, request_id, feature, model_name, model_adapter, model_request)`:
     - Reserves call row prior to invoking model adapter.
     - Times execution latency.
     - Extracts model usage events.
     - In `finally`, calculates exact USD cost via `observability.cost_usd(model_name, usage)` and conditionally transitions call row to terminal status.
     - Preserves `usage_known=False` for interrupted or failed streams.
3. **Integration Verification (`tests/integration/test_chat_accounting.py`)**:
   - `test_finish_chat_call_conditional_transition`: Verifies exactly-once update semantics.
   - `test_retry_call_accounting_isolation`: Verifies separate accounting between root and retry turns.
   - `test_turn_totals_multi_call_aggregation`: Verifies summation across multiple distinct calls (retrieval, generation, summary) in a single turn.
   - `test_interrupted_call_usage_unknown`: Verifies unknown-usage flags on interrupted calls.
   - `test_track_chat_call_lifecycle_orchestration`: Verifies end-to-end lifecycle from reservation to completion.

## Files Touched
- Modified: `backend/db.py`
- Created: `backend/services/coach_chat.py`
- Created: `backend/tests/integration/test_chat_accounting.py`
- Created: `.superpowers/sdd/2026-09-20-coach-chat-foundation/task-F4-brief.md`
- Created: `.superpowers/sdd/2026-09-20-coach-chat-foundation/task-F4-report.md`
