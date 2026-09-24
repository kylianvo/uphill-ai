"""Apply/Discard for Coach Chat proposals -- schedule moves (4a) and week rebuilds (4b).
The Apply button is the only confirmation: this re-validates everything at apply time
under row locks (proposal row, then the plan's workout rows), is idempotent (a duplicate
Apply returns the stored result), and marks a proposal `stale` -- writing nothing --
when a guard now fails or a touched workout changed since it was proposed."""

from typing import Any

import db
from services import calendar_ops
from services.calendar_rules import GuardViolation, resolve_today


def apply_proposal(user_id: int, proposal_id: int, client_today: str | None) -> tuple[int, dict[str, Any]]:
    """Returns (http_status, body). body carries `plan_id` for 200s so the router
    can attach the refreshed workouts; the router strips it."""
    # Imported lazily: week_rebuild pulls in the plan generator stack, which 4a
    # schedule moves never need.
    from services import week_rebuild

    today = resolve_today(client_today, calendar_ops.server_today())
    db.expire_orphaned_rebuilds(user_id)
    with db.engine.begin() as conn:
        row = db.lock_chat_proposal(conn, proposal_id, user_id)
        if row is None:
            return 404, {"detail": "Proposal not found."}
        if row["status"] == "applied":
            return 200, {"status": "applied", "result": row["result"], "plan_id": row["plan_id"]}
        if row["kind"] == "rebuild" and row["status"] in ("generating", "failed"):
            return 409, {"status": row["status"], "code": "NOT_ready", "stale_reason": row["stale_reason"]}
        if row["status"] != "proposed":
            return 409, {"status": row["status"], "stale_reason": row["stale_reason"]}
        savepoint = conn.begin_nested()
        try:
            if row["kind"] == "rebuild":
                result = week_rebuild.apply_rebuild(user_id, row, today, conn)
            else:
                changes = calendar_ops.apply(
                    user_id,
                    row["plan_id"],
                    row["operations"],
                    today,
                    agent=True,
                    expected_fingerprints=row["fingerprints"],
                    conn=conn,
                )
                result = {"moves": changes.moves, "warnings": changes.warnings}
        except GuardViolation as gv:
            savepoint.rollback()
            db.resolve_chat_proposal(conn, proposal_id, status="stale", stale_reason=gv.code)
            return 409, {"status": "stale", "stale_reason": gv.code}
        savepoint.commit()
        db.resolve_chat_proposal(conn, proposal_id, status="applied", result=result)
    if row["kind"] == "rebuild":
        db.set_plan_athlete_tier(row["plan_id"], (row.get("draft") or {}).get("resolved_tier"))
    return 200, {"status": "applied", "result": result, "plan_id": row["plan_id"]}


def discard_proposal(user_id: int, proposal_id: int) -> tuple[int, dict[str, Any]]:
    status = db.discard_chat_proposal(proposal_id, user_id)
    if status is None:
        return 404, {"detail": "Proposal not found."}
    return 200, {"status": status}
