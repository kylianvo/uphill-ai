"""Apply/Discard for Coach Chat schedule proposals. The Apply button is the
only confirmation: this re-validates everything at apply time under row locks
(proposal row, then the plan's workout rows), is idempotent (a duplicate Apply
returns the stored result), and marks a proposal `stale` -- writing nothing --
when a guard now fails or a touched workout changed since it was proposed."""

from typing import Any

import db
from services import calendar_ops
from services.calendar_rules import GuardViolation, resolve_today


def apply_proposal(user_id: int, proposal_id: int, client_today: str | None) -> tuple[int, dict[str, Any]]:
    """Returns (http_status, body). body carries `plan_id` for 200s so the router
    can attach the refreshed workouts; the router strips it."""
    today = resolve_today(client_today, calendar_ops.server_today())
    with db.engine.begin() as conn:
        row = db.lock_chat_proposal(conn, proposal_id, user_id)
        if row is None:
            return 404, {"detail": "Proposal not found."}
        if row["status"] == "applied":
            return 200, {"status": "applied", "result": row["result"], "plan_id": row["plan_id"]}
        if row["status"] != "proposed":
            return 409, {"status": row["status"], "stale_reason": row["stale_reason"]}
        savepoint = conn.begin_nested()
        try:
            changes = calendar_ops.apply(
                user_id,
                row["plan_id"],
                row["operations"],
                today,
                agent=True,
                expected_fingerprints=row["fingerprints"],
                conn=conn,
            )
        except GuardViolation as gv:
            savepoint.rollback()
            db.resolve_chat_proposal(conn, proposal_id, status="stale", stale_reason=gv.code)
            return 409, {"status": "stale", "stale_reason": gv.code}
        savepoint.commit()
        result = {"moves": changes.moves, "warnings": changes.warnings}
        db.resolve_chat_proposal(conn, proposal_id, status="applied", result=result)
        return 200, {"status": "applied", "result": result, "plan_id": row["plan_id"]}


def discard_proposal(user_id: int, proposal_id: int) -> tuple[int, dict[str, Any]]:
    status = db.discard_chat_proposal(proposal_id, user_id)
    if status is None:
        return 404, {"detail": "Proposal not found."}
    return 200, {"status": status}
