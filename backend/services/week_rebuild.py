"""Week rebuild (Coach Chat Sub-project 4b).

Regenerates the rest of one plan week. Two callers share everything here:
the Scheduler's adapt-week (writes directly -- the form submit is the
confirmation) and the chat tool propose_rebuild_week (drafts in the
background, the athlete taps Apply). The pure rules come first: which days
are kept (past days, completed, GPS-matched), the diff and the warnings."""

import datetime as dt
from dataclasses import dataclass
from typing import Any

from services.calendar_rules import (
    DAYS,
    FINGERPRINT_FIELDS,
    VOLUME_SHIFT_THRESHOLD,
    GuardViolation,
    _is_hard,
    _is_long_run,
    current_week,
    start_monday,
)
from services.coach_tools.base import json_safe

# Whole-week staleness: 4a's placement fields plus the content an edit changes.
REBUILD_FINGERPRINT_FIELDS = FINGERPRINT_FIELDS + ("title", "type", "duration_minutes", "session_slot")


@dataclass(frozen=True)
class RebuildRange:
    week: int
    from_day: str
    kept_ids: tuple[int, ...]
    replaceable_ids: tuple[int, ...]
    kept_slots: frozenset[tuple[str, str]]


def _day_idx(day: Any) -> int:
    return DAYS.index(day) if day in DAYS else len(DAYS)


def _slot(row: dict[str, Any]) -> str:
    return row.get("session_slot") or "main"


def _is_history(row: dict[str, Any]) -> bool:
    return row.get("matched_activity_id") is not None or int(row.get("is_completed") or 0) == 1


def rebuild_range(plan: dict[str, Any], workouts: list[dict[str, Any]], week: int, today: dt.date) -> RebuildRange:
    """Which workouts of `week` a rebuild may replace. A plan without a
    start_date has no calendar, so it rebuilds from Monday keeping only
    history (the chat caller refuses G7 before getting here)."""
    total_weeks = int(plan.get("total_weeks") or 0)
    generated = max((int(w["week_number"]) for w in workouts), default=0)
    if not 1 <= week <= total_weeks or week > generated:
        raise GuardViolation("G5_out_of_plan", {"week": week})
    from_idx = 0
    monday = start_monday(plan.get("start_date"))
    if monday is not None:
        cur = current_week(monday, today)
        if week < cur:
            raise GuardViolation("G3_past_target", {"week": week})
        if week == cur:
            from_idx = today.weekday()
    rows = [w for w in workouts if int(w["week_number"]) == week]
    kept = [w for w in rows if _day_idx(w["day_of_week"]) < from_idx or _is_history(w)]
    kept_ids = {w["id"] for w in kept}
    replaceable = [w for w in rows if w["id"] not in kept_ids]
    kept_days = {w["day_of_week"] for w in kept}
    if not replaceable and all(d in kept_days for d in DAYS[from_idx:]):
        raise GuardViolation("NOTHING_to_rebuild", {"week": week})
    return RebuildRange(
        week=week,
        from_day=DAYS[from_idx],
        kept_ids=tuple(sorted(kept_ids)),
        replaceable_ids=tuple(sorted(w["id"] for w in replaceable)),
        kept_slots=frozenset((w["day_of_week"], _slot(w)) for w in kept),
    )


def week_fingerprints(workouts: list[dict[str, Any]], week: int) -> dict[str, dict[str, Any]]:
    return {
        str(w["id"]): {f: json_safe(w.get(f)) for f in REBUILD_FINGERPRINT_FIELDS}
        for w in workouts
        if int(w["week_number"]) == week
    }


def filter_draft(draft: list[dict[str, Any]], rng: RebuildRange) -> list[dict[str, Any]]:
    """Generated workouts that may be written: the target week only, from
    `from_day` on, never onto a kept (day, slot)."""
    from_idx = DAYS.index(rng.from_day)
    out = []
    for wo in draft:
        if int(wo.get("week_number") or 0) != rng.week or _day_idx(wo.get("day_of_week")) < from_idx:
            continue
        if _day_idx(wo.get("day_of_week")) >= len(DAYS):
            continue
        if (wo["day_of_week"], _slot(wo)) in rng.kept_slots:
            continue
        out.append({**wo, "week_number": rng.week})
    return out


def _brief(row: dict[str, Any]) -> dict[str, Any]:
    return json_safe(
        {
            "id": row.get("id"),
            "title": row.get("title"),
            "type": row.get("type"),
            "duration_minutes": row.get("duration_minutes"),
            "distance_km": row.get("distance_km"),
            "elevation_gain_m": row.get("elevation_gain_m"),
            "session_slot": _slot(row),
            "target_zone": row.get("target_zone"),
        }
    )


def _totals(rows: list[dict[str, Any]]) -> dict[str, float]:
    return {
        "min": round(sum(float(r.get("duration_minutes") or 0) for r in rows)),
        "km": round(sum(float(r.get("distance_km") or 0) for r in rows), 1),
        "vert": round(sum(float(r.get("elevation_gain_m") or 0) for r in rows)),
    }


def _week_after(workouts: list[dict[str, Any]], rng: RebuildRange, draft: list[dict[str, Any]]) -> list[dict[str, Any]]:
    kept = [w for w in workouts if w["id"] in set(rng.kept_ids)]
    return kept + draft


def build_diff(workouts: list[dict[str, Any]], rng: RebuildRange, draft: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [w for w in workouts if int(w["week_number"]) == rng.week]
    kept, replaceable = set(rng.kept_ids), set(rng.replaceable_ids)
    days = [
        {
            "day": d,
            "kept": [_brief(w) for w in rows if w["id"] in kept and w["day_of_week"] == d],
            "before": [_brief(w) for w in rows if w["id"] in replaceable and w["day_of_week"] == d],
            "after": [json_safe(wo) for wo in draft if wo["day_of_week"] == d],
        }
        for d in DAYS
    ]
    return {
        "week": rng.week,
        "from_day": rng.from_day,
        "days": days,
        "totals": {"before": _totals(rows), "after": _totals(_week_after(rows, rng, draft))},
    }


def rebuild_warnings(
    workouts: list[dict[str, Any]], rng: RebuildRange, draft: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """W1 on the rebuilt days (and the kept day just before them); W2 on the
    week total. No W3: rebuilt workouts are inserted approved."""
    rows = [w for w in workouts if int(w["week_number"]) == rng.week]
    after = _week_after(rows, rng, draft)
    by_idx = {i: [r for r in after if _day_idx(r["day_of_week"]) == i] for i in range(len(DAYS))}
    warnings: list[dict[str, Any]] = []
    from_idx = DAYS.index(rng.from_day)
    for i in range(max(0, from_idx - 1), len(DAYS)):
        if i >= from_idx and sum(1 for r in by_idx[i] if _is_hard(r)) >= 2:
            warnings.append(
                {"code": "W1_hard_stacking", "params": {"kind": "same_day", "week": rng.week, "day": DAYS[i]}}
            )
        if i + 1 < len(DAYS) and any(_is_hard(r) for r in by_idx[i]) and any(_is_long_run(r) for r in by_idx[i + 1]):
            warnings.append(
                {"code": "W1_hard_stacking", "params": {"kind": "before_long_run", "week": rng.week, "day": DAYS[i]}}
            )
    was = sum(float(r.get("duration_minutes") or 0) for r in rows)
    now = sum(float(r.get("duration_minutes") or 0) for r in after)
    if was > 0 and abs(now - was) / was > VOLUME_SHIFT_THRESHOLD:
        warnings.append(
            {
                "code": "W2_volume_shift",
                "params": {"week": rng.week, "before_minutes": round(was), "after_minutes": round(now)},
            }
        )
    return warnings
