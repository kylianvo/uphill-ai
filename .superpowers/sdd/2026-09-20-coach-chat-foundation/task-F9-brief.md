# Task F9 Brief: Expose authenticated streaming, status, sources, clear and legacy compatibility

## Objective
Expose authenticated streaming SSE, thread pagination, turn status, message sources snapshot, thread clear, and backward-compatible legacy endpoints in `backend/routers/coach_chat.py` and `backend/db.py`. Verify with integration tests in `backend/tests/integration/test_chat_stream_api.py` and existing `backend/tests/integration/test_coach_chat_auth.py`.

## File Targets
- Modify: `backend/routers/coach_chat.py`
- Modify: `backend/db.py`
- Create: `backend/tests/integration/test_chat_stream_api.py`
- Report: `.superpowers/sdd/2026-09-20-coach-chat-foundation/task-F9-report.md`

## Specifications
1. **Streaming Endpoint (`POST /api/coach/chat/stream`)**:
   - Accepts `request_id`, `message`, `retry_of`, `lang`.
   - Validates UUID syntax, mutual exclusion of `message` and `retry_of`, and input length limit.
   - Emits SSE events: `status`, `token`, `citations`, `done`, `error`.
   - Sets headers: `Cache-Control: no-cache, no-transform`, `X-Accel-Buffering: no`, `Connection: keep-alive`.
   - Emits 10s idle heartbeat comment (`: heartbeat\n\n`).
2. **Thread Read & Pagination (`GET /api/coach/chat/thread`)**:
   - `before_id` and `limit` query parameters.
   - Returns chronologically ordered messages, thread summary, `has_more`, and `oldest_id` cursor.
3. **Turn Status (`GET /api/coach/chat/turns/{request_id}`)**:
   - Owner-scoped lookup returning `request_id`, `status`, `result_message_id`, and `attempt_number`.
   - Returns 404 for missing or unowned turns.
4. **Message Sources (`GET /api/coach/chat/messages/{message_id}/sources`)**:
   - Owner-scoped lookup returning retained `evidence`, `citations`, and `evidence_status`.
   - Returns 404 for missing or unowned messages.
5. **Thread Clear (`DELETE /api/coach/chat/thread`)**:
   - Deletes thread messages, drops summary, creates cleared tombstone turn row.
   - Preserves quotas and call accounting.
   - Raises 409 Conflict if a turn is currently active.
6. **Legacy Compatibility (`POST /api/coach/chat`)**:
   - Preserves session user identity, active plan, and Gemini API key resolution.
   - Never injects history into the persistent conversation thread.
   - Capped at 20 history items.
