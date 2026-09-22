# Task F4 Brief: Persist exactly-once call accounting

## Objective
Implement durable, exactly-once LLM call accounting (`chat_llm_calls`) and turn aggregation (`chat_turn_totals`) in `backend/db.py` and call lifecycle orchestration in `backend/services/coach_chat.py`. Consumes `services.observability` (`Usage`, `cost_usd`, `generation()`) without importing Langfuse outside `observability.py`.

## File Targets
- Modify: `backend/db.py`
- Modify: `backend/services/coach_model.py`
- Create: `backend/services/coach_chat.py`
- Create: `backend/tests/integration/test_chat_accounting.py`
- Report: `.superpowers/sdd/2026-09-20-coach-chat-foundation/task-F4-report.md`

## Specifications
1. **Durable Call Reservation & Completion**:
   - `reserve_chat_call(call_id: UUID, request_id: UUID, feature: str, model: str) -> None`:
     Inserts pending call with `status='reserved'`, `usage_known=False`, 0 tokens, and NULL cost.
   - `finish_chat_call(call_id: UUID, status: str, usage_known: bool, input_tokens: int, output_tokens: int, thinking_tokens: int, cached_tokens: int, cost_usd: Decimal | float | None, latency_ms: int | None) -> bool`:
     Pending-to-terminal conditional update (`WHERE call_id = :cid AND status = 'reserved'`).
     Only the first transition updates the row; subsequent calls return False.
   - `chat_turn_totals(request_id: UUID) -> dict[str, Any]`:
     Aggregates `total_calls`, `total_input_tokens`, `total_output_tokens`, `total_thinking_tokens`, `total_cached_tokens`, `total_cost_usd`, and boolean `usage_known` across all calls for a given turn.

2. **Call Tracking Orchestrator in `services/coach_chat.py`**:
   - `track_chat_call(call_id: UUID, request_id: UUID, feature: str, model_adapter: CoachModel, model_request: ModelRequest) -> AsyncIterator[ModelEvent]`:
     Reserves call row before calling model.
     Iterates model events, captures usage and latency.
     In `finally`, transitions call row conditionally to terminal status with computed `cost_usd` from `observability.cost_usd(model, usage)`.
     If stream is cancelled or terminates without usage, marks status="interrupted" / "error" with `usage_known=False`.

3. **Privacy & Observability Constraints**:
   - Never use athlete IDs in Prometheus labels.
   - No athlete content or prompts stored in `chat_llm_calls`.
   - Never import Langfuse or OpenTelemetry outside `services/observability.py`.
