"""Pure placement rules for athlete calendar edits (Coach Chat Sub-project 4a).

No DB access: services/calendar_ops.py loads a snapshot of the plan's workouts
and calls plan_changes(). Guard and warning codes are an API contract with the
frontend (it translates them) -- don't rename them.

Weeks run Monday-Sunday; week 1 starts on the Monday on or before
plans.start_date, exactly like the frontend's computeWorkoutDate. (This is
deliberately NOT db.compute_current_week, which isn't Monday-aligned.)"""

import datetime as dt
from dataclasses import dataclass
from typing import Any

from services.coach_tools.base import json_safe

DAYS: tuple[str, ...] = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
MAX_OPERATIONS = 5
HARD_ZONES = frozenset({"zone 3", "zone 4", "zone 5", "z3", "z4", "z5"})
HARD_TYPES = frozenset({"tempo", "interval", "race"})
LONG_RUN_TYPE = "long run"
VOLUME_SHIFT_THRESHOLD = 0.20
FINGERPRINT_FIELDS = (
    "id",
    "week_number",
    "day_of_week",
    "is_completed",
    "is_missed",
    "matched_activity_id",
    "approved_at",
)


class GuardViolation(Exception):
    def __init__(self, code: str, params: dict[str, Any] | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.params = params or {}


@dataclass
class ChangeSet:
    moves: list[dict[str, Any]]
    diff: list[dict[str, Any]]
    warnings: list[dict[str, Any]]
    fingerprints: dict[str, dict[str, Any]]


def resolve_today(client_today: str | None, server_today: dt.date) -> dt.date:
    if client_today:
        try:
            parsed = dt.date.fromisoformat(str(client_today)[:10])
        except ValueError:
            return server_today
        if abs((parsed - server_today).days) <= 1:
            return parsed
    return server_today


def start_monday(start_date: Any) -> dt.date | None:
    if not start_date:
        return None
    if isinstance(start_date, dt.date):
        d = start_date
    else:
        try:
            d = dt.date.fromisoformat(str(start_date)[:10])
        except ValueError:
            return None
    return d - dt.timedelta(days=d.weekday())


def workout_date(monday: dt.date, week: int, day: str) -> dt.date:
    return monday + dt.timedelta(days=(week - 1) * 7 + DAYS.index(day))


def current_week(monday: dt.date, today: dt.date) -> int:
    return (today - monday).days // 7 + 1


def fingerprint(row: dict[str, Any]) -> dict[str, Any]:
    return {f: json_safe(row.get(f)) for f in FINGERPRINT_FIELDS}


def _is_hard(row: dict[str, Any]) -> bool:
    return (row.get("target_zone") or "").strip().lower() in HARD_ZONES or (
        row.get("type") or ""
    ).strip().lower() in HARD_TYPES


def _is_long_run(row: dict[str, Any]) -> bool:
    return (row.get("type") or "").strip().lower() == LONG_RUN_TYPE


def _day_index(week: int, day: str) -> int:
    return (week - 1) * 7 + DAYS.index(day)


def _check_shape(operations: list[dict[str, Any]]) -> None:
    if not isinstance(operations, list) or not 1 <= len(operations) <= MAX_OPERATIONS:
        raise GuardViolation("INVALID_operation", {"reason": "count"})
    for i, op in enumerate(operations):
        kind = op.get("op") if isinstance(op, dict) else None
        if kind == "move":
            ok = (
                isinstance(op.get("workout_id"), int)
                and isinstance(op.get("target_week"), int)
                and op.get("target_day") in DAYS
            )
        elif kind == "swap_days":
            ok = isinstance(op.get("week"), int) and op.get("day_1") in DAYS and op.get("day_2") in DAYS
        else:
            ok = False
        if not ok:
            raise GuardViolation("INVALID_operation", {"index": i})


def _check_row(
    row: dict[str, Any],
    source: tuple[int, str],
    target: tuple[int, str],
    *,
    cross_week: bool,
    monday: dt.date | None,
    today: dt.date,
    total_weeks: int,
) -> None:
    if row.get("matched_activity_id") is not None or int(row.get("is_completed") or 0) == 1:
        raise GuardViolation("G2_history", {"workout_id": row["id"], "title": row.get("title")})
    to_week, to_day = target
    if not 1 <= to_week <= total_weeks:
        raise GuardViolation("G5_out_of_plan", {"week": to_week})
    if monday is None:
        return  # G7 plans only reach here via same-week swap_days; no dates to check
    if workout_date(monday, to_week, to_day) < today:
        raise GuardViolation("G3_past_target", {"workout_id": row["id"], "week": to_week, "day": to_day})
    if cross_week:
        cur = current_week(monday, today)
        if to_week not in (cur, cur + 1) or source[0] not in (cur - 1, cur, cur + 1):
            raise GuardViolation("G4_window", {"from_week": source[0], "to_week": to_week, "current_week": cur})


def plan_changes(
    plan: dict[str, Any],
    workouts: list[dict[str, Any]],
    operations: list[dict[str, Any]],
    today: dt.date,
) -> ChangeSet:
    """Apply `operations` in order to an in-memory copy of the plan's placement.
    Guards run per moved row against the evolving state; warnings run on the
    final state only. Raises GuardViolation; never touches the DB."""
    _check_shape(operations)
    by_id = {w["id"]: w for w in workouts}
    placement: dict[int, tuple[int, str]] = {w["id"]: (w["week_number"], w["day_of_week"]) for w in workouts}
    original = dict(placement)
    monday = start_monday(plan.get("start_date"))
    total_weeks = int(plan.get("total_weeks") or 0)
    touched: list[int] = []

    for op in operations:
        if op["op"] == "move":
            wid = op["workout_id"]
            if wid not in by_id:
                raise GuardViolation("G1_not_owner", {"workout_id": wid})
            if monday is None:
                raise GuardViolation("G7_no_dates", {})
            target = (op["target_week"], op["target_day"])
            if placement[wid] == target:
                continue
            row_moves = [(wid, target)]
            cross_week = target[0] != placement[wid][0]
        else:
            week, d1, d2 = op["week"], op["day_1"], op["day_2"]
            if d1 == d2:
                continue
            ids1 = [i for i, p in placement.items() if p == (week, d1)]
            ids2 = [i for i, p in placement.items() if p == (week, d2)]
            if not ids1 and not ids2:
                raise GuardViolation("NOTHING_to_move", {"week": week})
            row_moves = [(i, (week, d2)) for i in ids1] + [(i, (week, d1)) for i in ids2]
            cross_week = False
        for wid, target in row_moves:
            _check_row(
                by_id[wid],
                placement[wid],
                target,
                cross_week=cross_week,
                monday=monday,
                today=today,
                total_weeks=total_weeks,
            )
        for wid, target in row_moves:
            placement[wid] = target
            if wid not in touched:
                touched.append(wid)

    moved = [wid for wid in touched if placement[wid] != original[wid]]
    if not moved:
        raise GuardViolation("NOTHING_to_move", {})

    moves = [
        {
            "workout_id": wid,
            "from_week": original[wid][0],
            "from_day": original[wid][1],
            "to_week": placement[wid][0],
            "to_day": placement[wid][1],
        }
        for wid in moved
    ]
    diff = [
        {
            **m,
            "workout": json_safe(
                {**by_id[m["workout_id"]], "week_number": m["to_week"], "day_of_week": m["to_day"], "is_missed": 0}
            ),
        }
        for m in moves
    ]
    return ChangeSet(
        moves=moves,
        diff=diff,
        warnings=_warnings(by_id, original, placement, moved),
        fingerprints={str(wid): fingerprint(by_id[wid]) for wid in moved},
    )


def _warnings(
    by_id: dict[int, dict[str, Any]],
    before: dict[int, tuple[int, str]],
    after: dict[int, tuple[int, str]],
    moved: list[int],
) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    seen: set[tuple[str, int, str]] = set()

    def rows_at(index: int) -> list[dict[str, Any]]:
        return [by_id[i] for i, (w, d) in after.items() if _day_index(w, d) == index]

    def add_w1(kind: str, index: int) -> None:
        week, day = index // 7 + 1, DAYS[index % 7]
        if (kind, week, day) not in seen:
            seen.add((kind, week, day))
            warnings.append({"code": "W1_hard_stacking", "params": {"kind": kind, "week": week, "day": day}})

    for wid in moved:
        index = _day_index(*after[wid])
        same_day = rows_at(index)
        if sum(1 for r in same_day if _is_hard(r)) >= 2:
            add_w1("same_day", index)
        if _is_hard(by_id[wid]) and any(_is_long_run(r) for r in rows_at(index + 1)):
            add_w1("before_long_run", index)
        if _is_long_run(by_id[wid]) and any(_is_hard(r) for r in rows_at(index - 1)):
            add_w1("before_long_run", index - 1)

    weeks = sorted({before[w][0] for w in moved} | {after[w][0] for w in moved})
    for week in weeks:
        was = sum(float(by_id[i].get("duration_minutes") or 0) for i, p in before.items() if p[0] == week)
        now = sum(float(by_id[i].get("duration_minutes") or 0) for i, p in after.items() if p[0] == week)
        if was > 0 and abs(now - was) / was > VOLUME_SHIFT_THRESHOLD:
            warnings.append(
                {
                    "code": "W2_volume_shift",
                    "params": {"week": week, "before_minutes": round(was), "after_minutes": round(now)},
                }
            )

    for wid in moved:
        if by_id[wid].get("approved_at") is None:
            warnings.append(
                {"code": "W3_pending_draft", "params": {"workout_id": wid, "title": by_id[wid].get("title")}}
            )
    return warnings
