"""Parsers for COROS MCP tool output.

COROS returns human-readable prose from most tools (querySportRecords,
getActivityDetail, queryRestingHeartRate, ...) and raw JSON from others
(queryActivityLapData). None of it is a documented contract, so every parser
here is paired with a fixture test built from a verbatim real response.

Parsers raise CorosParseError when output does not look like the expected shape
at all. They must never return an empty result for unrecognised input -- that
reads downstream as "the athlete did nothing", which silently stops sync.

Guard design: a substring check on the response's title banner is not enough --
a truncated or garbled response can still carry the title text. Beyond the
banner check, each dict/list-returning parser also verifies that it actually
extracted something whenever the stripped response body (banner, "====" rules,
and "Note:" preambles removed) still has content left over. A body that is
genuinely empty after stripping is treated as a legitimate "no data for this
athlete" answer, not an error -- that happens for real, e.g. a brand-new
athlete with no history yet.
"""

import re
from datetime import UTC, date, datetime
from typing import Any

_RECORD_HEADER = re.compile(r"^\s*(\d+)\.\s+(.+?)\s+—\s+(\d{4}-\d{2}-\d{2})\s*$", re.M)
# Anchored to lines that are *only* a date -- a vendor-added trailing sentence
# that happens to start with a date (e.g. a footer disclaimer) must not be
# mistaken for a new block boundary.
_DATE_LINE = re.compile(r"^(\d{4}-\d{2}-\d{2})\s*$", re.M)


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


def _drop_lines(text: str, *line_patterns: str) -> str:
    """Strip banner/title/separator/note lines matching any of the given
    whole-line regexes, returning whatever is left.

    Used by the dict/list-returning parsers to tell a genuinely empty response
    body (a legitimate "no data" answer) apart from a body that has leftover
    content we failed to recognise (a truncated or reshaped response).
    """
    compiled = [re.compile(pattern) for pattern in line_patterns]
    kept = [
        line.strip()
        for line in text.split("\n")
        if line.strip() and not any(pattern.fullmatch(line.strip()) for pattern in compiled)
    ]
    return "\n".join(kept)


def parse_sport_records(text: str) -> list[dict[str, Any]]:
    if "Sport Records" not in text:
        raise CorosParseError("querySportRecords output missing its 'Sport Records' header")

    headers = list(_RECORD_HEADER.finditer(text))

    # The header line carries an authoritative "(N records)" count -- stronger
    # evidence than "is there any text left" for telling a real empty result
    # (N == 0) apart from a truncated response that claims records but has none.
    count_match = re.search(r"\((\d+)\s*records?\)", text)
    expected_count = int(count_match.group(1)) if count_match else None

    if not headers:
        if expected_count == 0:
            return []
        raise CorosParseError(
            "querySportRecords output has a 'Sport Records' header but no parsable "
            "record entries -- response shape may have changed"
        )

    records: list[dict[str, Any]] = []
    for index, header in enumerate(headers):
        end = headers[index + 1].start() if index + 1 < len(headers) else len(text)
        block = text[header.start() : end]

        coords = re.search(r"Start Coordinates:\s*(-?[\d.]+),\s*(-?[\d.]+)", block)
        duration = re.search(r"Duration:\s*([\d:]+)", block)
        pace = re.search(r"Average Pace:\s*([\d:]+)\s*/km", block)
        label_id_match = re.search(r"LabelId:\s*(\d+)", block)
        start_timestamp_match = re.search(r"startTimestamp=(\d+)", block)

        # LabelId is the cross-provider dedup key, Duration backs a NOT NULL DB
        # column, and start_timestamp becomes activities.start_time (also NOT
        # NULL, and fed straight into to_utc() by Task 6's adapter -- a missing
        # value there would otherwise surface as a bare TypeError from
        # datetime.fromtimestamp(None) far from the actual cause). A record
        # missing any of the three cannot be identified, timed, or stored, so
        # it must fail loudly rather than silently carry a None through.
        if label_id_match is None:
            raise CorosParseError(
                f"querySportRecords record #{index + 1} is missing its LabelId -- "
                "cannot dedupe this activity across providers"
            )
        if duration is None:
            raise CorosParseError(
                f"querySportRecords record #{index + 1} is missing its Duration -- "
                "cannot store an activity with no duration"
            )
        if start_timestamp_match is None:
            raise CorosParseError(
                f"querySportRecords record #{index + 1} is missing its Time Window "
                "startTimestamp -- cannot store an activity with no start time"
            )

        records.append(
            {
                "label_id": label_id_match[1],
                "sport_type": _search_int(r"SportType:\s*(\d+)", block),
                "sport_label": header.group(2).strip(),
                "date": date.fromisoformat(header.group(3)),
                "start_timestamp": int(start_timestamp_match.group(1)),
                "end_timestamp": _search_int(r"endTimestamp=(\d+)", block),
                "duration_seconds": parse_duration(duration.group(1)),
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

    entries = {
        date.fromisoformat(day): int(bpm) for day, bpm in re.findall(r"^(\d{4}-\d{2}-\d{2}):\s*(\d+)\s*bpm", text, re.M)
    }
    if not entries:
        remaining = _drop_lines(text, r"Resting Heart Rate.*", r"=+")
        if remaining:
            raise CorosParseError(
                "queryRestingHeartRate output has a header but no parsable date rows "
                "-- response shape may have changed"
            )
    return entries


def parse_sleep_hrv(text: str) -> dict[date, dict[str, Any]]:
    # "Sleep HRV" alone is not a safe guard -- it is a substring of the
    # "Sleep HRV Time Series" section heading, so a response containing only
    # that (much longer) section would slip past a check on "Sleep HRV".
    # The assessment section itself must be present.
    if "HRV Assessment" not in text:
        raise CorosParseError("querySleepHrv output missing its 'HRV Assessment' header")

    assessment = text.split("Sleep HRV Time Series")[0]
    # Tracked separately from `out` -- a date header that is matched but then
    # skipped (no "HRV Avg:" line, e.g. a night the watch couldn't compute
    # HRV for) is a recognised shape with legitimately nothing to record, not
    # an unrecognised response. `out` being empty can't distinguish the two;
    # this counter, taken before any skipping, can.
    date_headers = list(re.finditer(r"^(\d{4}-\d{2}-\d{2}):\s*$", assessment, re.M))
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

    if not date_headers:
        remaining = _drop_lines(
            assessment,
            r"Sleep HRV.*",
            r"HRV Assessment.*",
            r"=+",
            r"Note:.*",
        )
        if remaining:
            raise CorosParseError(
                "querySleepHrv output has an 'HRV Assessment' header but no parsable "
                "date rows -- response shape may have changed"
            )
    return out


def parse_training_load(text: str) -> dict[date, dict[str, Any]]:
    if "Training Load Assessment" not in text:
        raise CorosParseError("queryTrainingLoadAssessment output missing its header")

    out: dict[date, dict[str, Any]] = {}
    days = list(_DATE_LINE.finditer(text))
    for index, match in enumerate(days):
        end = days[index + 1].start() if index + 1 < len(days) else len(text)
        block = text[match.start() : end]
        parsed = {
            "training_load_short": _search_float(r"Short-Term Load:\s*([\d.]+)", block),
            "training_load_long": _search_float(r"Long-Term Load:\s*([\d.]+)", block),
            "load_ratio": _search_float(r"Load Ratio:\s*([\d.]+)", block),
            "comment": (re.search(r"Comment:\s*(.+)", block) or [None, None])[1],
        }
        if (
            parsed["training_load_short"] is None
            and parsed["training_load_long"] is None
            and parsed["load_ratio"] is None
        ):
            # A block carrying none of the numeric fields is boilerplate (e.g. a
            # footer sentence that happens to start with a date), not a real
            # entry -- never let it silently overwrite a populated entry for
            # the same date.
            continue
        out[date.fromisoformat(match.group(1))] = parsed

    # `days` (not `out`) is the right thing to test here: a date header that
    # was matched and then skipped for lacking numeric fields (e.g. "not
    # enough training history yet") is a recognised shape with legitimately
    # nothing to record, not an unrecognised response. `out` being empty
    # can't distinguish "found headers, all skipped" from "found no headers
    # at all" -- `days` was captured before any skipping happened.
    if not days:
        remaining = _drop_lines(text, r"Training Load Assessment.*", r"=+")
        if remaining:
            raise CorosParseError(
                "queryTrainingLoadAssessment output has a header but no parsable "
                "date rows -- response shape may have changed"
            )
    return out


def to_utc(timestamp: int) -> datetime:
    return datetime.fromtimestamp(timestamp, tz=UTC)
