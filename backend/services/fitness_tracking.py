"""Weekly aerobic-speed checkpoints for a plan, and the B/A path status read from them."""

from datetime import date, datetime, timedelta
from typing import Any

import db
import telemetry
from log_utils import get_logger
from services import aerobic_speed

_logger = get_logger(__name__)


def refresh(
    plan: dict[str, Any], user: dict[str, Any] | None, today: date | None = None
) -> aerobic_speed.PathStatus | None:
    """Recompute the plan's weekly points from synced runs, store them, and return the path status.
    None when the athlete has no AeT heart rate, no plan start, or too little history. Never raises."""
    today = today or date.today()
    try:
        aet = (user or {}).get("aet_hr")
        if not aet or not plan.get("start_date"):
            return None
        monday = aerobic_speed.plan_monday(plan["start_date"])
        through = (today - monday).days // 7 + 1
        since = datetime.combine(monday, datetime.min.time())
        until = datetime.combine(today + timedelta(days=1), datetime.min.time())
        activities = db.get_activities_for_pace(plan["user_id"], since, until)
        points = aerobic_speed.weekly_points(activities, float(aet), monday, through)
        for p in points:
            db.upsert_fitness_checkpoint(plan["id"], p.week, p.pace_min_km, p.n)
        status = aerobic_speed.path(points, int(plan.get("total_weeks") or 0))
        if status:
            telemetry.aerobic_path_total.labels(b=status.b, a=status.a, confidence=status.confidence).inc()
        return status
    except Exception:
        _logger.exception("fitness tracking failed", extra={"fields": {"plan_id": plan.get("id")}})
        return None


def path_payload(status: aerobic_speed.PathStatus | None) -> dict[str, Any] | None:
    return None if status is None else {**status.__dict__}
