# Task F9 Report: Expose authenticated streaming, status, sources, clear and legacy compatibility

## Summary
Task F9 implements and exposes all authenticated HTTP and SSE endpoints for Coach Chat in `backend/routers/coach_chat.py` and `backend/db.py`: streaming SSE (`POST /api/coach/chat/stream`), thread pagination (`GET /api/coach/chat/thread`), turn status (`GET /api/coach/chat/turns/{request_id}`), message sources snapshot (`GET /api/coach/chat/messages/{message_id}/sources`), conversation clear (`DELETE /api/coach/chat/thread`), and backward-compatible legacy query (`POST /api/coach/chat`). Behavior is verified with integration tests in `backend/tests/integration/test_chat_stream_api.py`.

## Components & Contracts Implemented
1. **Streaming SSE Endpoint (`POST /api/coach/chat/stream`)**:
   - Validates client `request_id` (UUID format).
   - Validates mutual exclusion between `message` and `retry_of`.
   - Validates message character limit (`COACH_CHAT_MAX_INPUT_CHARS`).
   - Streams `status`, `token`, `citations`, `done`, and `error` SSE events.
   - Sets streaming response headers (`no-cache`, `X-Accel-Buffering: no`, `keep-alive`).
   - Emits idle heartbeat comments (`: heartbeat\n\n`) on 10s intervals.
2. **Conversation Pagination (`GET /api/coach/chat/thread`)**:
   - Retrieves chronologically ordered messages with `before_id` cursor and `limit` capped at 50.
   - Includes current thread summary and `has_more` pagination flag.
3. **Turn Status Endpoint (`GET /api/coach/chat/turns/{request_id}`)**:
   - Owner-scoped lookup returning `status`, `result_message_id`, and `attempt_number`.
   - Returns 404 for missing or unowned turns.
4. **Message Sources Endpoint (`GET /api/coach/chat/messages/{message_id}/sources`)**:
   - Returns retained `evidence` items, `citations`, and `evidence_status` (`available` or `empty`).
   - Returns 404 for unowned or non-existent messages.
5. **Thread Clear Endpoint (`DELETE /api/coach/chat/thread`)**:
   - Deletes thread messages and citations, resets summary, and creates content-free cleared turn tombstone in `chat_turns`.
   - Preserves athlete quotas and durable call ledger.
   - Raises 409 Conflict if an active turn is currently in progress.
6. **Legacy Endpoint (`POST /api/coach/chat`)**:
   - Preserves session user identity, active plan, and Gemini API key resolution.
   - Capped at 20 history items; does not mutate persistent chat threads.
7. **Integration Test Suite (`tests/integration/test_chat_stream_api.py`)**:
   - `test_stream_api_pre_validation`: Validates UUID syntax, mutual exclusion, empty input, and character length limits.
   - `test_stream_api_sse_streaming`: Validates SSE event framing, headers, tokens, and done event.
   - `test_get_chat_thread_and_pagination`: Validates chronological order and pagination.
   - `test_get_chat_turn_status`: Validates turn status lookup and 404 behavior.
   - `test_get_chat_message_sources`: Validates retained sources lookup and 404 behavior.
   - `test_clear_chat_thread`: Validates message deletion, summary reset, and 409 conflict during active turn.

## Files Touched
- Modified: `backend/routers/coach_chat.py`
- Modified: `backend/db.py`
- Created: `backend/tests/integration/test_chat_stream_api.py`
- Created: `.superpowers/sdd/2026-09-20-coach-chat-foundation/task-F9-brief.md`
- Created: `.superpowers/sdd/2026-09-20-coach-chat-foundation/task-F9-report.md`
