# Task F8 Brief: Own turn lifecycle, partial persistence, recovery and summaries

## Objective
Implement complete turn lifecycle management in `backend/services/coach_chat.py` and thread summary CAS helpers in `backend/db.py`. Expose `run_turn(user, request) -> AsyncIterator[AppEvent]` with session advisory locking, quota admission, bounded graph execution (45s deadline), 1s / 256-char partial message persistence, clean error/cancellation preservation, atomic turn completion, and 10s capped post-turn summary updates. Verify with integration tests in `backend/tests/integration/test_chat_turn_lifecycle.py`.

## File Targets
- Modify: `backend/db.py`
- Modify: `backend/services/coach_chat.py`
- Create: `backend/tests/integration/test_chat_turn_lifecycle.py`
- Report: `.superpowers/sdd/2026-09-20-coach-chat-foundation/task-F8-report.md`

## Specifications
1. **Thread Summary CAS Helper (`backend/db.py`)**:
   - `update_chat_thread_summary_cas(thread_id, user_id, new_summary, new_summarized_through_id, expected_summarized_through_id) -> bool`:
     - Compares and swaps `summarized_through_id` and updates summary.
     - Prevents stale summary tasks from overwriting newer or cleared threads.
2. **Turn Execution Runner (`run_turn` in `coach_chat.py`)**:
   - Acquires PostgreSQL session advisory lock (`chat_turn_lock(user_id)`).
   - Resolves thread via `get_or_create_chat_thread(user_id)`.
   - Enforces admission via `admit_chat_turn`:
     - Replay of completed turn: yields stored content and `DoneEvent(replayed=True)` without calling provider.
     - Request conflict (different input on same request_id): raises `ChatRequestConflictError`.
     - Quota limits: raises `ChatDailyLimitError` or `ChatRetryLimitError`.
   - Initializes assistant message with `status="active"`.
   - Executes `astream_turn_graph` under 45-second deadline.
   - Throttled partial output persistence: writes to `chat_messages` every 1 second or 256 new characters.
   - On completion: persists citations, final text, usage, and cost; marks message and turn `status="ok"`; emits `DoneEvent`.
   - If database finalization fails: never emits `DoneEvent`.
   - On cancellation/disconnect/timeout: updates message to `status="interrupted"`, updates turn, preserves partial text without fabricating replacements.
   - Post-turn summary: under 10-second deadline, calls model to summarize recent thread messages and performs CAS update. Summary failure does not fail the turn.
3. **Integration Tests (`test_chat_turn_lifecycle.py`)**:
   - Two tokens then persisted done with matching DB state.
   - Error/disconnect preserves interrupted partial content.
   - Repeated successful UUID replays without provider call.
   - Concurrent turn conflicts.
   - DB finalization failure emits no done.
