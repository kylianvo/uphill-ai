"""Garmin push payloads in, canonical dataclasses out. Pure: no I/O.

Garmin pushes each summary type under its own top-level key. Activity summaries
(`activities`, `manuallyUpdatedActivities`) are flat; `activityDetails` nests the
same fields under `summary`. Either one alone is enough to store the activity, and
both carry `activityId`, so the two converge on one row.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from services.providers.base import CanonicalActivity

PROVIDER = "garmin"
ACTIVITY_KEYS = ("activities", "activityDetails", "manuallyUpdatedActivities")

# Garmin activityType -> our vocabulary. Anything not listed is not training we plan for.
ACTIVITY_TYPES = {
    "RUNNING": "outdoor_run",
    "STREET_RUNNING": "outdoor_run",
    "TRAIL_RUNNING": "trail_run",
    "ULTRA_RUN": "trail_run",
    "OBSTACLE_RUN": "trail_run",
    "TREADMILL_RUNNING": "indoor_run",
    "INDOOR_RUNNING": "indoor_run",
    "VIRTUAL_RUN": "indoor_run",
    "TRACK_RUNNING": "track_run",
    "HIKING": "hike",
    "RUCKING": "hike",
    "MOUNTAINEERING": "hike",
    "STAIR_CLIMBING": "hike",
    "STRENGTH_TRAINING": "strength",
    "HIIT": "strength",
    "INDOOR_CARDIO": "gym_cardio",
    "ELLIPTICAL": "gym_cardio",
}
RUN_TYPES = frozenset({"outdoor_run", "indoor_run", "trail_run", "track_run"})


def to_activity(item: dict[str, Any]) -> CanonicalActivity | None:
    """One pushed activity (any of ACTIVITY_KEYS) as a CanonicalActivity, or None when it
    is not a type we track or lacks the fields every activity needs."""
    summary = {**item, **(item.get("summary") or {})}
    activity_type = ACTIVITY_TYPES.get(str(summary.get("activityType") or "").upper())
    activity_id = item.get("activityId") or summary.get("activityId")
    start = summary.get("startTimeInSeconds")
    duration = summary.get("durationInSeconds")
    if not activity_type or activity_id is None or start is None or not duration:
        return None
    start_time = datetime.fromtimestamp(int(start), UTC)
    meters = summary.get("distanceInMeters")
    distance_km = meters / 1000 if meters else None
    pace = duration / distance_km if activity_type in RUN_TYPES and distance_km and distance_km >= 0.1 else None
    max_hr = summary.get("maxHeartRateInBeatsPerMinute")
    device = summary.get("deviceName")
    return CanonicalActivity(
        external_id=str(activity_id),
        provider=PROVIDER,
        activity_type=activity_type,
        start_time=start_time,
        end_time=start_time + timedelta(seconds=int(duration)),
        duration_seconds=float(duration),
        distance_km=distance_km,
        elevation_gain_m=summary.get("totalElevationGainInMeters"),
        elevation_loss_m=summary.get("totalElevationLossInMeters"),
        avg_hr=summary.get("averageHeartRateInBeatsPerMinute"),
        max_hr=int(max_hr) if max_hr is not None else None,
        avg_pace_sec_per_km=pace,
        calories=summary.get("activeKilocalories"),
        device_model=None if not device or device == "unknown" else str(device)[:100],
    )


def offset_minutes(item: dict[str, Any]) -> int | None:
    """The device's local-time offset, which places an activity on the athlete's calendar day."""
    offset = {**item, **(item.get("summary") or {})}.get("startTimeOffsetInSeconds")
    return int(offset) // 60 if offset is not None else None
