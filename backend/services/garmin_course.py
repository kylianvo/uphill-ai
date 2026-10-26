"""Send a race course (the athlete's GPX) to their Garmin device via the Courses API.

Garmin wants consecutive points no more than 100 m apart and about 10,000 points at
most, so the track is thinned to one point every MIN_SPACING_M (or more for very long
courses) without ever skipping more than 100 m. The highest point is marked as a
summit. Garmin syncs the course to the watch, which then navigates it with climb
guidance.
"""

import datetime as dt
from typing import Any

import gpxpy

import db
from config import settings
from services import garmin_oauth, garmin_push
from services.providers.garmin import PROVIDER

MAX_POINTS = 9_500
MIN_SPACING_M = 20.0
MAX_SPACING_M = 100.0
MAX_NAME = 100


class CourseError(garmin_push.PushError):
    """A course send refused or failed; `code` is what the UI explains."""


def _thin(raw: list, steps: list[float], spacing: float) -> list:
    """Keeps a point just before the gap since the last kept one would pass `spacing`; a raw
    step already longer than that is kept as it is."""
    points, since_kept = [raw[0]], 0.0
    for prev, step in zip(raw, steps, strict=False):
        if since_kept + step >= spacing and since_kept > 0:
            points.append(prev)
            since_kept = step
        else:
            since_kept += step
    points.append(raw[-1])
    return points


def geo_points(gpx_bytes: bytes) -> dict[str, Any]:
    """The track as Garmin geoPoints plus its distance, gain and loss (metres)."""
    try:
        gpx = gpxpy.parse(gpx_bytes.decode("utf-8", errors="ignore"))
    except Exception as exc:
        raise CourseError("GPX_invalid", 400) from exc
    raw = [p for t in gpx.tracks for s in t.segments for p in s.points] or [p for r in gpx.routes for p in r.points]
    if len(raw) < 2:
        raise CourseError("GPX_invalid", 400)

    steps = [b.distance_2d(a) or 0.0 for a, b in zip(raw, raw[1:], strict=False)]
    total = sum(steps)
    gain = loss = 0.0
    for a, b in zip(raw, raw[1:], strict=False):
        if a.elevation is not None and b.elevation is not None:
            rise = b.elevation - a.elevation
            gain, loss = (gain + rise, loss) if rise > 0 else (gain, loss - rise)
    spacing = min(MAX_SPACING_M, max(MIN_SPACING_M, total / MAX_POINTS))
    points = _thin(raw, steps, spacing)
    # Points land a little under `spacing` apart, so a long ultra can still run over the cap.
    while len(points) > MAX_POINTS and spacing < MAX_SPACING_M:
        spacing = min(MAX_SPACING_M, spacing * 1.2)
        points = _thin(raw, steps, spacing)

    geo = [{"latitude": p.latitude, "longitude": p.longitude, "elevation": p.elevation} for p in points]
    with_elevation = [g for g in geo if g["elevation"] is not None]
    if with_elevation:
        top = max(with_elevation, key=lambda g: g["elevation"])
        top["information"] = {"name": "Summit", "coursePointType": "SUMMIT"}
    return {
        "geoPoints": geo,
        "distance": round(total, 1),
        "elevationGain": round(gain, 1),
        "elevationLoss": round(loss, 1),
    }


async def send(user_id: int, gpx_bytes: bytes, name: str, transport=None) -> dict[str, Any]:
    connection = db.get_connection(user_id, PROVIDER)
    if not connection or connection.get("status") != "active":
        raise CourseError("GARMIN_not_connected", 409)
    if "COURSE_IMPORT" not in (connection.get("scopes") or "").split():
        raise CourseError("GARMIN_no_course_permission", 409)
    track = geo_points(gpx_bytes)
    # Shares the daily send cap with workouts: both spend Garmin's per-athlete call budget.
    limit = settings.GARMIN_DAILY_PUSH_LIMIT
    if not db.claim_garmin_push_slot(user_id, dt.datetime.now(dt.UTC).date(), limit):
        raise CourseError("PUSH_limit", 429, {"limit": limit})
    course = {
        "courseName": (name.strip() or "Race course")[:MAX_NAME],
        "description": "From Uphill AI",
        "activityType": "TRAIL_RUNNING",
        "coordinateSystem": "WGS84",
        **track,
    }
    try:
        token = await garmin_oauth.access_token(connection)
    except garmin_oauth.GarminAuthError as exc:
        raise CourseError("GARMIN_not_connected", 409) from exc
    try:
        created = await garmin_push._call("POST", "/training-api/courses/v1/course", token, course, transport)
    except garmin_oauth.GarminAuthError as exc:
        if exc.status == 412:
            raise CourseError("GARMIN_no_course_permission", 409) from exc
        raise CourseError("GARMIN_unavailable", 504) from exc
    return {
        "status": "sent",
        "course_id": str(created.get("courseId")) if isinstance(created, dict) and created.get("courseId") else None,
        "distance_km": round(track["distance"] / 1000, 1),
        "points": len(track["geoPoints"]),
    }
