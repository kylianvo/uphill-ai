# Task F5 Brief: Build bounded trusted context and two-domain retrieval

## Objective
Build two-domain semantic retrieval (`uphill_kb_scheduler` + `uphill_kb_nutrition_principles`) in `backend/services/kb_retrieval.py` and assemble bounded trusted context and citations in `backend/services/coach_context.py`. Update reindex hooks in `backend/services/kb_distiller.py` and allowlist in `backend/services/observability_policy.py`.

## File Targets
- Modify: `backend/services/kb_retrieval.py`
- Create: `backend/services/coach_context.py`
- Modify: `backend/services/kb_distiller.py`
- Modify: `backend/services/observability_policy.py`
- Create: `backend/tests/unit/test_chat_retrieval.py`
- Create: `backend/tests/unit/test_chat_context.py`
- Report: `.superpowers/sdd/2026-09-20-coach-chat-foundation/task-F5-report.md`

## Specifications
1. **Two-Domain Semantic Retrieval**:
   - Collections: `uphill_kb_scheduler` (up to 4 chunks) and `uphill_kb_nutrition_principles` (up to 2 chunks).
   - `search_principles(query: str, api_key: str, scheduler_k: int = 4, nutrition_k: int = 2) -> list[dict]`:
     - Embeds `query` once using `gemini-embedding-2` (`task_type="retrieval_query"`).
     - Queries both collections if they exist; tolerates either or both missing without error.
     - Excludes nutrition catalog products (only `kind=principle` indexed).
     - Returns list of evidence objects with `title`, `content`, `score`, `ref`, `domain`, `source_label`, `url`.
   - `reindex_nutrition_principles(chunks: list[dict], api_key: str) -> int`:
     - Creates/rebuilds collection `uphill_kb_nutrition_principles` with cosine distance and vector size 3072.
   - Updates `_COLLECTIONS` allowlist in `backend/services/observability_policy.py`.

2. **Bounded Trusted Context Assembler (`coach_context.py`)**:
   - Pulls server-side trusted state for authenticated `user_id`:
     - Physiology and preferences from `users`.
     - Current and next week workouts from `plans` & `workouts`.
     - Recent completed activities: max 8 within last 14 days from `activities`.
     - Retained thread history: max 20 messages, strictly excluding `status != 'ok'` and expired content (> 90 days).
     - Retrieved evidence list.
     - Current athlete question (never trimmed).
   - Budget trimming (16,000 tokens):
     - If total tokens exceed 16,000, trims oldest history first, then least-relevant evidence.
     - If essential context (physiology + plan + question) still exceeds 16,000, raises `CoachChatError(code="chat_context_too_large")`.
   - `resolve_citations(text: str, evidence: list[dict]) -> list[dict]`:
     - Extracts citation keys from text and resolves against turn evidence. Validates HTTP(S) URLs.
