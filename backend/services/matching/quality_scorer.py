"""Workout Execution Quality Scoring Engine.

Evaluates how faithfully and effectively an athlete executed a planned workout,
grounded in the coaching principles of Steve House & Scott Johnston's
"Training for the Uphill Athlete":

1. Volume Adherence: hitting the prescribed duration and distance within a
   sensible sweet spot (90-110%), while discouraging excessive over-mileage.
2. Intensity Discipline (Polarized Rules):
   - Easy / Recovery / Aerobic Base (Zone 1 / Zone 2): strictly staying below the
     Aerobic Threshold (AeT). Spiking heart rate or running too fast on easy days
     drifts into the "grey zone" and causes Aerobic Deficiency Syndrome (ADS) --
     so going too fast on recovery runs is actively penalized.
   - Quality / Tempo / Threshold / Intervals (Zone 3 / 4 / 5): evaluating attainment
     and consistency in the prescribed pace / HR zones without fading.
   - Strength / Muscular Endurance: completing prescribed duration and sets with
     controlled cardiovascular strain.
3. Terrain / Elevation Adherence: assessing vert gained for mountain runs.
4. A-F Grading Heuristic & Automated Coaching Takeaways:
   Produces a 0-100 score, letter grade (A/B/C/D/F), rating label, and actionable
   coaching bullet points.
"""

from dataclasses import dataclass, field
from typing import Any

from services.matching.bundler import SessionBundle
from services.matching.scorer import parse_hr_range, parse_pace_to_seconds


@dataclass
class WorkoutQualityResult:
    overall_score: float  # 0.0 to 100.0
    grade: str  # "A", "B", "C", "D", "F"
    rating: str  # "Outstanding Execution", "Good Execution", etc.
    subscores: dict[str, float]  # e.g. {"volume": 0.95, "intensity": 0.90}
    takeaways: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_score": round(self.overall_score, 1),
            "grade": self.grade,
            "rating": self.rating,
            "subscores": {k: round(v, 2) for k, v in self.subscores.items()},
            "takeaways": self.takeaways,
        }


def _grade_for_score(score: float) -> tuple[str, str]:
    if score >= 90.0:
        return "A", "Outstanding Execution"
    elif score >= 80.0:
        return "B", "Good Execution"
    elif score >= 70.0:
        return "C", "Moderate Adherence"
    elif score >= 60.0:
        return "D", "Needs Adjustment"
    else:
        return "F", "Underperformed"


def _volume_score(
    actual_minutes: float,
    planned_minutes: float | None,
    actual_km: float | None,
    planned_km: float | None,
) -> tuple[float, list[str]]:
    """Evaluates duration and distance completion."""
    takeaways: list[str] = []
    scores: list[float] = []

    if planned_minutes and planned_minutes > 0:
        ratio = actual_minutes / planned_minutes
        if 0.90 <= ratio <= 1.10:
            scores.append(1.0)
            takeaways.append(
                f"Volume on target: completed {actual_minutes:.0f}m of {planned_minutes:.0f}m planned ({ratio * 100:.0f}%)."
            )
        elif ratio < 0.90:
            score = max(0.2, ratio / 0.90)
            scores.append(score)
            takeaways.append(
                f"Cut short: completed {actual_minutes:.0f}m vs {planned_minutes:.0f}m prescribed ({ratio * 100:.0f}%)."
            )
        else:
            # Over-duration (> 110%): mild penalty to discourage unprescribed junk volume
            over = ratio - 1.10
            score = max(0.5, 1.0 - over * 0.8)
            scores.append(score)
            takeaways.append(f"Extended session: ran {actual_minutes:.0f}m vs {planned_minutes:.0f}m prescribed.")

    if planned_km and planned_km > 0 and actual_km is not None and actual_km > 0:
        ratio = actual_km / planned_km
        if 0.92 <= ratio <= 1.08:
            scores.append(1.0)
        elif ratio < 0.92:
            scores.append(max(0.2, ratio / 0.92))
        else:
            over = ratio - 1.08
            scores.append(max(0.5, 1.0 - over * 0.8))

    if not scores:
        return 1.0, takeaways
    return sum(scores) / len(scores), takeaways


def _intensity_score_easy_run(
    avg_hr: int | None,
    target_hr_range: tuple[int, int] | None,
    aet_hr: float | None,
    actual_pace_sec: float | None,
    target_pace_sec: float | None,
) -> tuple[float, list[str]]:
    """Uphill Athlete Polarized Rules:

    Going too hard on easy/recovery days destroys aerobic adaptation.
    """
    scores: list[float] = []
    takeaways: list[str] = []

    ceiling_hr = None
    if aet_hr and aet_hr > 0:
        ceiling_hr = aet_hr
    elif target_hr_range:
        ceiling_hr = target_hr_range[1]

    if avg_hr and ceiling_hr:
        if avg_hr <= ceiling_hr:
            scores.append(1.0)
            takeaways.append(
                f"Strict Zone 2 discipline: Avg HR of {avg_hr} bpm stayed safely under your aerobic ceiling of {int(ceiling_hr)} bpm."
            )
        elif avg_hr <= ceiling_hr + 5:
            scores.append(0.85)
            takeaways.append(
                f"Slight cardiac drift: Avg HR of {avg_hr} bpm was slightly over your {int(ceiling_hr)} bpm aerobic ceiling."
            )
        elif avg_hr <= ceiling_hr + 12:
            scores.append(0.65)
            takeaways.append(
                f"Grey Zone warning: Avg HR of {avg_hr} bpm exceeded aerobic ceiling ({int(ceiling_hr)} bpm). Keep easy days truly easy!"
            )
        else:
            scores.append(0.40)
            takeaways.append(
                f"High intensity on recovery day: Avg HR of {avg_hr} bpm was far above your {int(ceiling_hr)} bpm ceiling."
            )

    if actual_pace_sec and target_pace_sec:
        # On easy days, running significantly faster than target pace is a mistake
        if actual_pace_sec < target_pace_sec * 0.90:  # > 10% faster
            diff_sec = int(target_pace_sec - actual_pace_sec)
            scores.append(0.70)
            takeaways.append(f"Over-paced for an easy run: Ran {diff_sec}s/km faster than prescribed recovery pace.")
        elif actual_pace_sec > target_pace_sec * 1.25:  # > 25% slower
            scores.append(0.75)
            takeaways.append("Pace was significantly slower than prescribed aerobic target.")
        else:
            scores.append(1.0)

    if not scores:
        return 1.0, takeaways
    return sum(scores) / len(scores), takeaways


def _intensity_score_quality_run(
    avg_hr: int | None,
    target_hr_range: tuple[int, int] | None,
    ant_hr: float | None,
    actual_pace_sec: float | None,
    target_pace_sec: float | None,
) -> tuple[float, list[str]]:
    """Tempo / Threshold / Interval workout scoring."""
    scores: list[float] = []
    takeaways: list[str] = []

    if target_hr_range and avg_hr:
        low, high = target_hr_range
        if low <= avg_hr <= high:
            scores.append(1.0)
            takeaways.append(f"Target heart rate nailed: Avg HR of {avg_hr} bpm was inside target {low}-{high} bpm.")
        elif avg_hr < low:
            diff = low - avg_hr
            score = max(0.5, 1.0 - (diff / 25.0))
            scores.append(score)
            takeaways.append(f"Under target intensity: Avg HR of {avg_hr} bpm was {diff} bpm below threshold range.")
        else:
            diff = avg_hr - high
            score = max(0.6, 1.0 - (diff / 25.0))
            scores.append(score)
            takeaways.append(
                f"Pushed past target threshold: Avg HR of {avg_hr} bpm exceeded upper target ({high} bpm)."
            )

    if actual_pace_sec and target_pace_sec:
        rel_diff = abs(actual_pace_sec - target_pace_sec) / target_pace_sec
        if rel_diff <= 0.05:
            scores.append(1.0)
            takeaways.append("Pacing accuracy: Maintained prescribed interval/tempo pace within 5%.")
        elif actual_pace_sec > target_pace_sec:  # Slower
            scores.append(max(0.4, 1.0 - rel_diff * 2.0))
            takeaways.append(f"Interval pace dropped below prescription ({rel_diff * 100:.0f}% slower than target).")
        else:  # Faster
            scores.append(max(0.75, 1.0 - rel_diff))
            takeaways.append("Target pace achieved with strong finish.")

    if not scores:
        return 1.0, takeaways
    return sum(scores) / len(scores), takeaways


def _intensity_score_strength(
    actual_minutes: float,
    planned_minutes: float | None,
    avg_hr: int | None,
    sets: int | None,
) -> tuple[float, list[str]]:
    """Strength / Gym session scoring."""
    scores: list[float] = []
    takeaways: list[str] = []

    if planned_minutes and planned_minutes > 0:
        ratio = actual_minutes / planned_minutes
        if 0.85 <= ratio <= 1.25:
            scores.append(1.0)
            takeaways.append(f"Gym session completed: {actual_minutes:.0f}m workout.")
        else:
            scores.append(max(0.4, min(1.0, ratio)))

    if avg_hr:
        if avg_hr <= 135:
            scores.append(1.0)
            takeaways.append(f"Controlled cardiovascular strain during strength work (avg HR {avg_hr} bpm).")
        elif avg_hr > 150:
            scores.append(0.75)
            takeaways.append(
                f"High cardiovascular load during gym session (avg HR {avg_hr} bpm). Ensure adequate rest between sets."
            )

    if sets and sets > 1:
        takeaways.append(f"Logged {sets} strength sets.")

    if not scores:
        return 1.0, takeaways
    return sum(scores) / len(scores), takeaways


def score_workout_quality(
    workout: dict,
    activity: dict | SessionBundle,
    athlete_profile: dict[str, Any] | None = None,
) -> WorkoutQualityResult:
    """Computes a multi-factor Workout Execution Quality Score (0-100 & A-F grade)."""
    profile = athlete_profile or {}

    # Extract activity values
    if isinstance(activity, SessionBundle):
        duration_s = activity.duration_seconds
        distance_km = activity.distance_km
        elevation_m = activity.elevation_gain_m
        avg_hr = activity.avg_hr
        activity_type = list(activity.activity_types)[0] if activity.activity_types else "run"
        warmup_km = activity.warmup_distance_km
        sets = None
    else:
        duration_s = float(activity.get("duration_seconds") or 0.0)
        distance_km = float(activity.get("distance_km")) if activity.get("distance_km") is not None else None
        elevation_m = float(activity.get("elevation_gain_m") or 0.0)
        avg_hr = activity.get("avg_hr")
        activity_type = activity.get("activity_type", "run")
        warmup_km = float(activity.get("warmup_distance_km") or 0.0)
        sets = activity.get("sets")

    actual_minutes = duration_s / 60.0
    planned_minutes = workout.get("duration_minutes")
    planned_km = workout.get("distance_km")
    planned_elev = workout.get("elevation_gain_m")

    # Workout classification
    w_type = (workout.get("type") or "").upper()
    w_title = (workout.get("title") or "").lower()
    is_strength = (
        "STRENGTH" in w_type
        or "GYM" in w_type
        or "MUSCULAR ENDURANCE" in w_type
        or any(s in w_title for s in ["strength", "gym", "circuit", "muscular endurance"])
        or activity_type in {"strength", "indoor_strength", "gym_cardio"}
    )
    is_easy = not is_strength and (
        "EASY" in w_type
        or "RECOVERY" in w_type
        or "BASE" in w_type
        or "LONG" in w_type
        or "AEROBIC" in w_title
        or "zone 1" in w_title
        or "zone 2" in w_title
    )

    all_takeaways: list[str] = []

    # 1. Volume Score
    volume_score, vol_notes = _volume_score(actual_minutes, planned_minutes, distance_km, planned_km)
    all_takeaways.extend(vol_notes)

    # 2. Intensity Score
    target_hr_range = parse_hr_range(workout.get("target_hr_range"))
    target_pace_sec = parse_pace_to_seconds(workout.get("target_pace"))
    actual_pace_sec = (duration_s / distance_km) if (distance_km and distance_km > 0) else None
    aet_hr = profile.get("aet_hr")
    ant_hr = profile.get("ant_hr")

    if is_strength:
        intensity_score, int_notes = _intensity_score_strength(actual_minutes, planned_minutes, avg_hr, sets)
    elif is_easy:
        intensity_score, int_notes = _intensity_score_easy_run(
            avg_hr, target_hr_range, aet_hr, actual_pace_sec, target_pace_sec
        )
    else:
        # Quality / Tempo / Interval
        intensity_score, int_notes = _intensity_score_quality_run(
            avg_hr, target_hr_range, ant_hr, actual_pace_sec, target_pace_sec
        )
    all_takeaways.extend(int_notes)

    # 3. Elevation Score (if mountain run with >50m prescribed climbing)
    subscores: dict[str, float] = {
        "volume": volume_score,
        "intensity": intensity_score,
    }

    if planned_elev and planned_elev > 50 and elevation_m is not None:
        elev_ratio = min(1.2, elevation_m / planned_elev)
        elev_score = max(0.4, 1.0 - abs(1.0 - elev_ratio))
        subscores["elevation"] = elev_score
        if elevation_m >= planned_elev * 0.9:
            all_takeaways.append(f"Climbing vert hit: gained {elevation_m:.0f}m vs {planned_elev:.0f}m target.")

    # Bundled warm-up note
    if warmup_km > 0:
        all_takeaways.append(f"Included {warmup_km:.1f} km warm-up jog in the total workout volume.")

    # Weighted Overall Score
    if "elevation" in subscores:
        overall = subscores["volume"] * 0.35 + subscores["intensity"] * 0.45 + subscores["elevation"] * 0.20
    else:
        overall = subscores["volume"] * 0.45 + subscores["intensity"] * 0.55

    overall_100 = max(10.0, min(100.0, overall * 100.0))
    grade, rating = _grade_for_score(overall_100)

    return WorkoutQualityResult(
        overall_score=overall_100,
        grade=grade,
        rating=rating,
        subscores=subscores,
        takeaways=all_takeaways,
    )
