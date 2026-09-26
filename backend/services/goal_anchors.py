"""Numeric anchors for the LLM goal judge (docs/superpowers/specs/
2026-09-26-llm-goal-estimation-design.md).

Deterministic maths only: resolves the target course from the race KB and
turns each usable past result into one or more finish-time anchors on that
course. The judge (services/goal_judge.py) weighs these; it never does the
arithmetic itself. Anchors describe *current* fitness -- no time-to-race
improvement is applied here.
"""

from datetime import date
from typing import Any

from services.race_estimator import RaceEstimator, _parse_hms_to_mins

# Results older than this are not turned into anchors (still shown as history).
MAX_ANCHOR_AGE_YEARS = 4
MAX_ANCHOR_RESULTS = 6

# Field-position prior for athletes without usable results: weekly volume ->
# expected field percentile on the target race (lower = faster). A coarse
# heuristic by design; the judge is told it is a prior, and confidence is low.
_VOLUME_PERCENTILE = ((70.0, 40.0), (50.0, 55.0), (30.0, 70.0), (0.0, 85.0))
_ULTRA_EXPERIENCE_BONUS = 10.0


def _variant_filtered_results(
    results: list[dict[str, Any]], variants: dict[int, str | None], target_variant: str | None
) -> list[dict[str, Any]]:
    """Same rule as main._variant_filtered_results: only pool result-years
    whose curated course-profile variant matches the target's."""
    if not target_variant:
        return results
    return [r for r in results if variants.get(r.get("year")) == target_variant]


def resolve_course(
    race_name: str | None,
    distance_km: float | None,
    elevation_gain_m: float | None,
    before_year: int | None = None,
) -> dict[str, Any]:
    """Target (or reference) course: KB match, GPX checkpoints, terrain and
    the field curve. Explicit numbers win over the KB's; 0 counts as missing.
    `before_year` keeps only field years before it (the backtest's hold-out
    race must not see its own year's results)."""
    from services.race_matcher import course_profile, course_profile_variants, match_race, race_benchmarks

    matched = match_race(race_name, distance_km=distance_km) if race_name else None
    distance = distance_km or (matched.distance_km if matched else None)
    gain = elevation_gain_m or (matched.elevation_gain_m if matched else None) or 0.0
    profile = course_profile(race_name, matched.distance_label) if matched and matched.distance_label else None
    course: dict[str, Any] = {
        "race_name": matched.race_name if matched else race_name,
        "matched": matched is not None,
        "distance_km": distance,
        "elevation_gain_m": gain,
        "distance_label": matched.distance_label if matched else None,
        "terrain": matched.terrain if matched else [],
        "key_climbs": (matched.course_intelligence or {}).get("key_climbs", []) if matched else [],
        "climate": (matched.course_intelligence or {}).get("climate", {}) if matched else {},
        "location": (matched.course_intelligence or {}).get("location", "") if matched else "",
        "checkpoints": profile["checkpoints"] if profile else None,
        "profile_source": "gpx" if profile else "synthetic",
        "field": None,
    }
    if not race_name or not distance:
        return course
    bench = race_benchmarks(race_name, distance_km=distance)
    if not bench:
        return course
    variants = course_profile_variants(race_name, matched.distance_label) if matched and matched.distance_label else {}
    results = _variant_filtered_results(bench["results"], variants, profile["variant"] if profile else None)
    if before_year:
        results = [r for r in results if (r.get("year") or 0) < before_year]
    curve = RaceEstimator.percentile_curve(results)
    winners = [m for m in (_parse_hms_to_mins(r.get("winner_time")) for r in results) if m]
    course["field"] = {
        "years": sorted({r.get("year") for r in results if r.get("year")}, reverse=True),
        "curve": curve[0] if curve else None,
        "winner_mins": winners[0] if winners else None,
        "fastest_winner_mins": min(winners) if winners else None,
        "finishers": results[0].get("finishers") if results else None,
    }
    return course


def _age_years(race_date: str, as_of: date) -> float:
    return (as_of - date.fromisoformat(race_date[:10])).days / 365.25


def select_anchor_results(results: list[dict[str, Any]], target_km: float, as_of: date) -> list[dict[str, Any]]:
    """Finished results recent enough to anchor on, most relevant first:
    trail before road, then closeness in distance, then recency."""
    usable = [
        r
        for r in results
        if not r.get("is_dnf")
        and r.get("finish_time_sec")
        and r.get("distance_km")
        and _age_years(r["race_date"], as_of) <= MAX_ANCHOR_AGE_YEARS
    ]

    def relevance(r: dict[str, Any]) -> tuple[int, float, float]:
        ratio = max(r["distance_km"], target_km) / max(min(r["distance_km"], target_km), 0.1)
        return (0 if r.get("discipline") == "trail" else 1, round(ratio, 1), _age_years(r["race_date"], as_of))

    return sorted(usable, key=relevance)[:MAX_ANCHOR_RESULTS]


def _quality_notes(r: dict[str, Any], target_km: float, as_of: date, ref_profile: str) -> list[str]:
    notes = [f"{_age_years(r['race_date'], as_of):.1f} years old"]
    ratio = r["distance_km"] / target_km if target_km else 1.0
    if ratio < 0.5 or ratio > 2.0:
        notes.append(f"distance {r['distance_km']:.0f} km vs target {target_km:.0f} km")
    if r.get("discipline") == "road":
        notes.append("road result")
    if ref_profile == "synthetic":
        notes.append("reference course profile synthetic")
    if r.get("source") == "manual":
        notes.append("self-reported")
    return notes


def compute_anchors(
    target: dict[str, Any],
    results: list[dict[str, Any]],
    *,
    weekly_km: float | None = None,
    ultra_finishes: int = 0,
    easy_pace_min_km: float | None = None,
    base_pace_min_km: float | None = None,
    as_of: date | None = None,
) -> list[dict[str, Any]]:
    """Finish-time anchors on the target course.

    Per usable result: a physics anchor (course-normalised base pace), a
    field-rank anchor (the result's own overall rank mapped onto the target's
    field curve) and a percentile-transfer anchor (when the reference race has
    a curated curve too). Without any result anchors: a field-position prior
    from weekly volume, or a physics anchor from the athlete's easy pace."""
    as_of = as_of or date.today()
    target_km = target["distance_km"]
    field = target.get("field") or {}
    target_curve = field.get("curve")
    anchors: list[dict[str, Any]] = []
    if base_pace_min_km:
        anchors.append(
            _pace_anchor(target, "base_pace", base_pace_min_km, f"flat base pace {base_pace_min_km:.2f} min/km")
        )

    for r in select_anchor_results(results, target_km, as_of):
        ref = resolve_course(r["race_name"], r["distance_km"], r.get("elevation_gain_m"))
        finish_mins = r["finish_time_sec"] / 60
        notes = _quality_notes(r, target_km, as_of, ref["profile_source"])
        estimate = RaceEstimator.estimate(
            distance_km=target_km,
            elevation_gain_m=target["elevation_gain_m"],
            reference={
                "distance_km": r["distance_km"],
                "elevation_gain_m": r.get("elevation_gain_m") or 0.0,
                "finish_time_mins": finish_mins,
                "terrain_tags": ref["terrain"] or None,
                "checkpoints": ref["checkpoints"],
            },
            terrain_tags=target["terrain"] or None,
            target_checkpoints=target["checkpoints"],
        )
        base = {"source_result_id": r.get("id"), "notes": notes}
        anchors.append(
            {"id": f"phys_r{r.get('id')}", "method": "physics", "minutes": estimate["predicted_time_mins"], **base}
        )
        if target_curve and r.get("rank_overall") and r.get("total_overall"):
            pct = min(99.0, 100.0 * r["rank_overall"] / r["total_overall"])
            minutes = RaceEstimator.interpolate_percentile(target_curve, percentile=pct)
            anchors.append(
                {
                    "id": f"rank_r{r.get('id')}",
                    "method": "field_rank",
                    "minutes": round(minutes, 1),
                    **base,
                    "notes": [*notes, f"finished p{pct:.0f} of {r['total_overall']}"],
                }
            )
        ref_curve = (ref.get("field") or {}).get("curve")
        if target_curve and ref_curve:
            minutes = RaceEstimator.percentile_transfer_mins(ref_curve, finish_mins, target_curve)
            anchors.append(
                {"id": f"pct_r{r.get('id')}", "method": "percentile_transfer", "minutes": round(minutes, 1), **base}
            )

    if anchors:
        return anchors

    if target_curve and weekly_km is not None:
        pct = next(p for floor, p in _VOLUME_PERCENTILE if weekly_km >= floor)
        if ultra_finishes:
            pct -= _ULTRA_EXPERIENCE_BONUS
        anchors.append(
            {
                "id": "prior_field",
                "method": "field_prior",
                "minutes": round(RaceEstimator.interpolate_percentile(target_curve, percentile=pct), 1),
                "source_result_id": None,
                "notes": [f"prior: {weekly_km:.0f} km/week maps to about p{pct:.0f} of this field"],
            }
        )
    elif easy_pace_min_km:
        anchors.append(
            _pace_anchor(
                target, "easy_pace", easy_pace_min_km, f"prior: profile easy pace {easy_pace_min_km:.2f} min/km"
            )
        )
    return anchors


def _pace_anchor(target: dict[str, Any], method: str, pace_min_km: float, note: str) -> dict[str, Any]:
    estimate = RaceEstimator.estimate(
        distance_km=target["distance_km"],
        elevation_gain_m=target["elevation_gain_m"],
        base_flat_pace_min_km=pace_min_km,
        terrain_tags=target["terrain"] or None,
        target_checkpoints=target["checkpoints"],
    )
    return {
        "id": f"prior_{method}" if method == "easy_pace" else method,
        "method": method,
        "minutes": estimate["predicted_time_mins"],
        "source_result_id": None,
        "notes": [note],
    }
