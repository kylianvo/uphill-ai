# Task F5 Report: Build bounded trusted context and two-domain retrieval

## Summary
Task F5 implements two-domain semantic principle retrieval (`uphill_kb_scheduler` and `uphill_kb_nutrition_principles`) in `backend/services/kb_retrieval.py` using a single query embedding, and builds athlete trusted context assembly, 16,000-token budget trimming, and citation resolution in `backend/services/coach_context.py`. It extends the observability allowlist for `uphill_kb_nutrition_principles` in `backend/services/observability_policy.py`, wires nutrition principles reindexing in `backend/services/kb_distiller.py`, and validates all behavior with unit test suites in `backend/tests/unit/test_chat_retrieval.py` and `backend/tests/unit/test_chat_context.py`.

## Components & Contracts Implemented
1. **Two-Domain Principle Retrieval (`services/kb_retrieval.py`)**:
   - `search_principles(query, api_key, scheduler_k=4, nutrition_k=2)`:
     - Generates a single query embedding via `gemini-embedding-2`.
     - Queries `uphill_kb_scheduler` (up to 4 training chunks) and `uphill_kb_nutrition_principles` (up to 2 nutrition principle chunks).
     - Tolerates either or both collections missing without error.
     - Never returns nutrition products or ungrounded invented links.
   - `reindex_nutrition_principles(chunks, api_key)`:
     - Rebuilds Qdrant collection `uphill_kb_nutrition_principles` with cosine distance and vector size 3072.
   - Updated `_COLLECTIONS` allowlist in `backend/services/observability_policy.py`.
   - Wired into `save_domain` and `load_seed` in `backend/services/kb_distiller.py`.
2. **Athlete Trusted Context Assembler (`services/coach_context.py`)**:
   - `build_chat_context(user_id, question, thread_id, retrieval_evidence, now)`:
     - Server-side trusted state only: athlete physiology, current & next week plan workouts, recent activities (capped at 8, within 14 days).
     - Retained thread history (max 20 messages, status='ok' only, excluding expired messages > 90 days).
     - Current question is always included and never trimmed.
   - `trim_context_to_budget(context, token_counter, max_budget=16000)`:
     - If context exceeds 16,000 token budget: trims oldest thread history messages first, then lowest-scoring evidence.
     - Raises `CoachChatError(code="chat_context_too_large")` if essential baseline still exceeds budget.
   - `resolve_citations(reply_text, evidence)`:
     - Matches `[ref:<id>]` or `[<id>]` against turn evidence.
     - Validates URLs (preserves only `http://` and `https://`; non-HTTP schemes sanitized to None).
3. **Unit Test Verification**:
   - `tests/unit/test_chat_retrieval.py`: Verifies single embedding call, multi-domain search, missing collection resilience.
   - `tests/unit/test_chat_context.py`: Verifies message status and 90-day retention filtering, 14-day activity cap, token budget trimming order (history then evidence), essential overflow error, and URL sanitization.

## Files Touched
- Modified: `backend/services/kb_retrieval.py`
- Created: `backend/services/coach_context.py`
- Modified: `backend/services/kb_distiller.py`
- Modified: `backend/services/observability_policy.py`
- Created: `backend/tests/unit/test_chat_retrieval.py`
- Created: `backend/tests/unit/test_chat_context.py`
- Created: `.superpowers/sdd/2026-09-20-coach-chat-foundation/task-F5-brief.md`
- Created: `.superpowers/sdd/2026-09-20-coach-chat-foundation/task-F5-report.md`
