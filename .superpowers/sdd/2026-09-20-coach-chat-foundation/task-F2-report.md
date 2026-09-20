# Task F2 Report: Add the dual-schema conversation and accounting model

## Summary
Task F2 establishes the durable dual-schema persistence model for Coach Chat across both `backend/db.py:init_db()` and a hand-written Alembic migration `backend/alembic/versions/b2c3d4e5f6a7_coach_chat_foundation.py` (with `down_revision = "a1b2c3d4e5f7"` matching the current migration head). It registers all 5 new tables in child-first order in `backend/tests/integration/conftest.py`'s `ALL_TABLES`, implements owner-scoped parameterized SQL CRUD helpers in `backend/db.py`, and validates schema parity and table behavior in `backend/tests/integration/test_chat_schema.py`.

## Tables & Contracts Added
1. `chat_threads`:
   - Columns: `id` (SERIAL PK), `user_id` (INTEGER NOT NULL UNIQUE FK users ON DELETE CASCADE), `summary` (TEXT), `summarized_through_id` (INTEGER FK chat_messages ON DELETE SET NULL), `created_at` (TIMESTAMPTZ), `updated_at` (TIMESTAMPTZ).
   - Index: `idx_chat_threads_user_id`.
2. `chat_messages`:
   - Columns: `id` (SERIAL PK), `thread_id` (INTEGER NOT NULL FK chat_threads ON DELETE CASCADE), `role` (TEXT CHECK ('user', 'assistant')), `content` (TEXT NOT NULL), `lang` (TEXT DEFAULT 'en'), `status` (TEXT CHECK ('ok', 'error', 'interrupted')), `error_code` (TEXT), `evidence` (JSONB), `citations` (JSONB), `prompt_name` (TEXT), `prompt_version` (TEXT), `model` (TEXT), `usage` (JSONB), `cost_usd` (NUMERIC(10, 6)), `latency_ms` (INTEGER), `trace_id` (TEXT), `created_at` (TIMESTAMPTZ).
   - Index: `idx_chat_messages_thread_created` (`thread_id`, `created_at DESC`).
   - Circular FK `fk_chat_threads_summarized_through`: `chat_threads.summarized_through_id` -> `chat_messages.id` ON DELETE SET NULL.
3. `chat_turns`:
   - Columns: `request_id` (UUID PK), `user_id` (INTEGER NOT NULL FK users ON DELETE CASCADE), `thread_id` (INTEGER FK chat_threads ON DELETE CASCADE), `fingerprint` (TEXT NOT NULL), `root_turn_id` (UUID FK chat_turns(request_id) ON DELETE SET NULL), `attempt_number` (INTEGER NOT NULL DEFAULT 1), `status` (TEXT CHECK ('active', 'ok', 'error', 'interrupted', 'cleared')), `result_message_id` (INTEGER FK chat_messages ON DELETE SET NULL), `created_at` (TIMESTAMPTZ), `updated_at` (TIMESTAMPTZ).
   - Indexes: `idx_chat_turns_user_created` (`user_id`, `created_at DESC`), `idx_chat_turns_root` (`root_turn_id`).
4. `chat_daily_usage`:
   - Columns: `usage_date` (DATE), `user_id` (INTEGER NOT NULL FK users ON DELETE CASCADE), `new_turns_count` (INTEGER NOT NULL DEFAULT 0), `retries_count` (INTEGER NOT NULL DEFAULT 0), `created_at` (TIMESTAMPTZ), `updated_at` (TIMESTAMPTZ).
   - Primary Key: `(usage_date, user_id)`.
5. `chat_llm_calls`:
   - Columns: `call_id` (UUID PK), `request_id` (UUID NOT NULL FK chat_turns ON DELETE CASCADE), `feature` (TEXT NOT NULL), `model` (TEXT NOT NULL), `usage_known` (BOOLEAN NOT NULL DEFAULT FALSE), `input_tokens` (INTEGER NOT NULL DEFAULT 0), `output_tokens` (INTEGER NOT NULL DEFAULT 0), `thinking_tokens` (INTEGER NOT NULL DEFAULT 0), `cached_tokens` (INTEGER NOT NULL DEFAULT 0), `cost_usd` (NUMERIC(10, 6)), `status` (TEXT CHECK ('reserved', 'ok', 'error', 'unknown')), `latency_ms` (INTEGER), `created_at` (TIMESTAMPTZ), `completed_at` (TIMESTAMPTZ).
   - Index: `idx_chat_llm_calls_request_id` (`request_id`).

## Data Access Helpers Added in `db.py`
- `get_or_create_chat_thread(user_id: int) -> dict[str, Any]`
- `append_chat_message(...) -> int`
- `update_chat_message(...) -> None` (and alias `update_chat_message_content`)
- `get_chat_message(message_id: int, user_id: int | None = None) -> dict[str, Any] | None`
- `get_chat_thread_messages(user_id: int, before_id: int | None = None, limit: int = 20) -> list[dict[str, Any]]`
- `create_chat_turn(...) -> None`
- `get_chat_turn(user_id: int, request_id: Any) -> dict[str, Any] | None`
- `update_chat_turn_status(request_id: Any, status: str, result_message_id: int | None = None) -> None`
- `reserve_chat_call(call_id: Any, request_id: Any, feature: str, model: str) -> None`
- `finish_chat_call(...) -> None`
- `get_chat_call(call_id: Any) -> dict[str, Any] | None`

## Files Touched
- Modified: `backend/db.py`
- Created: `backend/alembic/versions/b2c3d4e5f6a7_coach_chat_foundation.py`
- Modified: `backend/tests/integration/conftest.py`
- Created: `backend/tests/integration/test_chat_schema.py`
- Created: `.superpowers/sdd/2026-09-20-coach-chat-foundation/task-F2-brief.md`
- Created: `.superpowers/sdd/2026-09-20-coach-chat-foundation/task-F2-report.md`
