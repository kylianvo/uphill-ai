"""Unit tests for session bundling -- pure functions, no DB.

The fixtures below are real fragmented days from a live COROS account
(2026-09-04 spike). They are the specification: seven such days appeared in
three months, five of them crossing sport types.
"""

from datetime import UTC, datetime, timedelta

from services.matching.bundler import (
    BUNDLE_GAP_SECONDS,
    bundle_activities,
)

BASE = datetime(2026, 8, 11, 6, 0, tzinfo=UTC)


def act(offset_s, duration_s, km, activity_type="outdoor_run", id_=None):
    return {
        "id": id_ if id_ is not None else offset_s,
        "start_time": BASE + timedelta(seconds=offset_s),
        "duration_seconds": float(duration_s),
        "distance_km": km,
        "activity_type": activity_type,
        "elevation_gain_m": 0.0,
        "avg_hr": 140,
    }


class TestBundling:
    def test_a_single_activity_is_its_own_bundle(self):
        bundles = bundle_activities([act(0, 3600, 10.0)])
        assert len(bundles) == 1
        assert bundles[0].distance_km == 10.0

    def test_bundles_a_gym_jog_with_the_treadmill_session_across_sport_types(self):
        # 2026-08-11 from the real account: 0.569 km outdoor jog, 5m48s gap,
        # then 10.91 km indoor. Bundling by exact type would miss this.
        jog = act(0, 212, 0.569, "outdoor_run")
        session = act(560, 3652, 10.91, "indoor_run")
        bundles = bundle_activities([jog, session])
        assert len(bundles) == 1
        assert round(bundles[0].distance_km, 2) == 11.48
        assert bundles[0].fragment_count == 2

    def test_bundles_three_fragments_jog_out_session_jog_home(self):
        # 2026-07-01: 0.653 outdoor, 2m19s, 10.61 indoor, 2m45s, 0.625 outdoor.
        frags = [
            act(0, 240, 0.653, "outdoor_run"),
            act(379, 3701, 10.61, "indoor_run"),
            act(4245, 245, 0.625, "outdoor_run"),
        ]
        bundles = bundle_activities(frags)
        assert len(bundles) == 1
        assert bundles[0].fragment_count == 3

    def test_does_not_bundle_across_a_genuine_double_session_day(self):
        morning = act(0, 3600, 10.0)
        evening = act(8 * 3600, 3600, 8.0)
        assert len(bundle_activities([morning, evening])) == 2

    def test_gap_exactly_at_the_threshold_still_bundles(self):
        first = act(0, 600, 2.0)
        second = act(600 + BUNDLE_GAP_SECONDS, 600, 2.0)
        assert len(bundle_activities([first, second])) == 1

    def test_gap_one_second_over_the_threshold_does_not_bundle(self):
        first = act(0, 600, 2.0)
        second = act(600 + BUNDLE_GAP_SECONDS + 1, 600, 2.0)
        assert len(bundle_activities([first, second])) == 2

    def test_does_not_bundle_a_run_with_a_non_run_activity(self):
        run = act(0, 3600, 10.0, "outdoor_run")
        swim = act(3700, 1800, 1.5, "pool_swim")
        assert len(bundle_activities([run, swim])) == 2

    def test_input_order_does_not_matter(self):
        jog = act(0, 212, 0.569, "outdoor_run")
        session = act(560, 3652, 10.91, "indoor_run")
        assert len(bundle_activities([session, jog])) == 1


class TestNoiseFloor:
    def test_a_lone_tiny_fragment_is_still_returned(self):
        # It is all the athlete did; dropping it would erase the day.
        assert len(bundle_activities([act(0, 90, 0.2)])) == 1

    def test_bundle_sums_are_correct(self):
        bundles = bundle_activities([act(0, 600, 2.0), act(900, 600, 3.0)])
        assert bundles[0].duration_seconds == 1200.0
        assert bundles[0].distance_km == 5.0


class TestBundleIdentity:
    def test_bundle_exposes_its_member_activity_ids(self):
        bundles = bundle_activities([act(0, 212, 0.5, id_=11), act(560, 3652, 10.9, id_=22)])
        assert bundles[0].activity_ids == [11, 22]

    def test_bundle_start_time_is_the_earliest_fragment(self):
        bundles = bundle_activities([act(0, 212, 0.5), act(560, 3652, 10.9)])
        assert bundles[0].start_time == BASE


class TestOverlappingFragments:
    """A watch can log a short activity inside a longer one's window.

    The session's end is the latest end among its members, not the end of the
    member that started last. Measuring the gap from the wrong one splits a
    session that plainly overlaps itself.
    """

    def test_a_contained_fragment_does_not_reset_the_session_end(self):
        # 06:00-07:00 long run, a 06:05-06:10 blip inside it, then 06:50 -- which
        # starts BEFORE the long run has even finished.
        bundles = bundle_activities([act(0, 3600, 10.0, id_=1), act(300, 300, 0.5, id_=2), act(3000, 1200, 3.0, id_=3)])
        assert len(bundles) == 1
        assert bundles[0].activity_ids == [1, 2, 3]


class TestWeightedHeartRate:
    def test_avg_hr_is_weighted_by_duration_not_a_plain_mean(self):
        # 60 min @ 140 and 30 min @ 170 -> 150, where a plain mean would give 155.
        a, b = act(0, 3600, 10.0), act(3600, 1800, 5.0)
        a["avg_hr"], b["avg_hr"] = 140, 170
        assert bundle_activities([a, b])[0].avg_hr == 150

    def test_fragments_without_hr_are_excluded_from_the_weighting(self):
        a, b = act(0, 3600, 10.0), act(3600, 1800, 5.0)
        a["avg_hr"], b["avg_hr"] = 150, None
        assert bundle_activities([a, b])[0].avg_hr == 150

    def test_avg_hr_is_none_when_no_fragment_reports_one(self):
        a, b = act(0, 3600, 10.0), act(3600, 1800, 5.0)
        a["avg_hr"] = b["avg_hr"] = None
        assert bundle_activities([a, b])[0].avg_hr is None


class TestWarmupBundling:
    def test_bundles_warmup_jog_with_main_session_within_40_minutes(self):
        # 0.6 km jog to gym, 40 minute gap, then 10 km run
        jog = act(0, 240, 0.6, id_=1)
        main_run = act(240 + 40 * 60, 3600, 10.0, id_=2)
        bundles = bundle_activities([jog, main_run])
        assert len(bundles) == 1
        assert bundles[0].fragment_count == 2
        assert round(bundles[0].distance_km, 1) == 10.6
        assert bundles[0].primary_activity_id == 2
        assert bundles[0].warmup_distance_km == 0.6
