"""Tests for FitParser.parse — pure byte parsing, no DB/network.

Uses a synthetic minimal FIT file (see fixtures/fit_builder.py) rather than
a real Garmin export, since real .fit files contain a runner's actual GPS
track and have no business being checked into a public test fixture.
"""

import pytest

from parsers.fit_parser import FitParser
from tests.unit.fixtures.fit_builder import build_fit_bytes, raw_timestamp

BASE_UNIX_TS = 1751328000  # arbitrary fixed reference; only relative deltas matter


def make_records(distances_and_hrs: list[tuple[float, int]], interval_seconds: int = 5):
    return [
        (raw_timestamp(BASE_UNIX_TS + i * interval_seconds), dist, hr) for i, (dist, hr) in enumerate(distances_and_hrs)
    ]


class TestFitParserParse:
    def test_returns_expected_top_level_shape(self):
        fit_bytes = build_fit_bytes(make_records([(0.0, 120), (20.0, 130), (45.0, 140)]))
        result = FitParser.parse(fit_bytes)
        assert set(result.keys()) == {"summary", "records", "total_raw_points"}
        assert result["total_raw_points"] == 3

    def test_backfills_total_distance_from_last_record_when_no_session(self):
        fit_bytes = build_fit_bytes(make_records([(0.0, 120), (20.0, 130), (45.0, 140)]))
        result = FitParser.parse(fit_bytes)
        assert result["summary"]["total_distance_meters"] == 45.0

    def test_backfills_duration_from_record_timestamps_when_no_session(self):
        fit_bytes = build_fit_bytes(make_records([(0.0, 120), (20.0, 130), (45.0, 140)], interval_seconds=5))
        result = FitParser.parse(fit_bytes)
        assert result["summary"]["total_duration_seconds"] == 10.0  # 3 records, 5s apart

    def test_computes_avg_and_max_heart_rate_from_records_when_no_session(self):
        fit_bytes = build_fit_bytes(make_records([(0.0, 100), (10.0, 150), (20.0, 200)]))
        result = FitParser.parse(fit_bytes)
        assert result["summary"]["avg_heart_rate"] == 150.0
        assert result["summary"]["max_heart_rate"] == 200

    def test_record_timestamps_are_isoformat_strings(self):
        fit_bytes = build_fit_bytes(make_records([(0.0, 120)]))
        result = FitParser.parse(fit_bytes)
        assert result["records"][0]["timestamp"] is not None
        # Should be parseable back into a datetime.
        from datetime import datetime

        datetime.fromisoformat(result["records"][0]["timestamp"])

    def test_invalid_bytes_raise_value_error(self):
        with pytest.raises(ValueError):
            FitParser.parse(b"this is not a fit file at all")


class TestSemicirclesToDegrees:
    def test_none_input_returns_none(self):
        assert FitParser.semicircles_to_degrees(None) is None

    def test_converts_semicircles_to_degrees(self):
        # 2^31 semicircles == 180 degrees, by definition.
        assert FitParser.semicircles_to_degrees(2**31) == pytest.approx(180.0)

    def test_zero_semicircles_is_zero_degrees(self):
        assert FitParser.semicircles_to_degrees(0) == 0.0
