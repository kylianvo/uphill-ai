# Coach Chat Foundation Stabilization Design

**Date:** 2026-09-20
**Sub-project:** 2 stabilization
**Branch under repair:** `codex/coach-chat-foundation`
**Reviewed range:** `09862fd..45520d0`

## Purpose

Repair the Coach Chat foundation so it satisfies the approved foundation
design and release contract before read-only tools are added. This work adds no
new coaching capability. It makes the existing persistent, bilingual,
retrieval-grounded streaming flow executable, bounded, auditable, and honest
about its verification evidence.

The stabilization is complete only when the production application imports,
the database lifecycle works against a fresh schema, all required backend and
frontend checks pass, and every release claim points to a reproducible command
or retained artifact.

## Scope

This stabilization includes:

- application import and production-build repairs;
- dual-schema corrections for chat message, turn, and call lifecycles;
- pre-stream validation, admission, quota, and credential checks;
- one shared bounded execution path for streaming and legacy chat;
- exact retry and stale-turn recovery semantics;
- durable accounting for answer, retrieval embedding, and summary calls;
- retained evidence and citation snapshots;
- enforced retrieval, input-token, output-token, and whole-turn limits;
- account-sensitive frontend state and UTF-8-safe SSE behavior;
- deterministic bilingual benchmark validation and honest release evidence;
- fresh dependency, migration, backend, frontend, and visual verification.

It excludes:

- model-callable tools, tool cards, and conditional tool routing;
- write proposals or Apply endpoints;
- changes to the coach copilot or week-review feature;
- new LLM, guardrail, evaluation, or infrastructure dependencies;
- deployment, production configuration changes, or Langfuse content export;
- invented latency, cost, quality, or safety results.

## Reproduced defects

The repair plan must cover these independently reproduced failures:

1. `routers/coach_chat.py` imports `resolve_zone2_pace` from
   `services.pacing_calculator`; the function is in `services.training_rules`,
   so backend test collection and application import fail.
2. Runtime inserts `chat_messages.status='active'`, but both schemas reject
   that status.
3. `clear_chat_thread()` inserts a turn without the required fingerprint.
4. Interrupted call finalization can write `chat_llm_calls.status='interrupted'`,
   but both schemas reject that status.
5. Main answer generation bypasses the durable `chat_llm_calls` lifecycle.
6. Final message persistence stores citations but drops the retrieval evidence
   snapshot.
7. The legacy endpoint still performs a full-KB raw Gemini call and bypasses
   the shared adapter, bounds, quotas, persistence, and accounting.
8. Input-token and retrieval deadlines are defined in the design but are not
   enforced; the model adapter also ignores `max_output_tokens`.
9. Retry finds the latest user message rather than the message attached to the
   referenced failed root turn.
10. Stale active turns are never recovered, and their rows can permanently
    block clear/recovery behavior after a worker failure.
11. `page.tsx` references the removed `chatMessages` binding, so the Next.js
    production build fails.
12. The frontend suite has nine failures: eight component tests lack a safe
    `scrollIntoView` environment and one UTF-8 fixture expects a character that
    its bytes do not contain.
13. The release report claims measured latency, cost, and 40/40 response
    quality without raw run artifacts or reproducible commands.

## Invariants

The following invariants apply to every implementation task:

- Authentication establishes `user_id`. Request bodies, graph state, prompts,
  and model/tool output never establish ownership.
- `LANGFUSE_EXPORT_CONTENT=false` remains the default. Prompts, replies,
  health notes, retrieved text, and tool arguments do not leave the service.
- `services/observability.py` remains the only module importing Langfuse,
  OpenInference, or OpenTelemetry packages.
- PostgreSQL remains the source of truth. LangGraph has no checkpointer.
- One athlete can have at most one executing turn across workers.
- No database transaction remains open during retrieval or generation.
- Every paid invocation has one durable call row and one canonical billable
  observability generation. Auto-instrumented descendants remain non-billable.
- Unknown usage and cost remain unknown; they are never converted to zero.
- `done` is emitted only after answer content, evidence, citations, metadata,
  call accounting, and turn state are durably finalized.
- The same dual schema is expressed in `db.py:init_db()` and the hand-written
  Alembic migration.
- English and Vietnamese behavior is equivalent for requests, status, errors,
  retries, citations, and visible UI copy.
- The coach copilot and week-review implementation are unchanged.

## Schema corrections

Because the foundation migration has not been merged, stabilization corrects
the existing foundation migration rather than adding a follow-up migration.
The matching `init_db()` DDL is changed in the same commit.

### `chat_messages`

The allowed statuses are:

```text
active | ok | error | interrupted
```

`active` represents a persisted partial assistant response. A terminal update
must change it to `ok`, `error`, or `interrupted`.

### `chat_turns`

Add nullable `user_message_id`, referencing `chat_messages(id) ON DELETE SET
NULL`. A newly admitted streaming turn links to the exact persisted user
message. Retries follow the owned root turn to this message instead of reading
the newest message in the thread.

The allowed statuses remain:

```text
active | ok | error | interrupted | cleared
```

Clearing a thread changes all of that athlete's retained turns to `cleared`,
sets `result_message_id` and `user_message_id` to null, and then removes message
content. It does not insert an unrelated synthetic turn.

### `chat_llm_calls`

The allowed statuses are:

```text
reserved | ok | error | interrupted | unknown
```

Add `user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE`.
`request_id` remains a non-null UUID used for grouping but is no longer a
cascading foreign key to `chat_turns`. This permits expired deduplication
tombstones to be deleted without deleting the content-free cost ledger, while
account deletion still removes all owned accounting rows.

`usage_known=false` is independent of terminal status. A cancelled call can be
`interrupted` with unknown usage; a provider failure can be `error` with known
or unknown usage.

Schema parity tests must compare columns, nullability, foreign keys, checks,
and indexes, not only table presence.

## Request preparation and execution

### Pre-stream preparation

The HTTP router validates and prepares a turn before constructing
`StreamingResponse`. Preparation performs, in order:

1. bearer authentication;
2. server-side feature-switch check;
3. `en|vi`, UUID, mutual-exclusion, and 4,000-character validation;
4. server-side credential resolution;
5. athlete advisory-lock acquisition;
6. owned request deduplication and atomic quota admission;
7. exact user-message persistence and turn linkage.

Stable failures from these steps return their specified HTTP status before SSE
headers. `prepare_turn(...)` returns a `PreparedTurn` that owns the
advisory-lock connection. `execute_prepared_turn(...)` consumes it inside the
SSE generator and releases it on normal completion, rejection, disconnect,
cancellation, or iterator close. If response construction fails after
preparation, the router closes the prepared turn explicitly. Preparation does
not start retrieval or a paid invocation.

### Stale-turn recovery

The advisory lock is the execution authority. After acquiring it, preparation
may recover that athlete's old `active` rows because no other worker can still
own the same athlete lock. Old active turns become `interrupted` with
`error_code='worker_interrupted'`; any active assistant partial is preserved as
interrupted. Recovery happens before admitting the new request.

An active row alone never blocks forever. A currently held advisory lock does
block with `chat_in_progress`.

### Streaming and legacy paths

`POST /api/coach/chat/stream` and legacy `POST /api/coach/chat` share the same
model adapter, retrieval operation, prompt compiler, limits, durable call
accounting, and error normalization.

The streaming route persists into the athlete's ongoing thread. The legacy
route preserves its request and JSON response shape and may use its bounded
client-provided history for that request, but it does not merge that supplied
history into the ongoing thread. It still reserves a new-turn quota and writes
an owned turn plus call ledger. It never calls `google.genai.Client` directly
and never loads the full KB dump.

## Bounded context and model execution

The ordinary turn enforces these backend limits:

| Control | Limit |
|---|---:|
| New turns per athlete per UTC day | 50 |
| Explicit retries per athlete per UTC day | 10 |
| Explicit retries per root turn | 2 |
| User input | 4,000 characters |
| Provider-counted input | 16,000 tokens |
| Model output | 2,048 tokens |
| Retained history | 20 messages |
| Recent activities | 8 within 14 days |
| Retrieval results | 4 scheduler + 2 nutrition-principle chunks |
| Retrieval deadline | 5 seconds |
| Whole ordinary turn | 45 seconds |
| Summary | 10 seconds |

Synchronous Qdrant and embedding work runs in a worker thread so it cannot
block the FastAPI event loop. The five-second retrieval timeout wraps the
awaited worker operation. A timed-out or unavailable retrieval emits
`evidence_status='unavailable'` and continues only where the existing safety
rules permit an unsourced general explanation.

After retrieval, the service assembles the exact model request and calls the
provider adapter's token counter. It removes oldest history first, then
lowest-scoring evidence, recounting after each reduction. The current question
and essential server context are never removed. If essential input still
exceeds 16,000 provider-counted tokens, the request terminates with
`chat_context_too_large` before answer generation.

`ModelRequest.max_output_tokens=2048` must reach the live provider request.
Automatic provider retries remain disabled. Graph/model iterators and provider
clients are closed in `finally` paths.

Conversation history and the retained summary must be included in the model
request or compiled prompt; persistence without conversational continuity is
not accepted.

## Durable accounting and observability

The service creates a distinct call ID and ledger row before each invocation:

- `chat_retrieval` for the query embedding;
- `coach_chat` for the answer;
- `chat_summary` for a summary refresh.

Answer and summary streams use the existing canonical
`observability.generation()` scope through `CoachModel`. Retrieval embedding
uses the existing retrieval/embedding observability boundary. Durable ledger
updates do not depend on Langfuse sampling or exporter availability.

The answer graph must consume a tracked model stream rather than calling the
adapter directly. Final cumulative usage updates both the canonical generation
and the reserved call row. Cancellation, timeout, provider error, missing final
usage, and database-finalization failure each have deterministic terminal
states.

Only approved metadata leaves the service: pseudonymous user/thread IDs,
feature, bounded model name, prompt name/version/source, call status, numeric
usage/cost/latency, evidence refs and scores. Existing serialized-export canary
tests must cover the repaired graph path.

## Evidence and message finalization

The assistant message stores, before `done`:

- complete or retained partial content;
- terminal message status and stable error code;
- retrieval evidence snapshot with source identity, ref, score, domain, title,
  source label, URL, and retained excerpt;
- resolved citations;
- prompt name, version, and source;
- model name;
- nullable usage and cost;
- latency and trace ID when available.

Citation URLs remain limited to valid HTTP(S) URLs from the retrieved evidence.
A citation marker that does not match retained evidence is not exposed as a
source. Evidence and citations expire with message content after 90 days.

The sources endpoint remains owner-scoped and reads only the retained snapshot;
it does not rerun retrieval.

## Retry, replay, clear, and retention

- Reusing a request UUID with the same fingerprint replays the persisted
  terminal result without a provider call or another quota reservation.
- Reusing it with different input returns `request_conflict`.
- Retry accepts only an owned `error` or `interrupted` root, creates a new UUID,
  links to the same root, and uses the root's exact `user_message_id` content.
- Retry never inserts a duplicate user message.
- A cleared or expired request returns `410 request_expired`.
- Clear conflicts only while the advisory lock is currently held.
- Clear deletes content and summaries but preserves daily counters and the call
  ledger.
- Retention deletes expired messages in bounded batches, removes stale
  summaries, and deletes expired cleared turn tombstones without cascading into
  `chat_llm_calls`.
- Account deletion cascades through all chat content, turns, usage, and call
  accounting by `user_id`.

## Frontend behavior

`useCoachChat` remains the sole conversation-state owner. It keys its lifecycle
to the authenticated account/session, not only component mount:

- abort the active stream on logout or account change;
- clear messages, selected sources, status, errors, pagination, and active
  request before loading the next account;
- never show one athlete's cached messages to another athlete;
- retain a stable request UUID for ambiguous network recovery;
- create a new UUID linked by `retry_of` only for explicit Retry.

The SSE parser continues to use streaming `TextDecoder`. Its split-codepoint
test fixture must contain the exact expected Vietnamese text. DOM-only test
environments install a `scrollIntoView` stub or the component checks that the
method is callable; the production behavior remains smooth scrolling.

The obsolete page-level chat scroll effect and transitional no-op chat state
shims are removed when no live consumer remains. The Next.js production build,
frontend tests, and lint all run from a clean install. Desktop and mobile
screenshots must show empty, streaming, interrupted, and citation states that
are reachable from the real backend contract.

## Release evidence

The release report distinguishes four kinds of evidence:

1. deterministic tests and their exact command/output;
2. owner-reviewed screenshots with file paths and test state;
3. synthetic fixture coverage and deterministic invariant results;
4. staging measurements with raw artifact, timestamp, sample size, load shape,
   cold/warm split, model/prompt versions, and calculation method.

The 40-case fixture validates dataset shape and deterministic prohibited-output
checks. It is not a 40/40 answer-quality result unless all 40 model outputs were
actually generated, retained, reviewed against the rubric, and linked from the
report.

The p95 latency values remain targets until a representative staging run
exists. Estimated cost must state the price table, token sample, calculation,
and whether usage was measured or hypothetical. Unsupported numbers are
removed rather than softened with approximate language.

## Verification gates

All gates must pass from the repaired branch before it can be called complete:

1. `git diff --check` reports no errors.
2. A fresh Python environment installs `backend/requirements.txt` alone;
   `pip check` passes and the full transitive tree is retained.
3. `python -c 'import main'` succeeds in the clean environment.
4. Alembic upgrades a fresh PostgreSQL database to head; schema-parity tests
   compare both schema paths.
5. The complete backend unit suite passes.
6. The complete non-external integration suite passes against PostgreSQL,
   including authentication regressions and all chat lifecycle tests.
7. Targeted regression tests demonstrate each reproduced defect fails before
   its fix and passes afterward.
8. `npm ci`, complete frontend tests, lint, and `npm run build` pass.
9. Serialized-export canaries prove no prompt, response, athlete context,
   evidence excerpt, provider error text, or tool argument leaves through OTel
   or Langfuse.
10. Real desktop and mobile screenshot evidence is retained and reviewed.
11. The release report contains no unsupported measured-result claim.
12. A final whole-branch security/correctness review finds no unresolved
    Critical or Important issue.

## Execution order

Repairs are implemented in this dependency order:

1. boot and dual-schema lifecycle;
2. atomic preparation, stale recovery, exact retry, clear, and retention;
3. bounded context, retrieval, and provider execution;
4. durable call accounting and export-boundary verification;
5. evidence/message finalization and shared legacy execution;
6. frontend account isolation, parser/tests, and production build;
7. deterministic benchmark and honest release report;
8. clean-install, migration, full-suite, visual, and whole-branch gates.

Sub-project 3 planning may proceed in parallel as documentation, but its code
must not execute or merge until these stabilization gates pass.
