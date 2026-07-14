"""Fuzzy-matches a user-entered race name (+ optional distance) against the
hand-curated race_courses KB, to enrich Scheduler and Gear Finder prompts
with curated terrain/climate/elevation context. Never guesses: a match
below the confidence threshold, or any lookup failure, returns no match so
callers fall back to whatever the user/GPX already supplied."""

import json
import re
from dataclasses import dataclass, field
from typing import Any

from rapidfuzz import fuzz

_MIN_NAME_LENGTH = 3
_FUZZY_THRESHOLD = 86.0
_AUTO_APPLY_GAP = 10.0
_CANDIDATE_THRESHOLD = 70.0
_MAX_CANDIDATES = 5
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


@dataclass
class RaceMatchResult:
    matched: bool
    auto_apply: bool
    top: MatchedRace | None
    candidates: list[MatchedRace] = field(default_factory=list)


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


def _normalize(text: str) -> str:
    """Lowercase and treat hyphens/en-dashes as spaces so 'Ultra-Trail
    Australia' matches the 'ultra trail australia' a runner actually types."""
    return re.sub(r"[-\u2013]+", " ", text.lower()).strip()


def _keyword_hit(keyword: str, query: str) -> bool:
    """Word/phrase-boundary match: True if `keyword` appears in `query` as a
    whole word or phrase (not merely as a substring), or vice versa."""
    if not keyword:
        return False
    if re.search(rf"\b{re.escape(keyword)}\b", query):
        return True
    return bool(re.search(rf"\b{re.escape(query)}\b", keyword))


def _lopsided_short_candidate(query: str, candidate: str) -> bool:
    """WRatio's partial-ratio component over-credits a short candidate that is
    merely a substring fragment of a much longer query (e.g. alias "uta"
    scores 90 against "utah 100 endurance run") -- skip fuzzy scoring in that
    lopsided case. Comparisons where both strings are similarly short (e.g.
    "my25" vs "my25") are unaffected: the length-ratio check only trips when
    the candidate is short AND the query is disproportionately longer."""
    candidate = candidate.lower()
    return len(candidate) < 5 and len(query) > 2 * len(candidate)


def _score_chunks(query: str, chunks: list[dict[str, Any]]) -> list[tuple[dict[str, Any], float]]:
    """Scores every chunk against `query` (exact keyword hits score 100.0,
    otherwise the best rapidfuzz WRatio across race_name + aliases), sorted
    highest score first."""
    query = _normalize(query)
    scored: list[tuple[dict[str, Any], float]] = []
    for chunk in chunks:
        payload = _payload_as_dict(chunk.get("payload"))
        keywords = payload.get("matching_hints", {}).get("name_keywords", [])
        if any(_keyword_hit(_normalize(kw), query) for kw in keywords if kw):
            scored.append((chunk, 100.0))
            continue

        candidates = [payload.get("race_name", "")] + list(payload.get("aliases", []))
        score = max(
            (fuzz.WRatio(query, _normalize(c)) for c in candidates if c and not _lopsided_short_candidate(query, c)),
            default=0.0,
        )
        scored.append((chunk, score))

    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored


def _to_matched_race(chunk: dict[str, Any], score: float, resolved_distance_km: float | None) -> MatchedRace:
    payload = _payload_as_dict(chunk.get("payload"))
    distances = payload.get("distances", [])
    distance_entry = None
    if resolved_distance_km is not None:
        distance_entry = _closest_distance_entry(distances, resolved_distance_km)
    elif len(distances) == 1:
        # single-distance races (road marathons etc.) need no disambiguation
        distance_entry = distances[0]

    return MatchedRace(
        race_name=payload.get("race_name", chunk.get("title", "")),
        distance_label=distance_entry.get("label") if distance_entry else None,
        distance_km=distance_entry.get("distance_km") if distance_entry else None,
        elevation_gain_m=distance_entry.get("elevation_gain_m") if distance_entry else None,
        terrain=payload.get("terrain", []),
        course_context=chunk.get("content", ""),
        confidence=score,
    )


def match_race_candidates(
    name: str | None,
    distance_km: float | None = None,
    distance_label: str | None = None,
) -> RaceMatchResult:
    """Scores every race in the curated KB against `name` and decides
    whether the top match clearly dominates (auto_apply=True, no
    candidates) or is ambiguous enough that the caller should let the user
    disambiguate (auto_apply=False, up to 5 candidates scoring >= 70)."""
    empty = RaceMatchResult(matched=False, auto_apply=False, top=None, candidates=[])
    if not name or len(name.strip()) < _MIN_NAME_LENGTH:
        return empty

    import db

    try:
        chunks = db.get_kb_chunks("race_courses", kind="race_profile")
    except Exception as e:
        print(f"[RaceMatcher] Failed to load race_courses KB: {e}")
        return empty
    if not chunks:
        return empty

    query = name.strip().lower()
    scored = _score_chunks(query, chunks)
    if not scored or scored[0][1] < _FUZZY_THRESHOLD:
        return empty

    resolved_distance_km = distance_km if distance_km is not None else _parse_distance_km(distance_label)
    top_chunk, top_score = scored[0]
    top_race = _to_matched_race(top_chunk, top_score, resolved_distance_km)

    second_score = scored[1][1] if len(scored) > 1 else 0.0
    auto_apply = (top_score - second_score) >= _AUTO_APPLY_GAP
    if auto_apply:
        return RaceMatchResult(matched=True, auto_apply=True, top=top_race, candidates=[])

    candidates = [
        _to_matched_race(chunk, score, resolved_distance_km)
        for chunk, score in scored[:_MAX_CANDIDATES]
        if score >= _CANDIDATE_THRESHOLD
    ]
    return RaceMatchResult(matched=True, auto_apply=False, top=top_race, candidates=candidates)


def match_race(
    name: str | None,
    distance_km: float | None = None,
    distance_label: str | None = None,
) -> MatchedRace | None:
    """Backward-compatible single-best-match lookup, used by server-side
    enrichment call sites (_resolve_course_match, gear_planner) that always
    want the top match regardless of how close the runner-up scored."""
    return match_race_candidates(name, distance_km=distance_km, distance_label=distance_label).top


def race_benchmarks(name: str | None, distance_km: float | None = None) -> dict[str, Any] | None:
    """Course-results benchmarks for the Pace Strategy finish-time slider.

    Matches `name` against the KB, reads the hand-curated per-year `results`
    block from the race payload, and (when distance_km is given) keeps only
    entries within ~15% of that distance. Returns None when the race is
    unknown or has no curated results yet."""
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

    scored = _score_chunks(name.strip().lower(), chunks)
    if not scored or scored[0][1] < _FUZZY_THRESHOLD:
        return None

    chunk = scored[0][0]
    payload = _payload_as_dict(chunk.get("payload"))
    results = payload.get("results") or []
    if distance_km is not None:
        results = [
            r for r in results if r.get("distance_km") and abs(r["distance_km"] - distance_km) / distance_km <= 0.15
        ]
    if not results:
        return None
    return {"race_name": payload.get("race_name", chunk.get("title", "")), "results": results}
