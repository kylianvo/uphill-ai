# Coach Chat First-Token Latency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the first words of a Coach Chat reply appear sooner, and measure it.

**Architecture:** Streaming already works end to end: `GeminiCoachModel.stream` yields text chunks from `chat.astream`, the graph's generate node forwards each one as a `token` SSE event, and both the web app (`useCoachChat`) and iOS (`ChatService`) append tokens as they arrive. So the wait is all before the first token: retrieval (now ~0.7s) plus Gemini's thinking. Two changes: (1) record time to first token on each coach generation so Langfuse can show it (today it is empty), and (2) apply `GEMINI_THINKING_LEVEL` to Coach Chat. Every other Gemini caller already sends `thinking_level=low`; `GeminiCoachModel` stores `thinking_level` but never passes it to `ChatGoogleGenerativeAI`, so Coach Chat runs at Gemini's default level. In production a coach generation spends a median 471 and a p95 of 2,332 reasoning tokens (Langfuse, 2026-09-24 → 10-09, 24 generations), all before the first visible token.

**Tech Stack:** FastAPI, LangGraph, `langchain-google-genai` 4.4.0 (`ChatGoogleGenerativeAI(thinking_config=...)`), `google-genai` `types.ThinkingConfig`, Langfuse OTel export via `services/observability.py`.

## Global Constraints

- Change 2 changes model behaviour, so it follows `.claude/skills/llm-change-process/SKILL.md`: capture the chat golden baseline **before** the change, compare after, put the checklist in the PR.
- Langfuse export is allowlisted (`services/observability_policy.py`); content never leaves the process. The first-token timestamp is a timestamp only.
- Unit tests must not need Postgres, Qdrant or a Gemini key.
- No staging: deploy to production by hand (back up `.env`, diff env keys after, set `LANGFUSE_RELEASE`). Auto mode blocks Claude's production writes, so the user runs the deploy commands.
- Run backend commands from `backend/`.

## Baseline (production)

| Coach chat, after #103 + #105 (4 turns) | p50 |
|---|---|
| Whole turn | 19.5s |
| `generate` (one model call) | 8.5s |
| retrieve step | 0.74s |
| time to first token | not recorded |

## File Structure

- Modify `backend/services/observability.py`: `GenerationRecorder.mark_first_token()`.
- Modify `backend/services/observability_policy.py`: allow `langfuse.observation.completion_start_time`.
- Modify `backend/services/coach_model.py`: mark the first text chunk; pass `thinking_config` to both `ChatGoogleGenerativeAI` constructions.
- Tests: `backend/tests/unit/test_observability_langfuse.py`, `backend/tests/unit/test_observability_policy.py`, `backend/tests/unit/test_coach_model.py`.

---

### Task 1: Record time to first token

**Files:**
- Modify: `backend/services/observability.py` (`GenerationRecorder`, ~line 787)
- Modify: `backend/services/observability_policy.py` (`_sanitize_attribute`, ~line 336)
- Modify: `backend/services/coach_model.py:225-233` (text extraction in `stream`)
- Test: `backend/tests/unit/test_observability_policy.py`, `backend/tests/unit/test_observability_langfuse.py`, `backend/tests/unit/test_coach_model.py`

**Interfaces:**
- Produces: `GenerationRecorder.mark_first_token() -> None` — idempotent; the first call sets Langfuse `completion_start_time` to now (UTC), later calls do nothing.
- Langfuse serializes the value as a JSON string, e.g. `'"2026-10-09T01:02:03Z"'` (checked with `langfuse._client.attributes._serialize`).

- [ ] **Step 1: Write the failing policy test** (append to `tests/unit/test_observability_policy.py`)

```python
def test_completion_start_time_attribute_exports_only_timestamps():
    def attrs(value):
        envelope = {"name": "generation", "attributes": {"langfuse.observation.completion_start_time": value}}
        return policy.sanitize_span_envelope(envelope)["attributes"]

    assert attrs('"2026-10-09T01:02:03Z"') == {"langfuse.observation.completion_start_time": '"2026-10-09T01:02:03Z"'}
    assert attrs('"what is my tempo pace?"') == {}
```

- [ ] **Step 2: Write the failing export test** (append to `tests/unit/test_observability_langfuse.py`)

```python
def test_generation_exports_first_token_time_once(langfuse_spans):
    with obs.generation("generation", feature="coach_chat", model="gemini-3.8-flash") as gen:
        gen.mark_first_token()
        gen.mark_first_token()  # no-op: the first call wins

    attrs = _attrs(_by_name(langfuse_spans, "generation"))
    assert attrs["langfuse.observation.completion_start_time"].startswith('"20')
```

- [ ] **Step 3: Write the failing adapter test** (append to `tests/unit/test_coach_model.py`)

```python
@pytest.mark.asyncio
async def test_gemini_adapter_marks_first_token_once():
    async def fake_astream(messages):
        for t in ["Easy ", "run ", "today."]:
            chunk = MagicMock()
            chunk.content = t
            chunk.additional_kwargs = {}
            chunk.tool_calls = []
            chunk.tool_call_chunks = []
            chunk.usage_metadata = None
            yield chunk

    adapter = GeminiCoachModel(api_key="test-key", model="gemini-3.8-flash")
    adapter._chat = MagicMock()
    adapter._chat.astream = fake_astream
    req = ModelRequest(
        messages=(ChatMessage(role="user", content="What today?"),),
        system="You are Coach Uphill.",
        max_output_tokens=500,
        call_id=uuid4(),
    )

    with patch("services.observability.generation") as mock_gen:
        recorder = mock_gen.return_value.__enter__.return_value
        events = [e async for e in adapter.stream(req)]

    assert [e.text for e in events if e.kind == "text"] == ["Easy ", "run ", "today."]
    recorder.mark_first_token.assert_called_once_with()
```

- [ ] **Step 4: Run the three tests to verify they fail**

Run: `pytest tests/unit/test_observability_policy.py tests/unit/test_observability_langfuse.py tests/unit/test_coach_model.py -q -k "completion_start or first_token"`
Expected: 3 failures (`{} == {...}`, `KeyError`/`AttributeError: mark_first_token`, `assert_called_once_with` called 0 times)

- [ ] **Step 5: Allow the attribute** (`observability_policy.py`, inside `_sanitize_attribute`, next to the other `if key == ...` checks)

```python
    if key == "langfuse.observation.completion_start_time":
        try:
            stamp = json.loads(value) if isinstance(value, str) else None
            datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return None
        return value
```

Add `from datetime import datetime` to the imports if it is not already there (`grep -n "^from datetime\|^import datetime" services/observability_policy.py`).

- [ ] **Step 6: Add `mark_first_token`** (`observability.py`, in `GenerationRecorder`; add `self._first_token_marked = False` in `__init__`)

```python
    def mark_first_token(self) -> None:
        """Record when the first visible token arrived (Langfuse time to first token). First call wins."""
        if self._first_token_marked:
            return
        self._first_token_marked = True
        if self._handle is None:
            return
        try:
            self._handle.update(completion_start_time=datetime.now(UTC))
        except Exception as exc:
            _warn_once("generation_first_token", exc)
```

Add `from datetime import UTC, datetime` to `observability.py`'s imports if missing.

- [ ] **Step 7: Mark the first text chunk** (`coach_model.py`, replace the "3. Extract text content" block)

```python
                    # 3. Extract text content
                    content = getattr(chunk, "content", None)
                    if isinstance(content, str):
                        texts = [content]
                    elif isinstance(content, list):
                        texts = [
                            part if isinstance(part, str) else part.get("text", "")
                            for part in content
                            if isinstance(part, str) or (isinstance(part, dict) and part.get("type") == "text")
                        ]
                    else:
                        texts = []
                    for text in texts:
                        if text:
                            gen.mark_first_token()
                            yield ModelEvent(kind="text", text=text)
```

- [ ] **Step 8: Run tests**

Run: `pytest tests/unit/test_observability_policy.py tests/unit/test_observability_langfuse.py tests/unit/test_coach_model.py tests/unit/test_coach_graph.py -q`
Expected: all PASS

- [ ] **Step 9: Commit**

```bash
git add backend/services/observability.py backend/services/observability_policy.py backend/services/coach_model.py backend/tests/unit/test_observability_policy.py backend/tests/unit/test_observability_langfuse.py backend/tests/unit/test_coach_model.py
git commit -m "chore(coach-chat): record time to first token on coach generations"
```

---

### Task 2: Apply the thinking level to Coach Chat

**Files:**
- Modify: `backend/services/coach_model.py:8-9` (imports), `:123-160` (`__init__`, `_get_chat`)
- Test: `backend/tests/unit/test_coach_model.py`

**Interfaces:**
- `GeminiCoachModel(api_key, model="gemini-3.8-flash", thinking_level: str | None = None, tools=None)`; `None` means `settings.GEMINI_THINKING_LEVEL` (prod: `low`). Callers (`coach_chat.py:301`, `scripts/golden_eval.py:158`) don't pass it and need no change.

- [ ] **Step 1: Capture the chat golden baseline before changing anything** (needs a `backend/.env` with `GEMINI_API_KEY` and a loaded KB; copy the main checkout's, never commit it)

Run: `python scripts/golden_eval.py capture --service chat`
Expected: `tests/golden/chat/*.ref.json` written, one per fixture. Commit these baselines on their own: `git commit -m "test(golden): chat baseline before thinking-level change"`.

- [ ] **Step 2: Write the failing tests** (append to `tests/unit/test_coach_model.py`)

```python
def test_gemini_adapter_sends_the_configured_thinking_level():
    adapter = GeminiCoachModel(api_key="test-key", tools=["fake-tool"])
    with (
        patch("langchain_google_genai.ChatGoogleGenerativeAI") as MockChat,
        patch("services.coach_model.settings.GEMINI_THINKING_LEVEL", "low"),
    ):
        MockChat.return_value.bind_tools.return_value = MockChat.return_value
        adapter._get_chat()
        adapter._get_chat(tools_enabled=False)

    for call in MockChat.call_args_list:
        assert call.kwargs["thinking_config"].thinking_level == "low"


def test_gemini_adapter_explicit_thinking_level_wins():
    adapter = GeminiCoachModel(api_key="test-key", thinking_level="medium")
    with patch("langchain_google_genai.ChatGoogleGenerativeAI") as MockChat:
        adapter._get_chat()
    assert MockChat.call_args.kwargs["thinking_config"].thinking_level == "medium"
```

- [ ] **Step 3: Run to verify they fail**

Run: `pytest tests/unit/test_coach_model.py -q -k thinking`
Expected: FAIL with `KeyError: 'thinking_config'` (and `AttributeError` on `settings` until the import exists)

- [ ] **Step 4: Implement**

Imports (`coach_model.py`):

```python
from config import settings
from services import observability
from services.observability import Usage
```

`__init__` signature and assignment:

```python
        thinking_level: str | None = None,
```

```python
        self.thinking_level = thinking_level or settings.GEMINI_THINKING_LEVEL
```

Add a helper method and use it in both constructions inside `_get_chat`:

```python
    def _new_chat(self) -> Any:
        from google.genai import types
        from langchain_google_genai import ChatGoogleGenerativeAI

        # max_retries=0: SDK retries are disabled per spec
        return ChatGoogleGenerativeAI(
            model=self.model,
            api_key=self.api_key,
            max_retries=0,
            temperature=0.3,
            thinking_config=types.ThinkingConfig(thinking_level=self.thinking_level),
        )
```

```python
    def _get_chat(self, tools_enabled: bool = True) -> Any:
        if not tools_enabled:
            # Forced final generation (tool budget exhausted): a fresh,
            # unbound chat instance so the model cannot emit another
            # tool_call. Not cached on self._chat -- that cache is the
            # tools-bound instance the rest of the turn uses.
            return self._new_chat()
        if self._chat is None:
            chat = self._new_chat()
            self._chat = chat.bind_tools(self.tools) if self.tools else chat
        return self._chat
```

- [ ] **Step 5: Run unit tests**

Run: `pytest tests/unit -q`
Expected: all PASS (the existing `test_gemini_adapter_binds_tools_when_provided` patches the same class and still passes)

- [ ] **Step 6: Compare against the golden baseline**

Run: `python scripts/golden_eval.py compare --service chat`
Expected: `tests/golden/report_chat.md` written. Accept only if no case loses a `must_contain` term or breaks a safety invariant, and the LLM-judge scores are within the run-to-run noise you see when running `compare` twice on the unchanged baseline. If quality drops, stop: pin chat to `"medium"` (`GeminiCoachModel(..., thinking_level="medium")` in `coach_chat.py`), compare again, and check with the user before going further.

- [ ] **Step 7: Commit**

```bash
git add backend/services/coach_model.py backend/tests/unit/test_coach_model.py backend/tests/golden/report_chat.md
git commit -m "perf(coach-chat): apply GEMINI_THINKING_LEVEL to coach chat generations"
```

---

### Task 3: PR, production deploy, measure

**Files:** none.

- [ ] **Step 1: Open the PR** with the `llm-change-process` checklist, the golden report summary and the baseline table above.

- [ ] **Step 2: Deploy by hand** (user runs; auto mode blocks Claude). Three backend files changed: `services/coach_model.py`, `services/observability.py`, `services/observability_policy.py`. Check production's copies match `main` first, back up those files and `backend/.env` into `backups/`, copy, set `LANGFUSE_RELEASE` to the PR head SHA, `docker compose restart backend`, wait for `/api/health` 200 (90–130 s), diff env keys against the backup. No dependency or schema change.

- [ ] **Step 3: Smoke test:** clear the chat thread, send 10 messages (5 training questions, 5 small talk), one at a time.

- [ ] **Step 4: Measure** (Langfuse `queryMetrics`, view `observations`, `environment = production`, `traceName = coach_chat.turn`, test window): `timeToFirstToken` p50/p95 on `type = GENERATION`; `latency` p50 of `coach_chat.turn` and `generate`; `usageByType` p50 for `output_reasoning`. Post before/after on the PR.

  Success: reasoning tokens p50 well below 471, `generate` p50 below 8.5s, and a first-token time that, plus the ~0.7s retrieval, is under ~3s for turns without a tool call.
