"""Tests for GpxParser.parse — pure byte parsing, no DB/network.

Uses a small, hand-written GPX track (not a real user's route file) so the
test is self-contained and doesn't check any real location data into the repo.
"""

import pytest

from parsers.gpx_parser import GpxParser


def make_gpx(points: list[tuple[float, float, float]]) -> bytes:
    """points: list of (lat, lon, elevation_m) tuples."""
    trkpts = "\n".join(f'<trkpt lat="{lat}" lon="{lon}"><ele>{ele}</ele></trkpt>' for lat, lon, ele in points)
    gpx = f"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="uphill-ai-tests" xmlns="http://www.topografix.com/GPX/1/1">
  <trk>
    <name>Synthetic Test Route</name>
    <trkseg>
      {trkpts}
    </trkseg>
  </trk>
</gpx>"""
    return gpx.encode("utf-8")


# Roughly 0.001 degrees of latitude ~= 111m, used to build predictable segment distances.
FLAT_ROUTE = make_gpx(
    [
        (45.0000, 7.0000, 1000.0),
        (45.0010, 7.0000, 1000.0),
        (45.0020, 7.0000, 1000.0),
    ]
)

CLIMBING_ROUTE = make_gpx(
    [
        (45.0000, 7.0000, 1000.0),
        (45.0010, 7.0000, 1200.0),
        (45.0020, 7.0000, 1500.0),
    ]
)


class TestGpxParserParse:
    def test_returns_expected_top_level_shape(self):
        result = GpxParser.parse(FLAT_ROUTE)
        assert set(result.keys()) == {"summary", "points", "checkpoints", "total_raw_points"}
        assert result["total_raw_points"] == 3

    def test_flat_route_has_no_elevation_gain_or_loss(self):
        result = GpxParser.parse(FLAT_ROUTE)
        assert result["summary"]["total_elevation_gain_meters"] == 0.0
        assert result["summary"]["total_elevation_loss_meters"] == 0.0

    def test_climbing_route_accumulates_gain(self):
        result = GpxParser.parse(CLIMBING_ROUTE)
        assert result["summary"]["total_elevation_gain_meters"] == pytest.approx(500.0)
        assert result["summary"]["min_elevation_meters"] == 1000.0
        assert result["summary"]["max_elevation_meters"] == 1500.0

    def test_total_distance_is_positive_for_moving_route(self):
        result = GpxParser.parse(FLAT_ROUTE)
        assert result["summary"]["total_distance_meters"] > 0

    def test_checkpoint_interval_controls_checkpoint_count(self):
        # A route short enough that a huge interval produces only the final "Finish" checkpoint.
        result = GpxParser.parse(FLAT_ROUTE, checkpoint_interval_meters=100_000.0)
        assert len(result["checkpoints"]) == 1
        assert result["checkpoints"][0]["name"] == "Finish"

    def test_invalid_xml_raises_value_error(self):
        with pytest.raises(ValueError):
            GpxParser.parse(b"this is not gpx xml at all")
