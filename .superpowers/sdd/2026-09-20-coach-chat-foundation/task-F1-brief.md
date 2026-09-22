# Task F1 Brief: Isolate the endpoint and prove the model/dependency boundary

## Objective
Isolate athlete coach chat routing into `backend/routers/coach_chat.py`, implement the provider-neutral `CoachModel` protocol and `GeminiCoachModel` adapter in `backend/services/coach_model.py`, define prompt interfaces in `backend/services/coach_prompts.py`, and test dependency candidates (`langgraph==1.2.11` and `langchain-google-genai==4.4.0`) against existing `langchain-core==1.6.3` and pinned observability stack.

## File Targets
- Create: `backend/routers/coach_chat.py`
- Create: `backend/services/coach_model.py`
- Create: `backend/services/coach_prompts.py`
- Modify: `backend/main.py`
- Modify: `backend/requirements.txt`
- Test: `backend/tests/unit/test_coach_model.py`
- Test: `backend/tests/integration/test_coach_chat_auth.py`
- Report: `.superpowers/sdd/2026-09-20-coach-chat-foundation/task-F1-report.md`

## Key Interfaces
```python
@dataclass(frozen=True)
class ModelRequest:
    messages: tuple[ChatMessage, ...]
    system: str
    max_output_tokens: int
    call_id: UUID

@dataclass(frozen=True)
class ModelEvent:
    kind: Literal["text", "usage", "tool_call"]
    text: str | None = None
    usage: Usage | None = None
    tool_call: dict | None = None

class CoachModel(Protocol):
    async def count_tokens(self, request: ModelRequest) -> int: ...
    async def stream(self, request: ModelRequest) -> AsyncIterator[ModelEvent]: ...
    async def close(self) -> None: ...
```

## Constraints & Requirements
1. UTF-8 Vietnamese multi-byte chunks assemble unchanged.
2. Provider thinking blocks are excluded from `ModelEvent(kind="text")`.
3. Usage is normalized once into canonical `Usage`.
4. Stream cancellation closes provider iterator properly.
5. Tool-call output from model is rejected with stable exception in Foundation.
6. Provider exceptions become stable local exceptions.
7. Include fake second provider implementing `CoachModel` for orchestration tests without Gemini imports.
8. Move athlete chat request types and route wiring to `routers/coach_chat.py`. Mount router in `main.py`. Preserve copilot constants, coach notes, and server lookups.
9. Wrap generation in single `observability.generation("generation", feature="coach_chat")`.
10. Pin exact compatible dependencies: `langgraph==1.2.11` and `langchain-google-genai==4.4.0`.
11. Clean install, `pip check`, and dependency delta inspection.
12. Real nested `ChatGoogleGenerativeAI` + Google GenAI instrumentation canary: verify one cost record, zero content canaries in serialized OTLP, no LangSmith active.
