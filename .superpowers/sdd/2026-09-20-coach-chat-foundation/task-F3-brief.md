# Task F3 Brief: Enforce cross-worker admission, deduplication, and quotas

## Objective
Implement durable cross-worker turn admission, PostgreSQL session advisory locking, canonical SHA-256 fingerprint deduplication, and daily/retry quota enforcement in `backend/db.py`, exposed through typed domain errors and configuration defaults in `backend/config.py`, `deploy.env.example`, and `CLAUDE.md`.

## File Targets
- Modify: `backend/db.py`
- Modify: `backend/config.py`
- Modify: `deploy.env.example`
- Modify: `CLAUDE.md`
- Create: `backend/tests/integration/test_chat_admission.py`
- Report: `.superpowers/sdd/2026-09-20-coach-chat-foundation/task-F3-report.md`

## Specifications
1. **Advisory Locking**:
   - `chat_turn_lock(user_id: int)`: context manager checking out a dedicated connection from `engine.connect()`.
   - Uses `pg_try_advisory_lock(CHAT_ADVISORY_NAMESPACE, user_id)`.
   - If False, raises `ChatInProgressError` (`error_code="chat_in_progress"`).
   - If True, yields the connection.
   - On exit or exception, executes `pg_advisory_unlock` and closes the connection. If connection is dropped/closed unexpectedly, PostgreSQL automatically releases session advisory locks.

2. **Fingerprinting**:
   - `compute_chat_fingerprint(message: str | None, retry_of: UUID | str | None, lang: str = "en", is_legacy: bool = False) -> str`:
   - Normalizes message (NFC unicode, stripped) or retry_of (stringified).
   - Normalizes language (`lang.lower().strip()`).
   - Computes deterministic SHA-256 hex digest. Never exported to telemetry.

3. **Quota & Deduplication Admission**:
   - `admit_chat_turn(user_id: int, request_id: UUID | str, thread_id: int | None, message: str | None = None, retry_of: UUID | str | None = None, lang: str = "en", is_legacy: bool = False, now: datetime | None = None) -> AdmissionResult`:
   - Same `request_id` + same `fingerprint` -> REPLAY (returns `{"kind": "replay", "turn": turn, "message": result_message}`).
   - Same `request_id` + different `fingerprint` -> CONFLICT (`ChatRequestConflictError`, `error_code="request_conflict"`).
   - If `retry_of`:
     - Must be owned by `user_id`.
     - Target turn status must be `error` or `interrupted` (or `nothing_to_retry` if status is `ok` or not found).
     - Target turn retry count under root must be < 2 (`COACH_CHAT_MAX_RETRIES_PER_ROOT = 2`); otherwise `ChatRetryLimitError` (`error_code="chat_retry_limit"`).
     - User's UTC date `retries_count` must be < 10 (`COACH_CHAT_DAILY_RETRIES_LIMIT = 10`); otherwise `ChatRetryLimitError` (`error_code="chat_retry_limit"`).
     - Increments `retries_count` atomically on `chat_daily_usage`.
     - Inserts new turn with `root_turn_id = root_id`, `attempt_number = prev_attempt + 1`.
   - If new turn (`message` provided):
     - User's UTC date `new_turns_count` must be < 50 (`COACH_CHAT_DAILY_NEW_TURNS_LIMIT = 50`); otherwise `ChatDailyLimitError` (`error_code="chat_daily_limit"`).
     - Increments `new_turns_count` atomically on `chat_daily_usage`.
     - Inserts new turn with `status="active"`.

4. **Configuration Defaults**:
   - `COACH_CHAT_DAILY_NEW_TURNS_LIMIT`: 50
   - `COACH_CHAT_DAILY_RETRIES_LIMIT`: 10
   - `COACH_CHAT_MAX_RETRIES_PER_ROOT`: 2
   - `COACH_CHAT_TURN_TIMEOUT_SECONDS`: 45
   - `COACH_CHAT_SUMMARY_TIMEOUT_SECONDS`: 10
