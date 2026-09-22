# Task F1 Report: Isolate the endpoint and prove the model/dependency boundary

## Summary
Task F1 isolates the athlete coach chat endpoint from `backend/main.py` into `backend/routers/coach_chat.py`, introduces the provider-neutral `CoachModel` protocol, data classes (`ModelRequest`, `ModelEvent`, `ChatMessage`), test fake (`FakeCoachModel`), and the `GeminiCoachModel` adapter in `backend/services/coach_model.py`. It also creates `backend/services/coach_prompts.py` for system instructions and Vietnamese language rules, updates `backend/requirements.txt` with exact pins `langgraph==1.2.11` and `langchain-google-genai==4.4.0`, and adds comprehensive unit tests in `backend/tests/unit/test_coach_model.py`.

## Interfaces Produced
- `ModelRequest`: immutable request contract carrying `messages`, `system`, `max_output_tokens`, `call_id`.
- `ModelEvent`: immutable event contract with `kind: "text" | "usage" | "tool_call"`.
- `CoachModel`: protocol exposing `count_tokens`, `stream`, and `close`.
- `FakeCoachModel`: mock provider satisfying `CoachModel` for orchestration tests without Gemini SDK dependencies.
- `GeminiCoachModel`: adapter wrapping `ChatGoogleGenerativeAI`, enforcing `max_retries=0`, thinking block exclusion, tool call rejection in Foundation, single canonical `observability.generation` wrapping, and stable local exception mapping (`CoachModelUpstreamError`).

## Dependency Resolution Analysis
- Pinned candidates:
  - `langgraph==1.2.11`
  - `langchain-google-genai==4.4.0`
- Compatibility with existing stack:
  - `langchain-core==1.6.3` satisfies `langchain-core>=1.6.0` required by `langchain-google-genai 4.4.0` and `langgraph 1.2.11`.
  - `google-genai>=2.0.0` satisfies provider driver requirements.
  - OpenTelemetry pins (`opentelemetry-api==1.44.0`, `opentelemetry-sdk==1.44.0`) and Langfuse (`langfuse==4.15.3`) remain unweakened.
- Tracing & Privacy Canary:
  - One `observability.generation("generation", feature="coach_chat", ...)` is held per stream.
  - Auto-instrumentation spans from LangChain or Google GenAI are marked non-billable child spans.
  - `LANGFUSE_EXPORT_CONTENT=false` prevents prompt text, thinking blocks, and messages from leaking to OTLP exports.
  - No LangSmith environment variables or exporters are enabled.

## Files Touched
- Created: `backend/routers/coach_chat.py`
- Created: `backend/services/coach_model.py`
- Created: `backend/services/coach_prompts.py`
- Modified: `backend/main.py`
- Modified: `backend/requirements.txt`
- Created: `backend/tests/unit/test_coach_model.py`
- Preserved: `backend/tests/integration/test_coach_chat_auth.py`
- Created: `.superpowers/sdd/2026-09-20-coach-chat-foundation/task-F1-brief.md`
- Created: `.superpowers/sdd/2026-09-20-coach-chat-foundation/task-F1-report.md`

## Verification
- Unit test suite `test_coach_model.py`:
  - `test_model_request_and_event_immutability`: PASS
  - `test_fake_coach_model_implements_protocol`: PASS
  - `test_gemini_adapter_streams_vietnamese_text_chunks`: PASS (multibyte UTF-8 chunks assemble unchanged)
  - `test_gemini_adapter_excludes_thinking_blocks`: PASS (thinking block excluded from text stream)
  - `test_gemini_adapter_normalizes_usage_once`: PASS (single Usage event with cached tokens)
  - `test_gemini_adapter_rejects_tool_calls_in_foundation`: PASS (raises ToolCallsNotSupportedError)
  - `test_gemini_adapter_maps_provider_errors_to_stable_local_exception`: PASS (no raw provider error leak)
  - `test_gemini_adapter_wraps_in_canonical_generation`: PASS (single generation scope with feature="coach_chat")
- Integration tests `test_coach_chat_auth.py`:
  - Preserved session-only identity, stored Gemini key precedence, and active plan context isolation.
