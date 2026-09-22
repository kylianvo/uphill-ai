# Task F3 Report: Enforce cross-worker admission, deduplication, and quotas

## Summary
Task F3 implements durable cross-worker turn admission, PostgreSQL session advisory locking via dedicated checked-out connections, canonical SHA-256 fingerprint deduplication, and athlete daily/retry quota enforcement in `backend/db.py`. Configuration defaults and documentation are added to `backend/config.py`, `deploy.env.example`, and `CLAUDE.md`. Integration tests in `backend/tests/integration/test_chat_admission.py` verify all locking contention, release on disconnect, replay, conflict, daily new turn quotas (50), daily retry quotas (10), root retry limits (2), and UTC rollover semantics.

## Components & Contracts Implemented
1. **Advisory Locking**:
   - Constant `CHAT_ADVISORY_NAMESPACE = 0x43484154` (ASCII 'CHAT').
   - `chat_turn_lock(user_id: int)` context manager checking out a dedicated connection from `engine.connect()`.
   - Acquires `pg_try_advisory_lock` non-blocking. If locked by another worker, raises typed `ChatInProgressError` (`error_code="chat_in_progress"`).
   - In `finally`, explicitly executes `pg_advisory_unlock` and closes the connection. If the connection drops or is closed, PostgreSQL automatically releases session advisory locks.
2. **Deterministic Fingerprinting**:
   - `compute_chat_fingerprint(message, retry_of, lang, is_legacy)`:
   - NFC unicode normalization and whitespace stripping for message.
   - String normalization for retry UUID and lowercase language.
   - Computes deterministic SHA-256 hex digest. Content is never exported to telemetry.
3. **Admission & Quota Enforcement**:
   - `admit_chat_turn(user_id, request_id, thread_id, message, retry_of, lang, is_legacy, now)`:
   - Replay: Same `request_id` + identical fingerprint returns replay dictionary without deducting quota or re-inserting turns.
   - Conflict: Same `request_id` + different fingerprint raises `ChatRequestConflictError` (`error_code="request_conflict"`).
   - Retry: Validates target turn ownership, failure status (`error` or `interrupted`), root retry count (< 2), and daily retry quota (< 10). Atomically increments `retries_count` in `chat_daily_usage` and inserts child turn linked to `root_turn_id`.
   - New turn: Validates daily new turn quota (< 50). Atomically increments `new_turns_count` in `chat_daily_usage` and inserts new turn with `status="active"`.
4. **Configuration & Documentation**:
   - `COACH_CHAT_DAILY_NEW_TURNS_LIMIT = 50`
   - `COACH_CHAT_DAILY_RETRIES_LIMIT = 10`
   - `COACH_CHAT_MAX_RETRIES_PER_ROOT = 2`
   - `COACH_CHAT_TURN_TIMEOUT_SECONDS = 45`
   - `COACH_CHAT_SUMMARY_TIMEOUT_SECONDS = 10`
   - `COACH_CHAT_RETENTION_DAYS = 90`
   - `COACH_CHAT_MAX_INPUT_CHARS = 2000`
   - Added to `backend/config.py`, `deploy.env.example`, and `CLAUDE.md`.

## Files Touched
- Modified: `backend/db.py`
- Modified: `backend/config.py`
- Modified: `deploy.env.example`
- Modified: `CLAUDE.md`
- Created: `backend/tests/integration/test_chat_admission.py`
- Created: `.superpowers/sdd/2026-09-20-coach-chat-foundation/task-F3-brief.md`
- Created: `.superpowers/sdd/2026-09-20-coach-chat-foundation/task-F3-report.md`
