"""Recorded race performance and attributed course facts; no generation or watch reads."""

import math
from typing import Any
from urllib.parse import urlsplit

from services.race_matcher import _payload_as_dict, score_race_course_chunks


def compatible_distance(result_km: float, entry_km: Any) -> bool:
    return (
        isinstance(entry_km, int | float)
        and not isinstance(entry_km, bool)
        and math.isfinite(entry_km)
        and entry_km > 0
        and result_km > 0
        and abs(entry_km - result_km) / result_km <= 0.15
    )


def historical_field(
    payload: dict[str, Any], distance_label: str, distance_km: float, year: int
) -> dict[str, Any] | None:
    label = distance_label.strip().casefold()
    matches = [
        row
        for row in payload.get("results", [])
        if row.get("year") == year
        and (row.get("distance_label") or "").strip().casefold() == label
        and compatible_distance(distance_km, row.get("distance_km"))
    ]
    return dict(matches[0]) if len(matches) == 1 else None


def safe_source_url(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        url = urlsplit(value)
        return (
            value
            if url.scheme in ("http", "https") and url.hostname and not url.username and not url.password
            else None
        )
    except ValueError:
        return None


def _strings(values: Any) -> list[str]:
    return [v for v in values if isinstance(v, str) and v.strip()] if isinstance(values, list) else []


def _number(value: Any, nonnegative: bool = False) -> int | float | None:
    if type(value) not in (int, float) or not math.isfinite(value) or (nonnegative and value < 0):
        return None
    return value


def select_course_context(
    result: dict[str, Any], chunks: list[dict[str, Any]], course_id: int | None = None
) -> dict[str, Any]:
    context = dict(status="missing", candidates=[], course=None, message=None)
    scored = []
    for chunk, score in score_race_course_chunks(result["race_name"], chunks):
        payload = _payload_as_dict(chunk.get("payload"))
        if payload.get("race_type") != result["discipline"]:
            continue
        entries = [
            entry
            for entry in payload.get("distances", [])
            if compatible_distance(result["distance_km"], entry.get("distance_km"))
            and isinstance(entry.get("label"), str)
            and entry["label"].strip()
        ]
        if not entries:
            continue
        entries.sort(key=lambda entry: abs(entry["distance_km"] - result["distance_km"]))
        ambiguous = (
            len(entries) > 1
            and entries[0]["label"] != entries[1]["label"]
            and abs(
                abs(entries[0]["distance_km"] - result["distance_km"])
                - abs(entries[1]["distance_km"] - result["distance_km"])
            )
            < 1e-6
        )
        scored.append((chunk, score, entries[0], ambiguous))
    scored.sort(key=lambda item: (-item[1], item[0]["id"]))
    if not scored or scored[0][1] < 86:
        if course_id is not None:
            raise ValueError("Course is not a compatible match for this result")
        return context
    automatic = len(scored) == 1 or scored[0][1] - scored[1][1] >= 10
    allowed = scored[:1] if automatic else [item for item in scored[:5] if item[1] >= 70]
    if course_id is not None:
        chosen = next((item for item in allowed if item[0]["id"] == course_id), None)
        if chosen is None:
            raise ValueError("Course is not a compatible match for this result")
    elif not automatic:
        context.update(
            status="ambiguous",
            candidates=[
                {
                    "id": item[0]["id"],
                    "race_name": _payload_as_dict(item[0]["payload"]).get("race_name") or item[0]["title"],
                    "distance_label": item[2]["label"],
                }
                for item in allowed
                if not item[3]
            ],
        )
        return context
    else:
        chosen = scored[0]
    chunk, _, entry, ambiguous_distance = chosen
    if ambiguous_distance:
        if course_id is not None:
            raise ValueError("Course distance is ambiguous")
        context["message"] = "Course distance is ambiguous"
        return context
    payload = _payload_as_dict(chunk.get("payload"))
    year = payload.get("edition_year")
    year = year if type(year) is int else None
    result_year = int(result["race_date"][:4])
    climate = {}
    raw_climate = payload.get("climate") or {}
    for key in ("avg_temp_c", "humidity_pct", "season", "notes"):
        value = raw_climate.get(key)
        if key in ("season", "notes"):
            if isinstance(value, str):
                climate[key] = value
        elif key == "humidity_pct" and isinstance(value, str):
            climate[key] = value
        elif _number(value) is not None:
            climate[key] = value
    context.update(
        status="matched",
        course={
            "id": chunk["id"],
            "race_name": payload.get("race_name") or chunk["title"],
            "distance_label": entry["label"],
            "distance_km": entry["distance_km"],
            "elevation_gain_m": _number(entry.get("elevation_gain_m"), True),
            "location": payload.get("location") if isinstance(payload.get("location"), str) else None,
            "terrain": _strings(payload.get("terrain")),
            "key_climbs": _strings(payload.get("key_climbs")),
            "climate": climate,
            "runner_reviews": _strings(payload.get("runner_reviews")),
            "source_label": chunk.get("source_label"),
            "source_urls": [url for value in _strings(payload.get("source_urls")) if (url := safe_source_url(value))],
            "verified_at": payload.get("verified_at"),
            "edition_year": year,
            "edition_status": "unknown" if year is None else "same" if year == result_year else "different",
        },
    )
    return context
