# Task F7 Brief: Implement the typed LangGraph runner

## Objective
Implement the typed, linear LangGraph runner (`START → retrieve → generate → END`) in `backend/services/coach_graph.py`. Define typed `TurnState`, application event union, and streaming execution with `stream_mode=["custom", "updates"], version="v2"`. Add comprehensive unit tests in `backend/tests/unit/test_coach_graph.py`.

## File Targets
- Create: `backend/services/coach_graph.py`
- Create: `backend/tests/unit/test_coach_graph.py`
- Report: `.superpowers/sdd/2026-09-20-coach-chat-foundation/task-F7-report.md`

## Specifications
1. **Typed State (`TurnState`)**:
   - TypedDict defining all turn state variables: `user_id`, `thread_id`, `request_id`, `call_id`, `question`, `lang`, `messages`, `context`, `evidence`, `evidence_status`, `system_prompt`, `prompt_name`, `prompt_version`, `prompt_source`, `reply_text`, `citations`, `usage`, `status`, `error_code`.
2. **Application Event Union**:
   - `StatusEvent`: `step: "retrieving" | "generating"`, `request_id: str`.
   - `TokenEvent`: `text: str`.
   - `CitationsEvent`: `citations: list[dict]`, `evidence_status: "available" | "empty" | "unavailable"`.
   - `DoneEvent`: `request_id: str`, `message_id: int | None`, `replayed: bool`.
   - `ErrorEvent`: `code: str`, `message: str | None`.
3. **Linear Graph (`build_graph`)**:
   - Nodes: `retrieve` and `generate` only.
   - Edges: `START → retrieve → generate → END`.
   - No checkpointer.
   - `retrieve` node:
     - Emits `status` event (`step="retrieving"`).
     - Calls `retrieve_fn(question)`:
       - If returns chunks: `evidence_status = "available"`.
       - If returns empty: `evidence_status = "empty"`.
       - If raises exception: catches, sets `evidence_status = "unavailable"`.
     - Assembles local prompt via `coach_prompts.compile_coach_prompt`.
     - Emits initial `citations` event with `evidence_status`.
   - `generate` node:
     - Emits `status` event (`step="generating"`).
     - Calls `model.stream(model_request)`.
     - Streams `token` custom events for each text chunk.
     - Rejects `tool_call` events by raising `ToolCallsNotSupportedError`.
     - Resolves citations from reply text against evidence.
     - Emits final `citations` event.
     - Finalizes usage in state.
4. **Streaming Projection (`astream_turn_graph`)**:
   - Calls `graph.astream(initial_state, stream_mode=["custom", "updates"], version="v2")`.
   - Yields only validated application events from `"custom"` stream.
   - Consumes `"updates"` internally to track state; never leaks raw state/messages to caller.
5. **Unit Tests (`test_coach_graph.py`)**:
   - Verify node execution order (`retrieve` then `generate`).
   - Verify token custom events emitted in order.
   - Verify private state updates.
   - Verify usage finalization.
   - Verify tool call rejection (`ToolCallsNotSupportedError`).
   - Verify cancellation handling.
   - Verify retrieval empty vs unavailable distinctions.
