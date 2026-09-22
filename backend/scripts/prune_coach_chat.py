"""CLI script to idempotently prune expired Coach Chat messages, summaries, and tombstones."""

import argparse
import sys
from datetime import UTC, datetime

import db
from log_utils import get_logger

logger = get_logger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description="Prune expired Coach Chat conversation data (> 90 days)")
    parser.add_argument("--batch-size", type=int, default=500, help="Batch size for deletions (default: 500)")
    parser.add_argument("--dry-run", action="store_true", help="Report counts without deleting")
    args = parser.parse_args()

    now = datetime.now(UTC)
    total_deleted_msgs = 0
    total_cleared_summaries = 0
    total_deleted_turns = 0

    print(f"[{now.isoformat()}] Starting Coach Chat retention pruning (batch_size={args.batch_size}, dry_run={args.dry_run})...")

    if args.dry_run:
        print("[DRY-RUN] Dry run mode enabled. No records will be modified.")
        return 0

    while True:
        stats = db.prune_coach_chat(now=now, batch_size=args.batch_size)
        msgs = stats.get("deleted_messages", 0)
        sums = stats.get("cleared_summaries", 0)
        turns = stats.get("deleted_turns", 0)

        total_deleted_msgs += msgs
        total_cleared_summaries += sums
        total_deleted_turns += turns

        if msgs < args.batch_size and turns < args.batch_size:
            break

    print(
        f"Pruning complete:\n"
        f"  - Deleted expired messages: {total_deleted_msgs}\n"
        f"  - Reset stale thread summaries: {total_cleared_summaries}\n"
        f"  - Deleted cleared turn tombstones: {total_deleted_turns}\n"
        f"  - Quotas and LLM call ledger preserved intact."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
