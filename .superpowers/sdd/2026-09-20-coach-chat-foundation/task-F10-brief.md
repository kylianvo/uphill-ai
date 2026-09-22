# Task F10 Brief: Enforce retention without resetting usage

## Objective
Implement 90-day conversation retention pruning, stale summary cleanup, and cleared turn tombstones in `backend/db.py` (`prune_coach_chat`). Create the standalone execution script in `backend/scripts/prune_coach_chat.py` and operation runbook in `docs/coach-chat-retention-runbook.md`. Verify with integration tests in `backend/tests/integration/test_chat_retention.py`.

## File Targets
- Modify: `.gitignore`
- Modify: `backend/db.py`
- Create: `backend/scripts/prune_coach_chat.py`
- Create: `docs/coach-chat-retention-runbook.md`
- Create: `backend/tests/integration/test_chat_retention.py`
- Report: `.superpowers/sdd/2026-09-20-coach-chat-foundation/task-F10-report.md`

## Specifications
1. **Pruning Method (`prune_coach_chat` in `backend/db.py`)**:
   - `prune_coach_chat(now, batch_size=500) -> dict[str, int]`:
     - Cutoff is `now - timedelta(days=settings.COACH_CHAT_RETENTION_DAYS)` (90 days).
     - Deletes expired `chat_messages` in bounded batches.
     - Resets thread summaries that reference expired/deleted messages.
     - Deletes expired `chat_turns` with `status = 'cleared'`.
     - Preserves all rows in `chat_daily_usage` and `chat_llm_calls`.
2. **CLI Runner (`backend/scripts/prune_coach_chat.py`)**:
   - Standalone CLI runner with `--batch-size` and `--dry-run` flags.
   - Loops iteratively until all expired batches are cleared.
3. **Retention & Restore Runbook (`docs/coach-chat-retention-runbook.md`)**:
   - Documents retention boundaries (90-day TTL vs content-free permanent audit ledger).
   - Documents cron scheduling.
   - Documents mandatory pre-traffic re-pruning procedure upon backup restore.
   - States cloud snapshot unknowns explicitly.
4. **Integration Tests (`test_chat_retention.py`)**:
   - 91-day expired message deletion vs 89-day retained message preservation.
   - Stale summary reset on referenced message deletion.
   - Clear preserving daily quota counters and call accounting.
   - Cleared turn UUID returning HTTP 410.
   - Account deletion cascading all child chat tables.
