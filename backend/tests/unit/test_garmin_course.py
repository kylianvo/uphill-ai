"""Race course GPX -> Garmin Courses API -- synthetic tracks, no live Garmin."""

import asyncio
import json
import math

import httpx
import pytest

from services import garmin_course, garmin_oauth, garmin_push


def _gpx(n: int, step_m: float, climb_at: int | None = None) -> bytes:
    """A track heading north, `n` points `step_m` apart, rising to a peak at index `climb_at`."""
    deg = step_m / 111_320
    pts = []
    for i in range(n):
        ele = 1000 + (i if climb_at is None or i <= climb_at else 2 * climb_at - i)
        pts.append(f'<trkpt lat="{22 + i * deg:.7f}" lon="103.8"><ele>{ele}</ele></trkpt>')
    return f'<gpx version="1.1"><trk><trkseg>{"".join(pts)}</trkseg></trk></gpx>'.encode()


def _gaps(points):
    return [
        math.hypot(b["latitude"] - a["latitude"], b["longitude"] - a["longitude"]) * 111_320
        for a, b in zip(points, points[1:], strict=False)
    ]


def test_a_dense_track_is_thinned_but_never_leaves_a_gap_over_100_m():
    track = garmin_course.geo_points(_gpx(2001, 5, climb_at=1200))  # 10 km, a point every 5 m
    points = track["geoPoints"]
    assert 500 <= len(points) <= 700  # one point every 15-20 m
    assert max(_gaps(points)) <= 100.5
    assert track["distance"] == pytest.approx(10_000, rel=0.01)
    assert track["elevationGain"] == pytest.approx(1200, abs=1) and track["elevationLoss"] == pytest.approx(800, abs=1)
    summit = [p for p in points if "information" in p]
    assert len(summit) == 1 and summit[0]["information"]["coursePointType"] == "SUMMIT"
    assert summit[0]["elevation"] == max(p["elevation"] for p in points)


def test_a_sparse_track_keeps_every_point():
    assert len(garmin_course.geo_points(_gpx(50, 300))["geoPoints"]) == 50


def test_a_file_that_is_not_a_track_is_refused():
    with pytest.raises(garmin_course.CourseError) as exc:
        garmin_course.geo_points(b"not xml")
    assert exc.value.code == "GPX_invalid"


@pytest.fixture
def connected(monkeypatch):
    monkeypatch.setattr(garmin_push, "CALL_SPACING_SECONDS", 0)
    monkeypatch.setattr(
        garmin_course.db, "get_connection", lambda u, p: {"status": "active", "scopes": "COURSE_IMPORT WORKOUT_IMPORT"}
    )
    monkeypatch.setattr(garmin_course.db, "claim_garmin_push_slot", lambda u, d, limit: True)

    async def token(connection):
        return "tok"

    monkeypatch.setattr(garmin_oauth, "access_token", token)


def test_send_posts_a_trail_running_course(connected):
    sent = {}

    def garmin(request: httpx.Request) -> httpx.Response:
        sent["path"] = request.url.path
        sent["body"] = json.loads(request.content)
        return httpx.Response(200, json={"courseId": 777})

    result = asyncio.run(garmin_course.send(42, _gpx(200, 10), "UTMB 50K", transport=httpx.MockTransport(garmin)))
    assert sent["path"] == "/training-api/courses/v1/course"
    assert sent["body"]["courseName"] == "UTMB 50K" and sent["body"]["activityType"] == "TRAIL_RUNNING"
    assert sent["body"]["coordinateSystem"] == "WGS84" and len(sent["body"]["geoPoints"]) >= 2
    assert result["course_id"] == "777" and result["distance_km"] == pytest.approx(2.0, abs=0.1)


def test_send_needs_the_course_permission(connected, monkeypatch):
    monkeypatch.setattr(
        garmin_course.db, "get_connection", lambda u, p: {"status": "active", "scopes": "WORKOUT_IMPORT"}
    )
    with pytest.raises(garmin_course.CourseError) as exc:
        asyncio.run(garmin_course.send(42, _gpx(10, 10), "x"))
    assert exc.value.code == "GARMIN_no_course_permission"


def test_a_long_ultra_stays_under_garmins_point_cap():
    track = garmin_course.geo_points(_gpx(34_000, 5))  # 170 km at a point every 5 m
    assert len(track["geoPoints"]) <= garmin_course.MAX_POINTS
    assert max(_gaps(track["geoPoints"])) <= 100.5
