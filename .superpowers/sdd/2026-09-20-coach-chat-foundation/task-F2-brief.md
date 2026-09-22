# Task F2 Brief: Add the dual-schema conversation and accounting model

## Objective
Add the durable conversation and call accounting model to both `backend/db.py:init_db()` and a hand-written Alembic migration `backend/alembic/versions/b2c3d4e5f6a7_coach_chat_foundation.py` (down_revision `a1b2c3d4e5f7`), update `ALL_TABLES` in `backend/tests/integration/conftest.py`, provide owner-scoped CRUD helpers in `db.py`, and test schema parity in `backend/tests/integration/test_chat_schema.py`.

## File Targets
- Modify: `backend/db.py`
- Create: `backend/alembic/versions/b2c3d4e5f6a7_coach_chat_foundation.py`
- Modify: `backend/tests/integration/conftest.py`
- Create: `backend/tests/integration/test_chat_schema.py`
- Report: `.superpowers/sdd/2026-09-20-coach-chat-foundation/task-F2-report.md`

## Required Tables & Schemas
1. `chat_threads`:
   - `id`: SERIAL PRIMARY KEY
   - `user_id`: INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE
   - `summary`: TEXT
   - `summarized_through_id`: INTEGER (FK chat_messages(id) ON DELETE SET NULL)
   - `created_at`: TIMESTAMPTZ DEFAULT NOW()
   - `updated_at`: TIMESTAMPTZ DEFAULT NOW()
   - Index: `idx_chat_threads_user_id`

2. `chat_messages`:
   - `id`: SERIAL PRIMARY KEY
   - `thread_id`: INTEGER NOT NULL REFERENCES chat_threads(id) ON DELETE CASCADE
   - `role`: TEXT NOT NULL CHECK (role IN ('user', 'assistant'))
   - `content`: TEXT NOT NULL
   - `lang`: TEXT NOT NULL DEFAULT 'en'
   - `status`: TEXT NOT NULL DEFAULT 'ok' CHECK (status IN ('ok', 'error', 'interrupted'))
   - `error_code`: TEXT
   - `evidence`: JSONB
   - `citations`: JSONB
   - `prompt_name`: TEXT
   - `prompt_version`: TEXT
   - `model`: TEXT
   - `usage`: JSONB
   - `cost_usd`: NUMERIC(10, 6)
   - `latency_ms`: INTEGER
   - `trace_id`: TEXT
   - `created_at`: TIMESTAMPTZ DEFAULT NOW()
   - Index: `idx_chat_messages_thread_created` (thread_id, created_at DESC)

3. `chat_turns`:
   - `request_id`: UUID PRIMARY KEY
   - `user_id`: INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE
   - `thread_id`: INTEGER REFERENCES chat_threads(id) ON DELETE CASCADE
   - `fingerprint`: TEXT NOT NULL
   - `root_turn_id`: UUID REFERENCES chat_turns(request_id) ON DELETE SET NULL
   - `attempt_number`: INTEGER NOT NULL DEFAULT 1
   - `status`: TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'ok', 'error', 'interrupted', 'cleared'))
   - `result_message_id`: INTEGER REFERENCES chat_messages(id) ON DELETE SET NULL
   - `created_at`: TIMESTAMPTZ DEFAULT NOW()
   - `updated_at`: TIMESTAMPTZ DEFAULT NOW()
   - Index: `idx_chat_turns_user_created` (user_id, created_at DESC)
   - Index: `idx_chat_turns_root` (root_turn_id)

4. `chat_daily_usage`:
   - `usage_date`: DATE NOT NULL
   - `user_id`: INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE
   - `new_turns_count`: INTEGER NOT NULL DEFAULT 0
   - `retries_count`: INTEGER NOT NULL DEFAULT 0
   - `created_at`: TIMESTAMPTZ DEFAULT NOW()
   - `updated_at`: TIMESTAMPTZ DEFAULT NOW()
   - PRIMARY KEY (usage_date, user_id)

5. `chat_llm_calls`:
   - `call_id`: UUID PRIMARY KEY
   - `request_id`: UUID NOT NULL REFERENCES chat_turns(request_id) ON DELETE CASCADE
   - `feature`: TEXT NOT NULL
   - `model`: TEXT NOT NULL
   - `usage_known`: BOOLEAN NOT NULL DEFAULT FALSE
   - `input_tokens`: INTEGER NOT NULL DEFAULT 0
   - `output_tokens`: INTEGER NOT NULL DEFAULT 0
   - `thinking_tokens`: INTEGER NOT NULL DEFAULT 0
   - `cached_tokens`: INTEGER NOT NULL DEFAULT 0
   - `cost_usd`: NUMERIC(10, 6)
   - `status`: TEXT NOT NULL DEFAULT 'reserved' CHECK (status IN ('reserved', 'ok', 'error', 'unknown'))
   - `latency_ms`: INTEGER
   - `created_at`: TIMESTAMPTZ DEFAULT NOW()
   - `completed_at`: TIMESTAMPTZ
   - Index: `idx_chat_llm_calls_request_id` (request_id)

## Data Access Helpers (SQLAlchemy Core parameterized SQL)
- `get_or_create_chat_thread(user_id: int) -> dict[str, Any]`
- `append_chat_message(thread_id: int, role: str, content: str, lang: str = 'en', status: str = 'ok', ...) -> int`
- `update_chat_message_content(message_id: int, content: str, status: str = 'ok', ...) -> None`
- `get_chat_message(message_id: int, user_id: int) -> dict[str, Any] | None`
- `get_chat_thread_messages(user_id: int, before_id: int | None = None, limit: int = 20) -> list[dict[str, Any]]`
- `get_chat_turn(user_id: int, request_id: UUID) -> dict[str, Any] | None`
- `update_chat_turn_status(request_id: UUID, status: str, result_message_id: int | None = None) -> None`
- `get_chat_call(call_id: UUID) -> dict[str, Any] | None`
