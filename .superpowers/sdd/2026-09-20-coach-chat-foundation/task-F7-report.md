# Task F7 Report: Implement the typed LangGraph runner

## Summary
Task F7 implements the typed, linear LangGraph runner (`START → retrieve → generate → END`) in `backend/services/coach_graph.py` without a checkpointer. It defines `TurnState`, the application event union (`StatusEvent`, `TokenEvent`, `CitationsEvent`, `DoneEvent`, `ErrorEvent`), safe custom event streaming via `stream_mode=["custom", "updates"], version="v2"`, and private internal state consumption. Comprehensive unit tests are added in `backend/tests/unit/test_coach_graph.py`.

## Components & Contracts Implemented
1. **Typed State (`TurnState`)**:
   - Explicit TypedDict tracking request/session identity, server trusted context, prompt templates, retrieval evidence & status, streaming output chunks, citations, final usage, and error codes.
2. **Application Event Union (`coach_graph.py`)**:
   - `StatusEvent`: Emits `retrieving` and `generating` steps with `request_id`.
   - `TokenEvent`: Emits incremental generated text chunks.
   - `CitationsEvent`: Emits resolved citation references and `evidence_status` (`available`, `empty`, or `unavailable`).
   - `DoneEvent`: Terminal event containing `request_id`, optional `message_id`, and `replayed` flag.
   - `ErrorEvent`: Error event containing stable error code and optional message.
   - `parse_app_event`: Validates and parses custom stream payloads into typed AppEvent instances.
3. **Linear StateGraph (`build_graph`)**:
   - `retrieve` node: Emits retrieving status, runs query retrieval with resilient fallback (empty vs unavailable distinction), updates context, compiles prompt locally, and emits initial citations event.
   - `generate` node: Emits generating status, calls model stream, emits incremental token events, rejects tool calls with `ToolCallsNotSupportedError`, resolves citations against evidence, and records final usage.
   - Clean linear topology: `START → retrieve → generate → END` with no checkpointer.
4. **Streaming Runner (`astream_turn_graph`)**:
   - Streams from compiled graph with `stream_mode=["custom", "updates"], version="v2"`.
   - Yields only validated application events to caller. Consumes `"updates"` internally so raw internal state and messages never leak.
5. **Unit Test Verification (`tests/unit/test_coach_graph.py`)**:
   - `test_graph_retrieve_generate_order_and_events`: Verifies sequential node order and event delivery.
   - `test_graph_retrieval_empty`: Verifies empty evidence status when retrieval returns 0 chunks.
   - `test_graph_retrieval_unavailable`: Verifies non-crashing graceful degradation when vector database is unavailable.
   - `test_graph_tool_calls_rejected`: Verifies `ToolCallsNotSupportedError` when model emits tool call.
   - `test_graph_private_state_and_usage_finalization`: Verifies private state accumulation and usage recording.

## Files Touched
- Created: `backend/services/coach_graph.py`
- Created: `backend/tests/unit/test_coach_graph.py`
- Created: `.superpowers/sdd/2026-09-20-coach-chat-foundation/task-F7-brief.md`
- Created: `.superpowers/sdd/2026-09-20-coach-chat-foundation/task-F7-report.md`
