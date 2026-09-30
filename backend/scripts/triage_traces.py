"""Route low-quality traces into the Langfuse "uphill-triage" annotation queue.

  python scripts/triage_traces.py [--days 7] [--dry-run]

Flags a trace when any score in RULES below landed on it in the window (chat thumbs and
judge scores, plan fallbacks/rework/checks/compliance, missed goals, gear/nutrition
catalog and brand misses).
Already-queued traces are skipped. Langfuse holds no content (LANGFUSE_EXPORT_CONTENT=false),
so for coach turns the script also prints the chat message id stored with each trace id:
look the reply up in the database, and if the verdict is needs_fixture write a *synthetic*
look-alike case in tests/golden/ -- never copy the athlete's words.
"""

import argparse
import os
import sys
from datetime import UTC, datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

QUEUE_NAME = "uphill-triage"
# (score name, filter for GET /api/public/v3/scores, human-readable reason)
RULES = [
    ("thumbs", {"data_type": "NUMERIC", "value_max": -0.5}, "thumbs down"),
    ("judge_safe", {"data_type": "NUMERIC", "value_max": 0.74}, "judge_safe < 0.75"),
    ("judge_grounded", {"data_type": "NUMERIC", "value_max": 0.49}, "judge_grounded < 0.5"),
    ("plan_engine", {"data_type": "CATEGORICAL", "value": "rules"}, "rule-based plan fallback"),
    ("plan_reworked", {"data_type": "NUMERIC", "value_min": 0.5}, "plan regenerated within 72 h"),
    ("plan_checks", {"data_type": "NUMERIC", "value_max": 0.66}, "plan failed a quality check"),
    ("block_compliance", {"data_type": "NUMERIC", "value_max": 0.49}, "athlete completed < 50% of the block"),
    ("goal_hit", {"data_type": "NUMERIC", "value_max": 0.5}, "race finish outside the A..C range"),
    ("catalog_valid", {"data_type": "NUMERIC", "value_max": 0.5}, "recommended an uncatalogued product"),
    ("brand_respected", {"data_type": "NUMERIC", "value_max": 0.5}, "ignored the preferred brands"),
]


def _all_pages(fetch):
    page = 1
    while True:
        res = fetch(page)
        yield from res.data
        if page >= res.meta.total_pages:
            return
        page += 1


def _scores_v3(api, **filters):
    cursor = None
    while True:
        # The subject (which trace a score belongs to) is only returned when requested.
        res = api.scores_v3.get_many_v3(limit=100, cursor=cursor, fields="core,subject", **filters)
        yield from res.data
        cursor = res.meta.cursor
        if not cursor:
            return


def flagged_traces(api, since: datetime, environment: str | None = None) -> dict[str, list[str]]:
    """trace_id -> reasons, from the scores written since `since`."""
    flagged: dict[str, list[str]] = {}
    for name, filters, reason in RULES:
        env = {"environment": environment} if environment else {}
        for score in _scores_v3(api, name=name, from_timestamp=since, **env, **filters):
            if getattr(score.subject, "kind", None) == "trace":
                flagged.setdefault(score.subject.id, []).append(reason)
    return flagged


def queued_trace_ids(api, queue_id: str) -> set[str]:
    items = _all_pages(lambda p: api.annotation_queues.list_queue_items(queue_id, page=p, limit=100))
    return {i.object_id for i in items}


def message_ids_for(trace_ids: list[str]) -> dict[str, int]:
    """Chat message ids for coach-turn traces (empty when no database is reachable)."""
    try:
        from sqlalchemy import text

        import db

        with db.engine.connect() as conn:
            rows = conn.execute(
                text("SELECT trace_id, id FROM chat_messages WHERE trace_id = ANY(:ids)"), {"ids": trace_ids}
            ).fetchall()
        return {r[0]: r[1] for r in rows}
    except Exception as exc:
        print(f"[triage] message lookup skipped: {type(exc).__name__}")
        return {}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--environment",
        default="production",
        help="Langfuse environment to triage (experiments run in test/development)",
    )
    args = parser.parse_args()

    from services import observability

    observability.init()
    api = observability.langfuse_api()
    if api is None:
        sys.exit("Langfuse is not configured (LANGFUSE_PUBLIC_KEY/SECRET_KEY/OBSERVABILITY_ID_SALT).")
    queue = next(
        (q for q in _all_pages(lambda p: api.annotation_queues.list_queues(page=p)) if q.name == QUEUE_NAME), None
    )
    if queue is None:
        sys.exit(f"Annotation queue {QUEUE_NAME!r} not found in this Langfuse project.")

    since = datetime.now(UTC) - timedelta(days=args.days)
    flagged = flagged_traces(api, since, args.environment)
    new = {t: r for t, r in flagged.items() if t not in queued_trace_ids(api, queue.id)}
    messages = message_ids_for(list(new))

    for trace_id, reasons in new.items():
        msg = f" chat_message={messages[trace_id]}" if trace_id in messages else ""
        print(f"[triage] {trace_id}{msg}: {', '.join(reasons)}")
        if not args.dry_run:
            api.annotation_queues.create_queue_item(queue.id, object_id=trace_id, object_type="TRACE")
    print(
        f"[triage] {len(new)} new of {len(flagged)} flagged in the last {args.days} days"
        + (" (dry run)" if args.dry_run else "")
    )


if __name__ == "__main__":
    main()
