"""Recorded race performance and attributed course facts; no generation or watch reads."""

import math
from typing import Any
from urllib.parse import urlsplit

from services.race_history import normalize_name
from services.race_matcher import _payload_as_dict, score_race_course_chunks


def _course_payload(raw: Any) -> dict[str, Any]:
    try:
        payload = _payload_as_dict(raw)
    except (TypeError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _dicts(values: Any) -> list[dict[str, Any]]:
    return [v for v in values if isinstance(v, dict)] if isinstance(values, list) else []


_FIELD_KEYS = ("year", "distance_label", "distance_km", "finishers", "winner_time", "winner_time_women", "percentiles")


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
        for row in _dicts(payload.get("results"))
        if row.get("year") == year
        and isinstance(row.get("distance_label"), str)
        and row["distance_label"].strip().casefold() == label
        and compatible_distance(distance_km, row.get("distance_km"))
    ]
    return {k: matches[0][k] for k in _FIELD_KEYS if k in matches[0]} if len(matches) == 1 else None


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
    chunks = [chunk for chunk in chunks if _course_payload(chunk.get("payload"))]
    for chunk, score in score_race_course_chunks(result["race_name"], chunks):
        payload = _course_payload(chunk.get("payload"))
        if payload.get("race_type") != result["discipline"]:
            continue
        entries = [
            entry
            for entry in _dicts(payload.get("distances"))
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
                    "race_name": _course_payload(item[0]["payload"]).get("race_name") or item[0]["title"],
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
    payload = _course_payload(chunk.get("payload"))
    year = payload.get("edition_year")
    year = year if type(year) is int else None
    result_year = int(result["race_date"][:4])
    climate = {}
    raw_climate = payload.get("climate") if isinstance(payload.get("climate"), dict) else {}
    for key in ("avg_temp_c", "humidity_pct", "season", "notes"):
        value = raw_climate.get(key)
        if key in ("season", "notes"):
            if isinstance(value, str):
                climate[key] = value
        elif key in ("humidity_pct", "avg_temp_c") and isinstance(value, str):
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


def top_position_pct(rank: int | None, total: int | None, is_dnf: bool) -> float | None:
    if is_dnf or type(rank) is not int or type(total) is not int or not 1 <= rank <= total:
        return None
    return round(100 * rank / total, 1)


def previous_finish(
    result: dict[str, Any], rows: list[dict[str, Any]], canonical_ids: dict[int, int]
) -> dict[str, Any] | None:
    if not result.get("selected") or result.get("is_dnf") or not result.get("finish_time_sec"):
        return None
    candidates = []
    current_course = canonical_ids.get(result["id"])
    for row in rows:
        same_name = normalize_name(row["race_name"]) == normalize_name(result["race_name"])
        same_course = current_course is not None and canonical_ids.get(row["id"]) == current_course
        if (
            row["id"] != result["id"]
            and row.get("selected")
            and not row.get("is_dnf")
            and (row.get("finish_time_sec") or 0) > 0
            and row["race_date"] < result["race_date"]
            and row["discipline"] == result["discipline"]
            and (same_name or same_course)
            and abs(row["distance_km"] - result["distance_km"]) / result["distance_km"] <= 0.01
        ):
            candidates.append(row)
    if not candidates:
        return None
    prior = sorted(candidates, key=lambda row: (row["race_date"], row["id"]), reverse=True)[0]
    return {
        "result_id": prior["id"],
        "race_date": prior["race_date"],
        "finish_time_sec": prior["finish_time_sec"],
        "delta_sec": result["finish_time_sec"] - prior["finish_time_sec"],
    }


def build_detail(user_id: int, result_id: int, course_id: int | None = None) -> dict[str, Any] | None:
    from datetime import date

    import db
    from log_utils import get_logger
    from services import race_history
    from services.race_personal_bests import compute_road_prs

    result = race_history.get_result(result_id, user_id)
    if result is None:
        return None
    rows = race_history._dedupe(race_history.list_results(user_id, False))
    prs = compute_road_prs(rows, date.today())
    road_pb_key = next((key for key, pr in prs.items() if pr and pr["result_id"] == result_id), None)
    chunks = []
    context = None
    try:
        chunks = db.get_kb_chunks("race_courses", kind="race_profile")
    except Exception as exc:
        get_logger(__name__).warning("Race course KB read unavailable: %s", type(exc).__name__)
        context = dict(
            status="unavailable", candidates=[], course=None, message="Course context could not be loaded. Retry."
        )
    if context is None:
        context = select_course_context(result, chunks, course_id)
    canonical_ids = {}
    if context["course"] is not None:
        canonical_ids[result_id] = context["course"]["id"]
    for row in rows:
        if row["id"] == result_id:
            continue
        match = select_course_context(row, chunks)
        if match["status"] == "matched":
            canonical_ids[row["id"]] = match["course"]["id"]
    field = None
    if context["course"] is not None:
        chosen = context["course"]
        payload = _course_payload(next(chunk["payload"] for chunk in chunks if chunk["id"] == chosen["id"]))
        field = historical_field(payload, chosen["distance_label"], result["distance_km"], int(result["race_date"][:4]))
    pace = None
    if (
        result["selected"]
        and result["discipline"] == "road"
        and not result["is_dnf"]
        and (result["finish_time_sec"] or 0) > 0
    ):
        pace = round(result["finish_time_sec"] / result["distance_km"], 1)
    public_result = {key: value for key, value in result.items() if key not in ("raw", "user_id")}
    return {
        "result": public_result,
        "performance": {
            "overall_top_pct": top_position_pct(
                result.get("rank_overall"), result.get("total_overall"), result["is_dnf"]
            ),
            "gender_top_pct": top_position_pct(result.get("rank_gender"), result.get("total_gender"), result["is_dnf"]),
            "age_group_top_pct": top_position_pct(
                result.get("rank_age_group"), result.get("total_age_group"), result["is_dnf"]
            ),
            "average_pace_sec_km": pace,
            "road_pb_key": road_pb_key,
        },
        "previous_finish": previous_finish(result, rows, canonical_ids),
        "course_context": context,
        "historical_field": field,
    }
