"""Parsers for COROS MCP tool output.

COROS returns human-readable prose from most tools (querySportRecords,
getActivityDetail, queryRestingHeartRate, ...) and raw JSON from others
(queryActivityLapData). None of it is a documented contract, so every parser
here is paired with a fixture test built from a verbatim real response.

Parsers raise CorosParseError when output does not look like the expected shape
at all. They must never return an empty result for unrecognised input -- that
reads downstream as "the athlete did nothing", which silently stops sync.
"""

import re
from datetime import UTC, date, datetime
from typing import Any

_RECORD_HEADER = re.compile(r"^\s*(\d+)\.\s+(.+?)\s+—\s+(\d{4}-\d{2}-\d{2})\s*$", re.M)
_DATE_LINE = re.compile(r"^(\d{4}-\d{2}-\d{2})", re.M)


class CorosParseError(ValueError):
    """COROS returned output that does not match the expected shape."""


def parse_duration(value: str) -> float:
    """'1:30:34' -> 5434.0, '19:31' -> 1171.0"""
    parts = [float(p) for p in value.strip().split(":")]
    seconds = 0.0
    for part in parts:
        seconds = seconds * 60 + part
    return seconds


def parse_pace(value: str) -> float:
    """'5:30 /km' -> 330.0 seconds per km"""
    return parse_duration(value.split("/")[0].strip())


def _search_float(pattern: str, text: str) -> float | None:
    match = re.search(pattern, text)
    return float(match.group(1)) if match else None


def _search_int(pattern: str, text: str) -> int | None:
    value = _search_float(pattern, text)
    return int(value) if value is not None else None


def parse_sport_records(text: str) -> list[dict[str, Any]]:
    if "Sport Records" not in text:
        raise CorosParseError("querySportRecords output missing its 'Sport Records' header")

    headers = list(_RECORD_HEADER.finditer(text))
    records: list[dict[str, Any]] = []
    for index, header in enumerate(headers):
        end = headers[index + 1].start() if index + 1 < len(headers) else len(text)
        block = text[header.start() : end]

        coords = re.search(r"Start Coordinates:\s*(-?[\d.]+),\s*(-?[\d.]+)", block)
        duration = re.search(r"Duration:\s*([\d:]+)", block)
        pace = re.search(r"Average Pace:\s*([\d:]+)\s*/km", block)

        records.append(
            {
                "label_id": (re.search(r"LabelId:\s*(\d+)", block) or [None, None])[1],
                "sport_type": _search_int(r"SportType:\s*(\d+)", block),
                "sport_label": header.group(2).strip(),
                "date": date.fromisoformat(header.group(3)),
                "start_timestamp": _search_int(r"startTimestamp=(\d+)", block),
                "end_timestamp": _search_int(r"endTimestamp=(\d+)", block),
                "duration_seconds": parse_duration(duration.group(1)) if duration else None,
                "distance_km": _search_float(r"Distance:\s*([\d.]+)\s*km", block),
                "avg_pace_sec_per_km": parse_pace(pace.group(1)) if pace else None,
                "avg_hr": _search_int(r"Avg HR:\s*(\d+)", block),
                "calories": _search_int(r"Calories:\s*(\d+)", block),
                "start_lat": float(coords.group(1)) if coords else None,
                "start_lon": float(coords.group(2)) if coords else None,
            }
        )
    return records


def parse_activity_detail(text: str) -> dict[str, Any]:
    if "Activity Details" not in text:
        raise CorosParseError("getActivityDetail output missing its 'Activity Details' header")

    workout_time = re.search(r"Workout Time:\s*([\d:]+)", text)
    pace = re.search(r"Average Pace:\s*([\d:]+)\s*/km", text)
    adjusted = re.search(r"Adjusted Pace:\s*([\d:]+)\s*/km", text)
    elevation = re.search(r"Elevation Gain / Loss:\s*(-?[\d.]+)\s*m\s*/\s*(-?[\d.]+)\s*m", text)

    return {
        "duration_seconds": parse_duration(workout_time.group(1)) if workout_time else None,
        "distance_km": _search_float(r"Distance:\s*([\d.]+)\s*km", text),
        "avg_pace_sec_per_km": parse_pace(pace.group(1)) if pace else None,
        "adjusted_pace_sec_per_km": parse_pace(adjusted.group(1)) if adjusted else None,
        "avg_hr": _search_int(r"Average Heart Rate:\s*(\d+)", text),
        "avg_cadence": _search_int(r"Average Cadence:\s*(\d+)", text),
        "elevation_gain_m": float(elevation.group(1)) if elevation else None,
        "elevation_loss_m": float(elevation.group(2)) if elevation else None,
        "calories": _search_int(r"Calories:\s*(\d+)", text),
        "training_load": _search_float(r"Training Load:\s*([\d.]+)", text),
        "aerobic_te": _search_float(r"Aerobic TE:\s*([\d.]+)", text),
        "anaerobic_te": _search_float(r"Anaerobic TE:\s*([\d.]+)", text),
    }


def parse_resting_hr(text: str) -> dict[date, int]:
    if "Resting Heart Rate" not in text:
        raise CorosParseError("queryRestingHeartRate output missing its header")
    return {
        date.fromisoformat(day): int(bpm) for day, bpm in re.findall(r"^(\d{4}-\d{2}-\d{2}):\s*(\d+)\s*bpm", text, re.M)
    }


def parse_sleep_hrv(text: str) -> dict[date, dict[str, Any]]:
    if "Sleep HRV" not in text and "HRV Assessment" not in text:
        raise CorosParseError("querySleepHrv output missing its header")

    assessment = text.split("Sleep HRV Time Series")[0]
    out: dict[date, dict[str, Any]] = {}
    blocks = re.split(r"^(\d{4}-\d{2}-\d{2}):\s*$", assessment, flags=re.M)
    for index in range(1, len(blocks) - 1, 2):
        day, body = blocks[index], blocks[index + 1]
        avg = re.search(r"HRV Avg:\s*([\d.]+)\s*ms\s*—\s*(.+?)\s*$", body, re.M)
        if not avg:
            continue
        out[date.fromisoformat(day)] = {
            "hrv_ms": float(avg.group(1)),
            "hrv_status": avg.group(2).strip(),
            "hrv_baseline_ms": _search_float(r"Baseline:\s*([\d.]+)\s*ms", body),
        }
    return out


def parse_training_load(text: str) -> dict[date, dict[str, Any]]:
    if "Training Load Assessment" not in text:
        raise CorosParseError("queryTrainingLoadAssessment output missing its header")

    out: dict[date, dict[str, Any]] = {}
    days = list(_DATE_LINE.finditer(text))
    for index, match in enumerate(days):
        end = days[index + 1].start() if index + 1 < len(days) else len(text)
        block = text[match.start() : end]
        out[date.fromisoformat(match.group(1))] = {
            "training_load_short": _search_float(r"Short-Term Load:\s*([\d.]+)", block),
            "training_load_long": _search_float(r"Long-Term Load:\s*([\d.]+)", block),
            "load_ratio": _search_float(r"Load Ratio:\s*([\d.]+)", block),
            "comment": (re.search(r"Comment:\s*(.+)", block) or [None, None])[1],
        }
    return out


def to_utc(timestamp: int) -> datetime:
    return datetime.fromtimestamp(timestamp, tz=UTC)
