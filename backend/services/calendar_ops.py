"""Guarded athlete calendar edits -- the single write path for workout
placement, shared by the Scheduler (manual) and Coach Chat proposals (agent).

Rules live in services/calendar_rules.py (pure); this module adds the access
checks that need the DB (G1 active plan, G6 coach link) and the transaction:
it locks the plan's workout rows, re-runs the rules against that locked
snapshot, compares fingerprints when a proposal is being applied, and writes."""

import datetime as dt
from typing import Any

import db
from services.calendar_rules import ChangeSet, GuardViolation, plan_changes


def server_today() -> dt.date:
    return dt.datetime.now(dt.UTC).date()


def _check_access(user_id: int, plan_id: int, *, agent: bool) -> dict[str, Any]:
    plan = db.get_active_plan(user_id)
    if not plan or plan["id"] != plan_id:
        raise GuardViolation("G1_not_owner", {"plan_id": plan_id})
    if agent and db.get_active_coach_link_for_athlete(user_id):
        raise GuardViolation("G6_coach_linked", {})
    return plan


def check_agent_access(user_id: int, plan_id: int) -> dict[str, Any]:
    """G1 + G6 for agent writes that don't go through preview/apply (week rebuilds)."""
    return _check_access(user_id, plan_id, agent=True)


def preview(user_id: int, plan_id: int, operations: list[dict[str, Any]], today: dt.date, *, agent: bool) -> ChangeSet:
    plan = _check_access(user_id, plan_id, agent=agent)
    with db.engine.connect() as conn:
        rows = db.get_plan_workouts_for_placement(conn, plan_id, lock=False)
    return plan_changes(plan, rows, operations, today)


def apply(
    user_id: int,
    plan_id: int,
    operations: list[dict[str, Any]],
    today: dt.date,
    *,
    agent: bool,
    expected_fingerprints: dict[str, Any] | None = None,
    conn=None,
) -> ChangeSet:
    plan = _check_access(user_id, plan_id, agent=agent)
    if conn is not None:
        return _apply_in(conn, plan, operations, today, expected_fingerprints)
    with db.engine.begin() as own:
        return _apply_in(own, plan, operations, today, expected_fingerprints)


def _apply_in(
    conn,
    plan: dict[str, Any],
    operations: list[dict[str, Any]],
    today: dt.date,
    expected_fingerprints: dict[str, Any] | None,
) -> ChangeSet:
    rows = db.get_plan_workouts_for_placement(conn, plan["id"], lock=True)
    changes = plan_changes(plan, rows, operations, today)
    if expected_fingerprints is not None and changes.fingerprints != expected_fingerprints:
        raise GuardViolation("STALE_changed", {})
    db.apply_workout_moves(conn, changes.moves)
    return changes
