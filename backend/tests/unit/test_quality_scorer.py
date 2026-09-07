"""Unit tests for the Workout Execution Quality Scoring Engine."""

from datetime import UTC, datetime

from services.matching.bundler import SessionBundle
from services.matching.quality_scorer import score_workout_quality


def make_bundle(duration_min=60.0, km=10.0, avg_hr=138, warmup_km=0.0, activity_type="outdoor_run"):
    return SessionBundle(
        start_time=datetime(2026, 9, 6, 6, 0, tzinfo=UTC),
        duration_seconds=duration_min * 60.0,
        distance_km=km,
        elevation_gain_m=50.0,
        avg_hr=avg_hr,
        activity_ids=[1],
        activity_types={activity_type},
        warmup_distance_km=warmup_km,
    )


def make_workout(
    type_="EASY", title="Aerobic Base Run", duration_min=60.0, km=10.0, target_hr="130-145", target_pace="6:00"
):
    return {
        "id": 101,
        "type": type_,
        "title": title,
        "duration_minutes": duration_min,
        "distance_km": km,
        "target_hr_range": target_hr,
        "target_pace": target_pace,
        "elevation_gain_m": 50.0,
    }


class TestQualityScorerEasyRuns:
    def test_strict_zone2_discipline_scores_grade_a(self):
        w = make_workout(
            type_="EASY", title="Aerobic Base Run", duration_min=60.0, km=10.0, target_hr="130-145", target_pace="6:00"
        )
        b = make_bundle(duration_min=61.0, km=10.1, avg_hr=138)
        profile = {"aet_hr": 142, "ant_hr": 165}

        res = score_workout_quality(w, b, profile)
        assert res.grade == "A"
        assert res.overall_score >= 90.0
        assert any("strict zone 2 discipline" in t.lower() for t in res.takeaways)

    def test_running_too_fast_or_high_hr_on_easy_day_is_penalized(self):
        # Runner ran 4:45 pace on a 6:00 recovery run with HR at 160 (way above AeT of 142)
        w = make_workout(
            type_="RECOVERY", title="Recovery Jog", duration_min=45.0, km=7.5, target_hr="120-135", target_pace="6:00"
        )
        b = make_bundle(duration_min=35.0, km=7.5, avg_hr=160)
        profile = {"aet_hr": 138, "ant_hr": 165}

        res = score_workout_quality(w, b, profile)
        assert res.overall_score < 75.0
        assert res.grade in {"C", "D"}
        assert any(
            "grey zone" in t.lower() or "over-paced" in t.lower() or "exceeded" in t.lower() for t in res.takeaways
        )


class TestQualityScorerQualityRuns:
    def test_tempo_workout_hitting_targets_scores_high(self):
        w = make_workout(
            type_="TEMPO",
            title="60m Sub-Threshold Tempo",
            duration_min=60.0,
            km=12.0,
            target_hr="155-168",
            target_pace="5:00",
        )
        b = make_bundle(duration_min=60.0, km=12.0, avg_hr=162)
        profile = {"aet_hr": 142, "ant_hr": 168}

        res = score_workout_quality(w, b, profile)
        assert res.grade == "A"
        assert res.overall_score >= 90.0
        assert any("target heart rate nailed" in t.lower() or "pacing" in t.lower() for t in res.takeaways)


class TestQualityScorerStrengthWorkouts:
    def test_strength_session_with_controlled_hr_scores_grade_a(self):
        w = {
            "id": 102,
            "type": "STRENGTH",
            "title": "Gym Muscular Endurance Circuit Progression",
            "duration_minutes": 60.0,
            "distance_km": None,
            "target_hr_range": None,
            "target_pace": None,
            "elevation_gain_m": 0.0,
        }
        activity = {
            "duration_seconds": 3800.0,  # ~63 min
            "distance_km": None,
            "elevation_gain_m": 0.0,
            "avg_hr": 112,
            "activity_type": "strength",
            "sets": 3,
        }
        res = score_workout_quality(w, activity)
        assert res.grade == "A"
        assert res.overall_score >= 90.0
        assert any("strength" in t.lower() or "gym" in t.lower() for t in res.takeaways)


class TestQualityScorerWarmupBundling:
    def test_bundled_warmup_is_reflected_in_takeaways(self):
        w = make_workout(type_="EASY", duration_min=60.0, km=10.0)
        b = make_bundle(duration_min=63.0, km=10.6, avg_hr=138, warmup_km=0.6)
        res = score_workout_quality(w, b)
        assert any("0.6 km warm-up" in t for t in res.takeaways)
