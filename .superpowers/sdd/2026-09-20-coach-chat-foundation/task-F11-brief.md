# Task F11 Brief: Build the UTF-8-safe frontend stream client and single state owner

## Goal
Build the robust, UTF-8 streaming SSE parser client in `frontend/src/lib/coachChatStream.ts` and the single conversation state hook in `frontend/src/hooks/useCoachChat.ts`. Colocate Vitest unit tests in `coachChatStream.test.ts` and `useCoachChat.test.ts`. Remove obsolete duplicate chat state from `frontend/src/contexts/AppContext.tsx` without touching unrelated code.

## Architecture & Requirements
1. **UTF-8 Streaming SSE Parser (`frontend/src/lib/coachChatStream.ts`)**:
   - Implements `consumeCoachChatStream(response: Response, onEvent: (event: ChatStreamEvent) => void, signal?: AbortSignal): Promise<void>`.
   - Uses `TextDecoder("utf-8")` with `{ stream: true }` to guarantee multi-byte UTF-8 characters (like Vietnamese diacritics: `à`, `ạ`, `ơ`, `ư`, `đ`) split across arbitrary byte chunk boundaries decode perfectly without  replacement characters.
   - Handles CRLF (`\r\n`) and LF (`\n`) line endings.
   - Ignores SSE comment lines (e.g. `: heartbeat\n\n`).
   - Parses multiple events packed within a single chunk or spread across multiple chunks.
   - Parses typed events: `status`, `token`, `citations`, `done`, `error`.
   - Distinguishes clean termination (`done` or `error`) from unexpected EOF mid-stream.
   - Validates event payload schemas and handles malformed JSON without crashing.

2. **Single Conversation State Owner (`frontend/src/hooks/useCoachChat.ts`)**:
   - Exposes `{ messages, activeRequest, status, error, hasMore, isLoadingOlder, send, retry, clear, loadOlder, refreshTurn, selectedMessageSources, fetchMessageSources, clearMessageSources }`.
   - Authenticated POST streaming with Bearer token from localStorage.
   - Deduplication & idempotency: uses `crypto.randomUUID()` for `request_id`; prevents concurrent double-submissions while a turn is active.
   - Explicit retry: generates a new `request_id` with `retry_of: rootRequestId`.
   - Incremental streaming updates: appends user message immediately, creates streaming assistant message, appends tokens smoothly, persists citations on `citations` event, and finalizes on `done`.
   - Honest partial retention: if an error occurs or connection drops mid-stream, preserves received tokens with `interrupted: true` rather than replacing with generic error text.
   - Pagination: loads previous messages via `GET /api/coach/chat/thread?before_id=...`.
   - Sources drawer: fetches and stores retained citations via `GET /api/coach/chat/messages/{id}/sources`.
   - Thread clear: issues `DELETE /api/coach/chat/thread`, handles 409 conflict gracefully, and resets local messages on success.
   - Cleanup: aborts in-flight stream on unmount or session logout.

3. **AppContext Clean-up (`frontend/src/contexts/AppContext.tsx`)**:
   - Clean up obsolete manual message state while preserving backwards compatibility for any lingering references.

4. **Colocated Unit Tests**:
   - `frontend/src/lib/coachChatStream.test.ts`: mid-codepoint UTF-8 splits, multiple events per chunk, CRLF, heartbeats, malformed JSON, premature EOF, done/error exclusivity.
   - `frontend/src/hooks/useCoachChat.test.ts`: thread pagination, stream progression, stable UUID admission, explicit retry, clear conflict, error partial preservation, unmount abort.
