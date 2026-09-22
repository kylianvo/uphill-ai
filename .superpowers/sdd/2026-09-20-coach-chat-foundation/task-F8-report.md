# Task F8 Report: Own turn lifecycle, partial persistence, recovery and summaries

## Summary
Task F8 implements turn execution lifecycle ownership, PostgreSQL session locking, quota admission, partial stream persistence, recovery, and post-turn thread summary CAS updates in `backend/services/coach_chat.py` and `backend/db.py`. Comprehensive integration tests are added in `backend/tests/integration/test_chat_turn_lifecycle.py`.

## Components & Contracts Implemented
1. **Thread Summary CAS (`db.py`)**:
   - `update_chat_thread_summary_cas(thread_id, user_id, new_summary, new_summarized_through_id, expected_summarized_through_id)`:
     - Compare-and-swap mechanism ensuring summaries are updated atomically and never overwrite newer or cleared thread states.
2. **Turn Execution Runner (`run_turn` in `services/coach_chat.py`)**:
   - Acquires PostgreSQL session advisory lock via `chat_turn_lock(user_id)`.
   - Resolves thread via `get_or_create_chat_thread(user_id)`.
   - Admits turn via `admit_chat_turn(request_id, user_id, thread_id, message, retry_of)`.
   - Replay short-circuit: immediately returns persisted message tokens, citations, and `DoneEvent(replayed=True)` without calling the provider or reserving new quotas.
   - Initial assistant message creation: appends assistant row with `status="active"`.
   - Bounded execution (45s deadline): runs `astream_turn_graph` under `COACH_CHAT_TURN_TIMEOUT_SECONDS`.
   - Throttled partial persistence: writes accumulated reply text to `chat_messages` every 1 second or 256 new characters.
   - Clean finalization: persists final text and citations, updates turn to `status="ok"`, and emits `DoneEvent`. If DB finalization fails, `DoneEvent` is never emitted.
   - Resilient error handling: on cancellation, timeout, or upstream failure, preserves exact partial text in `chat_messages` with `status="interrupted"` or `"error"` without fabricating replacement text.
   - Bounded post-turn summary: under 10-second cap, summarizes thread messages and CAS-updates `chat_threads`. Summary failure is isolated and does not fail the primary coaching turn.
3. **Integration Test Suite (`tests/integration/test_chat_turn_lifecycle.py`)**:
   - `test_turn_lifecycle_success_stream`: Validates end-to-end token delivery, message persistence, turn status update, and `DoneEvent`.
   - `test_turn_lifecycle_error_preserves_partial`: Validates that upstream errors preserve partial text in DB with `status="error"` and emit `ErrorEvent` without `DoneEvent`.
   - `test_turn_lifecycle_replay_does_not_call_model`: Validates that repeated request IDs replay stored answers with `replayed=True` without calling model stream.
   - `test_turn_lifecycle_conflict`: Validates `ChatRequestConflictError` when the same request ID is submitted with different input.
   - `test_turn_lifecycle_db_finalization_failure_emits_no_done`: Validates that database failures during finalization prevent `DoneEvent` emission.

## Files Touched
- Modified: `backend/db.py`
- Modified: `backend/services/coach_chat.py`
- Created: `backend/tests/integration/test_chat_turn_lifecycle.py`
- Created: `.superpowers/sdd/2026-09-20-coach-chat-foundation/task-F8-brief.md`
- Created: `.superpowers/sdd/2026-09-20-coach-chat-foundation/task-F8-report.md`
