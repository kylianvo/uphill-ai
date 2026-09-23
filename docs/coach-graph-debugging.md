# Coach graph debugging

Three ways to see the Coach Chat LangGraph (`backend/services/coach_graph.py`).
All of them keep the privacy boundary: no prompt/reply content leaves your machine
except what you yourself view in LangGraph Studio's browser tab (§3).

## 1. Structure diagram

```bash
cd backend
.venv/bin/python -m scripts.draw_coach_graph            # with tools (the normal chat graph)
.venv/bin/python -m scripts.draw_coach_graph --no-tools # the linear no-API-key graph
.venv/bin/python -m scripts.draw_coach_graph --out /tmp/coach_graph.md
```

Paste the output into any Mermaid viewer (VS Code Markdown preview, GitHub). Rendering
is local; the script never calls the mermaid.ink web service.

## 2. Per-turn traces in Langfuse

The LangChain instrumentor in `services/observability.py` exports every graph node
(`retrieve`, `generate`, `tools`, `final_generate`) as a span. Content is masked by design
(`LANGFUSE_EXPORT_CONTENT=false` is enforced) -- you see the flow, timing, tool names and
token usage, never messages.

The privacy policy's span-name allowlist (`_SPAN_NAMES` in
`backend/services/observability_policy.py`) includes the coach graph's static node/tool
names -- `LangGraph`, `retrieve`, `generate`, `tools`, `final_generate`,
`_tools_condition`, `get_week`, `pace_strategy`, `week_review`, `kb_search`,
`propose_schedule_change` -- so Langfuse shows those names as-is; any other span name is
still masked to `operation`.

1. In the git-ignored `backend/.env` set `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`,
   `OBSERVABILITY_ID_SALT`, `LANGFUSE_ENVIRONMENT=local`, `LANGFUSE_SAMPLE_RATE=1`.
2. Restart the backend (`docker compose restart backend`, or re-run uvicorn).
3. Send a chat turn in the app.
4. In Langfuse (EU cloud) filter Environment = `local`, open the newest trace, and expand
   the LangGraph span to see the node spans in order.

`tests/integration/test_coach_graph_spans.py` guards both halves: nodes are exported, and
no question/reply text appears in any span.

## 3. LangGraph Studio (local dev database only)

Studio steps through a turn node by node with the state at each step.

**Privacy.** Studio's UI is a hosted page on smith.langchain.com that talks to the local
server (`127.0.0.1:2024`) from your browser. Use test users with synthetic data only. The
entry point refuses to load with `ENVIRONMENT=production` or a non-local `DATABASE_URL`
host. Never point it at staging or production. Leave `LANGSMITH_TRACING` unset, so
nothing is uploaded as a trace.

**Why a separate venv.** `langgraph-cli[inmem]` pulls `langgraph-api`, which needs
`protobuf<7` and OpenTelemetry 1.42, while the app pins OTel 1.44. It lives only in
`backend/.venv-studio` (already set up in this worktree -- don't recreate it, just
`pip install`-upgrade it if `requirements-studio.txt` changes).

`backend/.env` may not define `DATABASE_URL` (it doesn't in local dev by default, since
`config.py` falls back to a default). `dev/studio_graph.py` requires it to be set
explicitly so the local-only guard has something to check, so export it yourself before
`langgraph dev`, pointing at the port your local `db` container publishes (check with
`docker ps` -- e.g. `postgresql://uphill:uphill_secret@localhost:<db host port>/uphill_ai`):

```bash
cd backend
python3 -m venv .venv-studio                              # only if backend/.venv-studio doesn't already exist
.venv-studio/bin/pip install -r requirements.txt
.venv-studio/bin/pip install -r requirements-studio.txt   # pip may warn about OTel/protobuf -- fine here

export DATABASE_URL=postgresql://uphill:uphill_secret@localhost:<db host port>/uphill_ai  # port your local db container publishes
export STUDIO_USER_ID=<id of a local test user with an active plan>
export LANGGRAPH_CLI_NO_ANALYTICS=1
# optional: use Gemini (your key from backend/.env) instead of the scripted fake model
# export STUDIO_REAL_MODEL=1
.venv-studio/bin/langgraph dev
```

Open the printed Studio URL. It needs a free LangSmith login. In the `coach` graph, type
a `question` (and `lang`: `en` or `vi`) and run it. Expand the `coach` node to see
retrieve → generate → tools → generate / final_generate.

- The default fake model always calls `get_week`, then replies, so the tool loop is
  visible without an API key.
- Tools run for real against your local database as `STUDIO_USER_ID`.
- Studio runs write no chat messages and skip admission and rate limits.
