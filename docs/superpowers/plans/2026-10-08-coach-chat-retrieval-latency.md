# Coach Chat Retrieval Latency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cut the Coach Chat "retrieve" step from a ~6.6s median to ~2s without changing what the coach answers.

**Architecture:** Three changes to the turn's critical path. (1) Reuse one Qdrant client and one Gemini client per process instead of building both on every turn, and remember which collections exist. (2) Start KB retrieval in a worker thread the moment the question is known, so it runs while chat context is read from Postgres instead of after. (3) Give each Qdrant query its own Langfuse span so the unexplained ~3s inside the retrieval span becomes visible. Retrieval inputs, `k` values and the prompt are unchanged.

**Tech Stack:** FastAPI, LangGraph, qdrant-client 1.18, google-genai, Langfuse (via `services/observability.py`), pytest with `asyncio_mode = auto`.

## Global Constraints

- No prompt, model or `k` changes. This plan is not an LLM change, so the `llm-change-process` golden eval does not apply; the retrieved chunks for a given question must be identical before and after.
- Langfuse metadata is allowlisted (`services/observability_policy.py:METADATA_KEYS`). Only use existing keys (`collections`, `retrieval_k`, …); never add question text or chunk content to spans.
- `services/kb_retrieval.py` functions stay synchronous (callers wrap them in `asyncio.to_thread`).
- Unit tests must not need Postgres, Qdrant or a Gemini key (`tests/unit/` runs in the pre-commit hook).
- Run backend commands from `backend/`.

## Baseline (Langfuse, production, 2026-09-24 → 2026-10-08)

| Observation | Count | p50 | p95 |
|---|---|---|---|
| `coach_chat.turn` span | 5 | 30.6s | 45.1s |
| `retrieve` chain (graph node) | 6 | 6.6s | 15.7s |
| `retrieval` span (`kb_retrieval`) | 17 | 4.0s | 12.6s |
| embedding generation | 17 | 1.0s | 2.8s |
| `generate` chain | 11 | 6.7s | 14.6s |

## File Structure

- Modify `backend/services/kb_retrieval.py`: cached `_client()`, new `_genai_client(api_key)`, new `_collection_exists(client, name)`, per-query `qdrant_query` spans.
- Modify `backend/services/coach_chat.py`: new `_prefetch_retrieval(retrieve, question)`; `run_turn` starts retrieval before reading chat context and reads chat context in a worker thread.
- Modify `backend/tests/unit/test_kb_retrieval.py`, `backend/tests/unit/test_chat_retrieval.py`: cache-reset fixture plus new tests.
- Create `backend/tests/unit/test_coach_chat_prefetch.py`.

---

### Task 1: Per-query Qdrant spans

Splits the 4s `retrieval` span into embedding (already its own generation) and each Qdrant query, so Task 4 can show where the remaining time goes.

**Files:**
- Modify: `backend/services/kb_retrieval.py:196-238` (`search_principles`), `:116` (`search_scheduler_chunks`)
- Test: `backend/tests/unit/test_chat_retrieval.py`

**Interfaces:**
- Consumes: `observability.span(name, *, metadata)` (`services/observability.py:712`).
- Produces: Langfuse spans named `qdrant_query` with `metadata={"collections": [<name>]}`.

- [ ] **Step 1: Write the failing test** (append to `tests/unit/test_chat_retrieval.py`)

```python
def test_search_principles_wraps_each_qdrant_query_in_a_span():
    import contextlib

    mock_qdrant = MagicMock()
    mock_qdrant.collection_exists.return_value = True
    mock_qdrant.query_points.return_value.points = []
    opened: list[tuple[str, dict]] = []

    @contextlib.contextmanager
    def fake_span(name, *, metadata=None):
        opened.append((name, metadata or {}))
        yield MagicMock()

    with (
        patch.object(kb_retrieval, "_client", return_value=mock_qdrant),
        patch.object(kb_retrieval, "_embed", return_value=[[0.1] * kb_retrieval.VECTOR_SIZE]),
        patch.object(kb_retrieval.observability, "span", side_effect=fake_span),
    ):
        kb_retrieval.search_principles("q", api_key="test-key")

    query_spans = [meta["collections"] for name, meta in opened if name == "qdrant_query"]
    assert query_spans == [[kb_retrieval.COLLECTION_SCHEDULER], [kb_retrieval.COLLECTION_NUTRITION_PRINCIPLES]]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_chat_retrieval.py::test_search_principles_wraps_each_qdrant_query_in_a_span -v`
Expected: FAIL, `assert [] == [[...], [...]]`

- [ ] **Step 3: Implement**

In `search_principles`, wrap each `query_points` call:

```python
        if has_sched and scheduler_k > 0:
            with observability.span("qdrant_query", metadata={"collections": [COLLECTION_SCHEDULER]}):
                hits_sched = client.query_points(
                    collection_name=COLLECTION_SCHEDULER, query=vector, limit=scheduler_k
                ).points
```

```python
        if has_nutr and nutrition_k > 0:
            with observability.span("qdrant_query", metadata={"collections": [COLLECTION_NUTRITION_PRINCIPLES]}):
                hits_nutr = client.query_points(
                    collection_name=COLLECTION_NUTRITION_PRINCIPLES, query=vector, limit=nutrition_k
                ).points
```

In `search_scheduler_chunks` (line 116):

```python
        with observability.span("qdrant_query", metadata={"collections": [COLLECTION]}):
            hits = client.query_points(collection_name=COLLECTION, query=vector, limit=limit).points
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_chat_retrieval.py tests/unit/test_kb_retrieval.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add backend/services/kb_retrieval.py backend/tests/unit/test_chat_retrieval.py
git commit -m "chore(kb): trace each Qdrant query as its own span"
```

---

### Task 2: Reuse Qdrant and Gemini clients; remember existing collections

Today every retrieval builds a new `QdrantClient` and a new `genai.Client` (fresh connections and TLS each turn) and makes two `collection_exists` round trips before searching.

**Files:**
- Modify: `backend/services/kb_retrieval.py:9-48` (imports, `_client`, `_embed`), `:107-112` (`search_scheduler_chunks`), `:174-178` (`search_principles`)
- Test: `backend/tests/unit/test_kb_retrieval.py`, `backend/tests/unit/test_chat_retrieval.py`

**Interfaces:**
- Produces: `_client() -> QdrantClient` (now cached, same signature), `_genai_client(api_key: str) -> genai.Client` (cached per key), `_collection_exists(client: QdrantClient, name: str) -> bool` (caches only `True`), module set `_existing_collections: set[str]`.

- [ ] **Step 1: Add a cache-reset fixture to both test files**

Top of `tests/unit/test_kb_retrieval.py` and `tests/unit/test_chat_retrieval.py`, after the imports:

```python
import pytest


@pytest.fixture(autouse=True)
def _reset_kb_retrieval_caches():
    kb_retrieval._genai_client.cache_clear()
    kb_retrieval._existing_collections.clear()
    yield
    kb_retrieval._genai_client.cache_clear()
    kb_retrieval._existing_collections.clear()
```

- [ ] **Step 2: Write the failing tests** (append to `tests/unit/test_kb_retrieval.py`)

```python
def test_genai_client_is_built_once_per_api_key():
    fake_hit = MagicMock()
    fake_hit.payload = {"title": "Taper", "content": "Cut volume ~50%."}
    fake_hit.score = 0.83
    fake_client = MagicMock()
    fake_client.collection_exists.return_value = True
    fake_client.query_points.return_value.points = [fake_hit]
    with (
        patch.object(kb_retrieval, "_client", return_value=fake_client),
        patch("google.genai.Client", side_effect=_fake_genai_client) as genai_ctor,
    ):
        kb_retrieval.search_scheduler_chunks("taper", api_key="test-key")
        kb_retrieval.search_scheduler_chunks("taper again", api_key="test-key")

    assert genai_ctor.call_count == 1


def test_existing_collection_is_checked_once():
    fake_client = MagicMock()
    fake_client.collection_exists.return_value = True
    fake_client.query_points.return_value.points = []
    with (
        patch.object(kb_retrieval, "_client", return_value=fake_client),
        patch("google.genai.Client", side_effect=_fake_genai_client),
    ):
        kb_retrieval.search_principles("q1", api_key="test-key")
        kb_retrieval.search_principles("q2", api_key="test-key")

    # Two collections, one existence check each across both searches.
    assert fake_client.collection_exists.call_count == 2


def test_missing_collection_is_rechecked_on_next_search():
    fake_client = MagicMock()
    fake_client.collection_exists.return_value = False
    with patch.object(kb_retrieval, "_client", return_value=fake_client):
        kb_retrieval.search_scheduler_chunks("q", api_key="test-key")
        kb_retrieval.search_scheduler_chunks("q", api_key="test-key")

    assert fake_client.collection_exists.call_count == 2
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/unit/test_kb_retrieval.py -v`
Expected: every test ERRORs in the fixture with `AttributeError: ... has no attribute '_genai_client'`

- [ ] **Step 4: Implement**

Imports (`kb_retrieval.py` top):

```python
import functools
import hashlib
from collections.abc import Callable
```

Replace `_client` and the first line of `_embed`:

```python
@functools.lru_cache(maxsize=1)
def _client() -> QdrantClient:
    # One client per process: it pools HTTP connections and is safe to share
    # across the worker threads that callers run these sync functions in.
    return QdrantClient(url=settings.QDRANT_URL)


@functools.lru_cache(maxsize=8)
def _genai_client(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key)


# Collections seen to exist. Only positive answers are cached, so a collection
# created after startup is picked up on the next search.
_existing_collections: set[str] = set()


def _collection_exists(client: QdrantClient, name: str) -> bool:
    if name in _existing_collections:
        return True
    if client.collection_exists(name):
        _existing_collections.add(name)
        return True
    return False


def _embed(texts: list[str], api_key: str, task_type: str) -> list[list[float]]:
    client = _genai_client(api_key)
```

In `search_scheduler_chunks`, replace `if not client.collection_exists(COLLECTION):` with:

```python
        if not _collection_exists(client, COLLECTION):
```

In `search_principles`, replace the two existence checks with:

```python
    has_sched = _collection_exists(client, COLLECTION_SCHEDULER)
    has_nutr = _collection_exists(client, COLLECTION_NUTRITION_PRINCIPLES)
```

Leave `reindex_*` and `scheduler_point_count` calling `client.collection_exists` directly: they run rarely and must see the live state.

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/unit/test_kb_retrieval.py tests/unit/test_chat_retrieval.py tests/unit/test_coach_tools_knowledge.py -v`
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add backend/services/kb_retrieval.py backend/tests/unit/test_kb_retrieval.py backend/tests/unit/test_chat_retrieval.py
git commit -m "perf(kb): reuse Qdrant and Gemini clients across retrievals"
```

---

### Task 3: Start retrieval while chat context is being read

`run_turn` reads chat context (`coach_context.build_chat_context`, ~4 Postgres queries) synchronously on the event loop, and only then does the graph's retrieve node start embedding and searching. This task starts retrieval in a worker thread first, then reads chat context in another worker thread, so the two overlap. The retrieve node already accepts an async `retrieve_fn` and keeps its 8s timeout.

**Files:**
- Modify: `backend/services/coach_chat.py:292-301` and `:343-351` (turn trace block)
- Create: `backend/tests/unit/test_coach_chat_prefetch.py`

**Interfaces:**
- Consumes: `build_graph(model, retrieve_fn, tools)` (`services/coach_graph.py:579`); retrieve node awaits `retrieve_fn(question)` when it is a coroutine function (`coach_graph.py:233`).
- Produces: `_prefetch_retrieval(retrieve: Callable[[str], list[dict]], question: str) -> Callable[[str], Awaitable[list[dict]]]` in `services/coach_chat.py`.

- [ ] **Step 1: Write the failing tests** (`tests/unit/test_coach_chat_prefetch.py`)

```python
import asyncio
import time

from services.coach_chat import _prefetch_retrieval


async def test_prefetch_returns_the_retrieval_result():
    retrieve = _prefetch_retrieval(lambda q: [{"title": q}], "taper")
    assert await retrieve("taper") == [{"title": "taper"}]


async def test_prefetch_overlaps_with_other_blocking_work():
    def slow_retrieve(_q):
        time.sleep(0.3)
        return []

    start = time.monotonic()
    retrieve = _prefetch_retrieval(slow_retrieve, "q")
    await asyncio.to_thread(time.sleep, 0.3)  # stands in for build_chat_context
    await retrieve("q")
    elapsed = time.monotonic() - start

    assert elapsed < 0.5  # sequential would be >= 0.6
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_coach_chat_prefetch.py -v`
Expected: FAIL with `ImportError: cannot import name '_prefetch_retrieval'`

- [ ] **Step 3: Add the helper** (in `services/coach_chat.py`, after `today_line`)

```python
def _prefetch_retrieval(
    retrieve: Callable[[str], list[dict[str, Any]]], question: str
) -> Callable[[str], Awaitable[list[dict[str, Any]]]]:
    """Start KB retrieval now in a worker thread; the graph's retrieve node awaits the result.

    Lets embedding + Qdrant run while the turn's chat context is read from Postgres."""
    task = asyncio.create_task(asyncio.to_thread(retrieve, question))

    async def _await_retrieval(_question: str) -> list[dict[str, Any]]:
        return await task

    return _await_retrieval
```

Change the import on line 8 of `coach_chat.py` from `from collections.abc import AsyncIterator` to:

```python
from collections.abc import AsyncIterator, Awaitable, Callable
```

- [ ] **Step 4: Run the helper tests**

Run: `pytest tests/unit/test_coach_chat_prefetch.py -v`
Expected: PASS

- [ ] **Step 5: Rewire `run_turn`**

Move the root-trace block up so the prefetched retrieval span is still a child of `coach_chat.turn`, start the prefetch, and read chat context off the event loop. Replace the current lines from `graph = build_graph(...)` through `chat_context = coach_context.build_chat_context(...)`:

```python
        # Root trace for the turn: feedback, proposal outcomes and judge scores attach to
        # its id, stored on the assistant message. Opened before retrieval starts so the
        # prefetched retrieval span is recorded inside it.
        turn_trace = contextlib.ExitStack()
        turn_trace.enter_context(
            observability.trace(
                "coach_chat.turn", feature="coach_chat", user_id=user_id, thread_id=thread_id, metadata={"lang": lang}
            )
        )
        trace_id = observability.current_trace_id()

        try:
            retrieve_kb = _prefetch_retrieval(_retrieve_kb, question)
            graph = build_graph(model=model, retrieve_fn=retrieve_kb, tools=tools or None)
            call_id = uuid4()

            chat_context = await asyncio.to_thread(
                coach_context.build_chat_context, user_id=user_id, question=question, thread_id=thread_id
            )
        except BaseException:
            turn_trace.close()
            raise
```

Then delete the old trace block that sat just before `try: async with asyncio.timeout(...)` (the `# Root trace for the turn` comment, `turn_trace = contextlib.ExitStack()`, `turn_trace.enter_context(...)`, `trace_id = ...`). Everything between (summary, `today`, `prior_messages`, `initial_state`, `accumulated`, …) stays as is. The existing `finally: turn_trace.close()` still closes the trace on the normal path.

- [ ] **Step 6: Run the coach chat unit tests**

Run: `pytest tests/unit -k "coach or chat or retrieval or kb" -v`
Expected: all PASS

- [ ] **Step 7: Run the whole unit suite and lint**

Run: `pytest tests/unit -q && ruff check services/coach_chat.py services/kb_retrieval.py tests/unit`
Expected: all PASS, no lint errors

- [ ] **Step 8: Commit**

```bash
git add backend/services/coach_chat.py backend/tests/unit/test_coach_chat_prefetch.py
git commit -m "perf(coach-chat): run KB retrieval alongside chat context assembly"
```

---

### Task 4: Deploy to production and measure

No staging step: staging is stopped on the production server. The change has no schema change and no prompt change, and every new code path falls back the way it did before (retrieval errors still land in the retrieve node's `except`), so production is the test bed.

**Files:** none (deploy and measure).

- [ ] **Step 1: Open the PR** with the baseline table above and wait for CI.

- [ ] **Step 2: Deploy to production by hand from this worktree.** `deploy_server.sh` clobbers the production `backend/.env`: back it up first (`backups/backend.env.pre-<branch>-<timestamp>`), and diff the env keys after the deploy. Set `LANGFUSE_RELEASE` to the deployed SHA (`git rev-parse --short HEAD`). No `alembic upgrade` is needed.

- [ ] **Step 3: Smoke test:** send 10 coach chat turns in production from the web app: 5 doctrine questions ("how long should my taper be?"), 5 small talk ("thanks!"). Check that each gets an answer, that doctrine answers still show citations, and that `docker logs` has no `KB retrieval failed` warnings. The first turn after a restart is a cold start; note it separately.

- [ ] **Step 4: Read latencies from Langfuse** (MCP `queryMetrics`, view `observations`, filter `environment = production`, time range = the smoke-test window, dimensions `name`, metrics `count`, `p50`/`p95` of `latency`). Record `retrieve`, `retrieval`, `qdrant_query`, embedding `generation`, `coach_chat.turn` on the PR next to the baseline.

  Success: `retrieve` p50 ≤ 2.5s. If `qdrant_query` p50 is still above ~200 ms, Qdrant itself is the problem (check its container resources and whether the backend reaches it over the Docker network or a public port). Open a follow-up for that; don't tune it in this PR.

  Rollback: redeploy the previous SHA (`48ba3a8` or whatever is live before Step 2) with the same `.env` backup routine.

- [ ] **Step 5: After 3 days in production,** rerun the Step 4 query over those 3 days and post the numbers on the PR.

---

## Follow-up plans (separate documents, write after Task 4's numbers are in)

1. **Model benchmark: Haiku 5.5 vs Gemini 3.8 Flash.** A script under `backend/scripts/` that replays each golden set (`tests/golden/`) through both models and records time to first token, total time, tokens and cost; quality compared with `scripts/golden_eval.py compare`. Golden sets exist for chat, gear, goal_judge, nutrition and scheduler. Start with Goal and Nutrition (small and fast to compare), then Plan. Price reference: Gemini 3.8 Flash $0.75 / $3.75 per 1M tokens in/out (doubles to $1.50 / $7.50 on 2027-01-01); Claude Haiku 5.5 $0.10 / $0.50 (≤100K-token prompts). Haiku 5.5 thinks by default at effort `medium` — benchmark at `low`. Needs a decision first: whether Coach Chat (LangChain tool binding) is in scope at all.
2. **Gear finder catalog prefilter.** Gear sends its whole catalog in the prompt (p50 19.7s, p95 45s). Filter catalog rows by category, terrain and budget in code before building the prompt, and record `catalog_entries` (already an allowed metadata key) to show the cut. This one changes the prompt, so it goes through `llm-change-process` with the gear golden set.
3. **Possible chat follow-ups once Task 4 is measured:** skip the upfront retrieval for short small-talk messages, and stop double-searching when the model also calls `kb_search` in the same turn.
