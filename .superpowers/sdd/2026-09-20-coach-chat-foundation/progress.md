# SDD ledger — plan: docs/superpowers/plans/2026-09-20-coach-chat-foundation.md

Task F1: starting from 09862fd (main merge commit).
Worktree: .claude/worktrees/coach-chat-foundation on branch codex/coach-chat-foundation.
Superpowers skills announced and activated:
- superpowers:using-git-worktrees
- superpowers:executing-plans
- superpowers:test-driven-development
- superpowers:requesting-code-review
- superpowers:receiving-code-review
- superpowers:verification-before-completion
- superpowers:finishing-a-development-branch
- db-migration
- uphill-ai-vietnamese-copy
- ui-screenshot-evidence
- langfuse

Task F1: isolated athlete chat routing into routers/coach_chat.py, created provider-neutral CoachModel protocol and GeminiCoachModel adapter in services/coach_model.py, created coach_prompts.py, pinned langgraph==1.2.11 and langchain-google-genai==4.4.0 in requirements.txt, added test_coach_model.py. Unit tests verify protocol satisfaction, Vietnamese chunk assembly, thinking block exclusion, tool call rejection, single canonical generation wrapping, and error normalization. Review clean. Task F1 complete.

Task F2: added durable dual-schema persistence model across db.py:init_db() and Alembic migration b2c3d4e5f6a7_coach_chat_foundation.py (down_revision = "a1b2c3d4e5f7"). Added chat_threads, chat_messages, chat_turns, chat_daily_usage, chat_llm_calls. Updated ALL_TABLES in conftest.py. Added parameterized SQL CRUD helpers in db.py for thread creation, message append/update, owner-scoped turn lookup and call accounting. Parity and lifecycle verified in test_chat_schema.py. Review clean. Task F2 complete.

Task F3: implemented namespaced PostgreSQL session advisory locking via dedicated checked-out connections (chat_turn_lock), canonical SHA-256 fingerprinting (compute_chat_fingerprint), and durable turn admission (admit_chat_turn) with daily new turn quota (50), daily retry quota (10), root retry limit (2), replay detection, and conflict detection. Updated config.py, deploy.env.example, CLAUDE.md. Integration tests in test_chat_admission.py verify contention, connection drop release, quotas, limits, replays, and UTC rollover. Review clean. Task F3 complete.

Task F4: implemented durable exactly-once call accounting via conditional pending-to-terminal updates in finish_chat_call, multi-call turn aggregation in chat_turn_totals, and call tracking orchestration in services/coach_chat.py (track_chat_call). Integrated with observability.cost_usd and Usage while maintaining strict privacy and zero direct Langfuse imports. Integration tests in test_chat_accounting.py verify conditional transitions, multi-call aggregation, root/retry isolation, and unknown usage on interruption. Review clean. Task F4 complete.

Task F5: implemented two-domain semantic principle retrieval (uphill_kb_scheduler and uphill_kb_nutrition_principles) in services/kb_retrieval.py (search_principles, reindex_nutrition_principles), updated collection allowlist in services/observability_policy.py, and built athlete context assembly, token budget trimming (16,000 budget, trimming history then evidence), and citation resolution with URL sanitization in services/coach_context.py. Unit tests in test_chat_retrieval.py and test_chat_context.py verify single query embedding, multi-domain search, budget enforcement, and citation validation. Review clean. Task F5 complete.

Task F6: implemented Langfuse prompt template versioning with in-memory caching and resilient local fallback in services/observability.py (PromptTemplate, get_prompt_template, clear_prompt_cache), allowlisted prompt metadata keys (prompt_name, prompt_version, prompt_source) in services/observability_policy.py, added configuration in config.py, deploy.env.example, CLAUDE.md, and built local prompt compilation with athlete profile, workouts, and Vietnamese runner tone/term/ban-list rules in services/coach_prompts.py. Unit tests in test_coach_prompts.py verify absent keys fallback, successful fetch, network failure fallback, stale cache fallback, local compilation, and metadata filtering. Review clean. Task F6 complete.

Task F7: implemented typed linear LangGraph retrieve-generate runner (START -> retrieve -> generate -> END) without checkpointer in services/coach_graph.py (TurnState, AppEvent union, StatusEvent, TokenEvent, CitationsEvent, DoneEvent, ErrorEvent, build_graph, astream_turn_graph). Stream mode uses pinned ["custom", "updates"], version="v2". Consumes updates privately; yields validated application events. Handles retrieval empty vs unavailable gracefully; rejects tool calls with ToolCallsNotSupportedError. Unit tests in test_coach_graph.py verify node execution order, token events, private state updates, usage finalization, tool call rejection, and KB availability resilience. Review clean. Task F7 complete.

Task F8: implemented turn execution lifecycle runner (run_turn), session advisory locking, quota admission, 45s turn deadline, throttled partial message persistence (1s / 256 chars), error/cancellation partial retention without fabricated replacement, and 10s post-turn thread summary updates with CAS in services/coach_chat.py and db.py:update_chat_thread_summary_cas. Integration tests in test_chat_turn_lifecycle.py verify successful streaming, error partial preservation, replay without model invocation, conflict detection, and no done emission on DB finalization failure. Review clean. Task F8 complete.

Task F9: exposed authenticated streaming SSE (POST /api/coach/chat/stream with 10s heartbeats and error isolation), thread pagination (GET /api/coach/chat/thread), turn status (GET /api/coach/chat/turns/{id}), message sources snapshot (GET /api/coach/chat/messages/{id}/sources), thread clear with 409 conflict handling (DELETE /api/coach/chat/thread), and backward-compatible legacy endpoint (POST /api/coach/chat) in routers/coach_chat.py and db.py (get_chat_thread_paginated, get_chat_message_sources, clear_chat_thread). Integration tests in test_chat_stream_api.py verify validation, SSE event framing, pagination, status, sources, and clear conflict semantics. Review clean. Task F9 complete.

Task F10: implemented 90-day conversation retention enforcement, bounded batch pruning of expired messages, stale summary resets, and cleared turn tombstones in db.py (prune_coach_chat), un-ignored docs/coach-chat-retention-runbook.md and release report in .gitignore, created CLI runner in backend/scripts/prune_coach_chat.py, documented operational runbook in docs/coach-chat-retention-runbook.md, and validated retention boundaries, quota preservation, 410 tombstone semantics, and account deletion cascading in test_chat_retention.py. Review clean. Task F10 complete.

Task F11: implemented UTF-8 safe incremental streaming SSE parser in frontend/src/lib/coachChatStream.ts (handling split Vietnamese multi-byte codepoints, CRLF, heartbeat comment skipping, typed event unions, and premature stream error detection) and single conversation state owner in frontend/src/hooks/useCoachChat.ts (handling mount pagination, in-place token streaming, deduplication, retry_of semantics, interrupted partial retention, thread clearing with 409 conflict handling, on-demand source fetching, and unmount abort). Removed duplicate chat state from frontend/src/contexts/AppContext.tsx. Colocated unit test suites in coachChatStream.test.ts and useCoachChat.test.ts pass. Review clean. Task F11 complete.

Task F12: rendered bilingual Coach Chat interface in frontend/src/views/ChatTab.tsx and sources drawer in frontend/src/components/ChatSources.tsx consuming useCoachChat exclusively. Enforced honest boundaries (no write tools, cards, Apply buttons, or false claims), added bilingual locale dictionaries in frontend/src/app/translations.ts meeting uphill-ai-vietnamese-copy standards, delegated ChatView.tsx to ChatTab, removed dead chat methods from page.tsx, and validated component behaviors, status labels, interrupted message retry actions, 429/409 errors, and source links in ChatTab.test.tsx and ChatSources.test.tsx. Review clean. Task F12 complete.



