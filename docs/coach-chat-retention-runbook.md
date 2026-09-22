# Coach Chat Content Retention and Backup Restore Runbook

## Overview & Retention Invariants

Uphill AI enforces a strict **90-day retention boundary** for all athlete conversation content:

1. **Content Tables (90-day TTL)**:
   - `chat_messages`: Athlete messages and coach responses expire after 90 days (`COACH_CHAT_RETENTION_DAYS=90`).
   - `chat_threads`: Retained thread summaries and pointer (`summarized_through_id`) are cleared when their referenced messages expire.
   - `chat_turns`: Cleared request tombstones expire after 90 days.
   - Dynamic context filtering in `services/coach_context.py` excludes any message older than 90 days from prompt assembly and model history even before physical database cleanup.

2. **Accounting Ledger (Content-Free & Non-Expiring)**:
   - `chat_daily_usage`: Daily per-athlete turn and retry counts are content-free numerical counters. They are NOT pruned by conversation cleanup.
   - `chat_llm_calls`: Bounded per-invocation metadata (call UUID, model, tokens, cost, latency) is a financial audit ledger containing zero athlete text or prompt content. It is NOT pruned by conversation cleanup.

3. **Cascading Deletion**:
   - If an athlete account is deleted, foreign keys with `ON DELETE CASCADE` instantly delete all associated `chat_threads`, `chat_messages`, `chat_turns`, and `chat_llm_calls`.

---

## Scheduled Pruning Job

Retention cleanup runs idempotently via CLI script `backend/scripts/prune_coach_chat.py`.

### Crontab Schedule
On the host running the backend Docker container or host cron:
```bash
# Run daily at 03:00 UTC
0 3 * * * cd /opt/uphill-ai-backend && python scripts/prune_coach_chat.py --batch-size 500 >> /var/log/uphill-prune.log 2>&1
```

### Manual Execution
```bash
cd backend
python scripts/prune_coach_chat.py --batch-size 500

# Dry-run inspection
python scripts/prune_coach_chat.py --dry-run
```

---

## Database Backup & Restore Procedure

### The Retention Risk
PostgreSQL database backups (`pg_dump` or filesystem volume snapshots) capture point-in-time states. If a 60-day-old backup is restored 40 days later, messages that were 60 days old at backup time are now 100 days old in real time.

### Mandatory Pre-Traffic Re-Pruning Procedure
Whenever restoring a database backup to staging or production:

1. **Restore database dump** into PostgreSQL.
2. **DO NOT start or expose the web API container yet.**
3. **Execute the retention pruner immediately**:
   ```bash
   python backend/scripts/prune_coach_chat.py --batch-size 1000
   ```
4. **Verify zero expired messages remain**:
   ```sql
   SELECT COUNT(*) FROM chat_messages WHERE created_at < NOW() - INTERVAL '90 days';
   ```
   Must return `0`.
5. **Start backend API containers and open traffic.**

---

## Stated Unknowns Before Invited Beta

1. **Cloud Snapshot Window**: Exact retention period of automated cloud/VPS disk snapshots at the hosting provider is managed at the infrastructure layer.
2. **Cold Offsite Storage**: If offsite S3/GCS database dump archiving is enabled in the future, dumps older than 90 days must be encrypted at rest and destroyed according to organizational data retention schedules.
