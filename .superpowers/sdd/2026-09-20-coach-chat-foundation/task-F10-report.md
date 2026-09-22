# Task F10 Report: Enforce retention without resetting usage

## Summary
Task F10 implements 90-day conversation retention enforcement, bounded batch pruning of expired messages, stale summary resets, and cleared turn tombstones in `backend/db.py` (`prune_coach_chat`). It creates the standalone runner script in `backend/scripts/prune_coach_chat.py`, publishes the comprehensive operational runbook in `docs/coach-chat-retention-runbook.md`, and validates retention invariants with integration tests in `backend/tests/integration/test_chat_retention.py`.

## Components & Contracts Implemented
1. **Retention Pruning Engine (`db.py:prune_coach_chat`)**:
   - Computes cutoff dynamically from `settings.COACH_CHAT_RETENTION_DAYS` (90 days).
   - Deletes expired `chat_messages` in bounded batches (`batch_size`).
   - Resets summaries on `chat_threads` whose `summarized_through_id` points to a deleted message.
   - Deletes expired cleared `chat_turns` tombstones.
   - Never deletes rows from `chat_daily_usage` or `chat_llm_calls` (accounting ledgers remain intact).
2. **CLI Runner (`backend/scripts/prune_coach_chat.py`)**:
   - Supports `--batch-size` (default 500) and `--dry-run`.
   - Iterates in chunks until all expired rows are cleaned.
   - Logs execution results with ISO timestamps.
3. **Operations Runbook (`docs/coach-chat-retention-runbook.md`)**:
   - Establishes the 90-day content boundary vs content-free accounting ledger invariants.
   - Documents host crontab and manual execution instructions.
   - Details mandatory pre-traffic re-pruning procedure when restoring backups.
   - Explicitly states unknown cloud snapshot infrastructure details.
4. **Integration Test Suite (`tests/integration/test_chat_retention.py`)**:
   - `test_retention_prune_deletes_91_day_messages_and_keeps_89_day`: Validates exact 90-day cutoff boundary.
   - `test_retention_prune_clears_expired_summaries`: Validates dangling summary reset.
   - `test_clear_preserves_counters_and_calls`: Validates that clearing conversation does not reset daily turn quotas or LLM call audit records.
   - `test_cleared_uuid_returns_410`: Validates HTTP 410 Gone for cleared turn requests.
   - `test_account_deletion_cascades_chat_tables`: Validates `ON DELETE CASCADE` across `chat_threads`, `chat_messages`, `chat_turns`, and `chat_llm_calls`.

## Files Touched
- Modified: `.gitignore`
- Modified: `backend/db.py`
- Created: `backend/scripts/prune_coach_chat.py`
- Created: `docs/coach-chat-retention-runbook.md`
- Created: `backend/tests/integration/test_chat_retention.py`
- Created: `.superpowers/sdd/2026-09-20-coach-chat-foundation/task-F10-brief.md`
- Created: `.superpowers/sdd/2026-09-20-coach-chat-foundation/task-F10-report.md`
