# Task F11 Report: Build the UTF-8-safe frontend stream client and single state owner

## Summary
Task F11 implements the robust, UTF-8 streaming SSE parser in `frontend/src/lib/coachChatStream.ts` and the single conversation state owner in `frontend/src/hooks/useCoachChat.ts`. It removes duplicate chat state from `frontend/src/contexts/AppContext.tsx` while maintaining backward-compatible shims for unmigrated components, and provides full unit test coverage in `frontend/src/lib/coachChatStream.test.ts` and `frontend/src/hooks/useCoachChat.test.ts`.

## Components & Contracts Implemented
1. **UTF-8 SSE Stream Client (`frontend/src/lib/coachChatStream.ts`)**:
   - `consumeCoachChatStream(response, onEvent, signal)`:
     - Uses `TextDecoder("utf-8")` with `{ stream: true }` to guarantee multi-byte UTF-8 codepoints split across arbitrary chunk boundaries (such as Vietnamese diacritics: `à`, `ạ`, `ơ`, `ư`, `đ`) decode cleanly without Unicode replacement characters (`\uFFFD`).
     - Parses both CRLF (`\r\n`) and LF (`\n`) event delimiters.
     - Silently skips SSE comment lines (e.g. `: heartbeat\n\n`) to preserve connection liveness without polluting application event streams.
     - Dispatches strongly typed events: `StatusEvent`, `TokenEvent`, `CitationsEvent`, `DoneEvent`, `ErrorEvent`.
     - Validates terminal completion: throws `CoachChatStreamError` on premature stream cutoff or non-200 HTTP responses with parsed JSON error details.
     - Tolerates malformed JSON payloads without crashing the streaming parser.
2. **Conversation State Hook (`frontend/src/hooks/useCoachChat.ts`)**:
   - Manages complete turn and message lifecycle with the backend API:
     - Initial mount loads paginated thread via `GET /api/coach/chat/thread?limit=50`.
     - `send(text)`: Generates client UUID (`crypto.randomUUID()`), appends optimistic user message, connects to `POST /api/coach/chat/stream`, streams tokens directly into the assistant message, attaches citations, and finalizes with server message ID.
     - Concurrency protection: Locks execution ref to prevent duplicate or ambiguous submissions while a turn is active.
     - `retry(rootRequestId)`: Issues a new request with a fresh UUID and `retry_of` pointing to the root turn.
     - Partial message preservation: If a network disconnection, server error, or abort occurs, preserves already-received tokens and flags `interrupted: true` rather than replacing with fabricated canned error text.
     - `loadOlder()`: Paginates older history via `before_id`.
     - `clear()`: Sends `DELETE /api/coach/chat/thread`, handles 409 conflict if a turn is active, and resets local conversation state on success.
     - `fetchMessageSources(messageId)`: Loads citation and evidence snapshot on demand for the sources drawer.
     - Cleans up active fetch requests with `AbortController` on unmount.
3. **Context Clean-up (`frontend/src/contexts/AppContext.tsx`)**:
   - Removed duplicate `useState<Message[]>` and `useState(false)` chat loading state from `AppContext`.
   - Provided transitional read-only shims to prevent breaking unmigrated UI prior to Task F12.
4. **Colocated Vitest Test Suites**:
   - `frontend/src/lib/coachChatStream.test.ts`:
     - Multi-event chunk parsing.
     - Vietnamese multi-byte codepoints split across chunks without `\uFFFD`.
     - CRLF line ending compatibility.
     - Heartbeat comment skipping.
     - Citations event schema parsing.
     - Server error event dispatching.
     - HTTP non-200 error handling with detail parsing.
     - Premature EOF error detection.
     - Malformed JSON resilience.
   - `frontend/src/hooks/useCoachChat.test.ts`:
     - Initial paginated message loading on mount.
     - Incremental streaming token accumulation and turn completion.
     - Concurrent double-send protection.
     - Explicit retry with distinct UUID and `retry_of`.
     - Partial token preservation on stream failure with `interrupted: true`.
     - Thread clear success and 409 conflict handling.
     - Message source inspection and clearing.

## Files Touched
- Created: `frontend/src/lib/coachChatStream.ts`
- Created: `frontend/src/lib/coachChatStream.test.ts`
- Created: `frontend/src/hooks/useCoachChat.ts`
- Created: `frontend/src/hooks/useCoachChat.test.ts`
- Modified: `frontend/src/contexts/AppContext.tsx`
- Created: `.superpowers/sdd/2026-09-20-coach-chat-foundation/task-F11-brief.md`
- Created: `.superpowers/sdd/2026-09-20-coach-chat-foundation/task-F11-report.md`
