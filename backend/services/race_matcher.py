"""Fuzzy-matches a user-entered race name (+ optional distance) against the
hand-curated race_courses KB, to enrich Scheduler and Gear Finder prompts
with curated terrain/climate/elevation context. Never guesses: a match
below the confidence threshold, or any lookup failure, returns None so
callers fall back to whatever the user/GPX already supplied."""

import json
import re
from dataclasses import dataclass
from typing import Any

from rapidfuzz import fuzz

_MIN_NAME_LENGTH = 3
_FUZZY_THRESHOLD = 86.0
_MILE_TO_KM = 1.60934
_NAMED_DISTANCES_KM = {
    "half marathon": 21.0975,
    "marathon": 42.195,
    "half": 21.0975,
    "5k": 5.0,
    "10k": 10.0,
}


@dataclass
class MatchedRace:
    race_name: str
    distance_label: str | None
    distance_km: float | None
    elevation_gain_m: float | None
    terrain: list[str]
    course_context: str
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "race_name": self.race_name,
            "distance_label": self.distance_label,
            "distance_km": self.distance_km,
            "elevation_gain_m": self.elevation_gain_m,
            "terrain": self.terrain,
        }


def _payload_as_dict(payload: Any) -> dict[str, Any]:
    if payload is None:
        return {}
    if isinstance(payload, str):
        try:
            return json.loads(payload)
        except Exception:
            return {}
    return dict(payload)


def _parse_distance_km(distance_label: str | None) -> float | None:
    if not distance_label:
        return None
    label = distance_label.strip().lower()
    for name, km in _NAMED_DISTANCES_KM.items():
        if name in label:
            return km
    match = re.search(r"(\d+(?:\.\d+)?)", label)
    if not match:
        return None
    value = float(match.group(1))
    if "mile" in label or re.search(r"\bmi\b", label):
        return value * _MILE_TO_KM
    return value


def _closest_distance_entry(distances: list[dict[str, Any]], distance_km: float) -> dict[str, Any] | None:
    if not distances:
        return None
    return min(distances, key=lambda d: abs((d.get("distance_km") or 0) - distance_km))


def _keyword_hit(keyword: str, query: str) -> bool:
    """Word/phrase-boundary match: True if `keyword` appears in `query` as a
    whole word or phrase (not merely as a substring), or vice versa."""
    if not keyword:
        return False
    if re.search(rf"\b{re.escape(keyword)}\b", query):
        return True
    return bool(re.search(rf"\b{re.escape(query)}\b", keyword))


def match_race(
    name: str | None,
    distance_km: float | None = None,
    distance_label: str | None = None,
) -> MatchedRace | None:
    if not name or len(name.strip()) < _MIN_NAME_LENGTH:
        return None

    import db

    try:
        chunks = db.get_kb_chunks("race_courses", kind="race_profile")
    except Exception as e:
        print(f"[RaceMatcher] Failed to load race_courses KB: {e}")
        return None
    if not chunks:
        return None

    query = name.strip().lower()
    best_chunk = None
    best_score = 0.0

    for chunk in chunks:
        payload = _payload_as_dict(chunk.get("payload"))
        keywords = payload.get("matching_hints", {}).get("name_keywords", [])
        if any(_keyword_hit(kw.lower(), query) for kw in keywords if kw):
            best_chunk = chunk
            best_score = 100.0
            break

        # Very short candidates (e.g. 3-4 letter acronyms like "UTA") are excluded
        # from fuzzy scoring: WRatio's partial-ratio component gives near-full
        # credit when a short string is merely a substring of an unrelated query
        # (e.g. alias "UTA" inside "Utah 100 Endurance Run"), letting the same
        # class of false positive back in above the confidence threshold even
        # though the exact-keyword bypass above is fixed.
        candidates = [payload.get("race_name", "")] + list(payload.get("aliases", []))
        score = max(
            (fuzz.WRatio(query, c.lower()) for c in candidates if c and len(c) >= 5),
            default=0.0,
        )
        if score > best_score:
            best_score = score
            best_chunk = chunk

    if best_chunk is None or best_score < _FUZZY_THRESHOLD:
        return None

    payload = _payload_as_dict(best_chunk.get("payload"))
    resolved_distance_km = distance_km if distance_km is not None else _parse_distance_km(distance_label)

    distance_entry = None
    if resolved_distance_km is not None:
        distance_entry = _closest_distance_entry(payload.get("distances", []), resolved_distance_km)

    return MatchedRace(
        race_name=payload.get("race_name", best_chunk.get("title", "")),
        distance_label=distance_entry.get("label") if distance_entry else None,
        distance_km=distance_entry.get("distance_km") if distance_entry else None,
        elevation_gain_m=distance_entry.get("elevation_gain_m") if distance_entry else None,
        terrain=payload.get("terrain", []),
        course_context=best_chunk.get("content", ""),
        confidence=best_score,
    )
