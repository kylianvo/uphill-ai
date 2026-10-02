"""Snapshot priority rules. DB is stubbed; the pure volume rule is tested directly."""

from datetime import UTC, date, datetime, timedelta

import pytest

from services import fitness_snapshot as fs

TODAY = date(2026, 10, 2)  # Thursday; current week starts Mon Sep 28
WEEKS = [
    {"week_start": date(2026, 8, 31), "km": 148.7, "vert_m": 8146.0},
    {"week_start": date(2026, 9, 7), "km": 125.5, "vert_m": 1837.0},
    {"week_start": date(2026, 9, 14), "km": 126.8, "vert_m": 5808.0},
    {"week_start": date(2026, 9, 21), "km": 27.5, "vert_m": 0.0},
]
FIRST = datetime(2026, 8, 23, tzinfo=UTC)


class TestMeasuredWeeklyVolume:
    def test_partial_week_after_last_sync_is_excluded(self):
        """REGRESSION: sync stopped Sep 25, so the Sep 21 week (27.5 km) is incomplete."""
        km, vert, end = fs.measured_weekly_volume(WEEKS, FIRST, datetime(2026, 9, 25, 1, 54, tzinfo=UTC), TODAY)
        assert km == pytest.approx((148.7 + 125.5 + 126.8) / 3, abs=0.1)
        assert end == date(2026, 9, 20)

    def test_covered_week_without_activity_counts_as_zero(self):
        weeks = [w for w in WEEKS if w["week_start"] != date(2026, 9, 7)]
        km, _, _ = fs.measured_weekly_volume(weeks, FIRST, datetime(2026, 10, 1, tzinfo=UTC), TODAY)
        assert km == pytest.approx((148.7 + 0 + 126.8 + 27.5) / 4, abs=0.1)

    def test_weeks_before_the_first_synced_activity_do_not_count(self):
        assert fs.measured_weekly_volume(WEEKS, datetime(2026, 9, 10, tzinfo=UTC), datetime(2026, 10, 1, tzinfo=UTC), TODAY) is None

    def test_fewer_than_three_weeks_returns_none(self):
        assert fs.measured_weekly_volume(WEEKS, FIRST, datetime(2026, 9, 15, tzinfo=UTC), TODAY) is None

    def test_no_sync_returns_none(self):
        assert fs.measured_weekly_volume(WEEKS, FIRST, None, TODAY) is None


@pytest.fixture
def stub_db(monkeypatch):
    state = {
        "user": {"id": 30, "current_weekly_km": 120.0, "threshold_pace": "4:10", "threshold_source": "unknown",
                 "gender": None, "aet_hr": 134, "ant_hr": 163},
        "connection": {"status": "active", "last_sync_at": datetime(2026, 9, 25, 1, 54, tzinfo=UTC)},
        "assessment": {"vo2max": 61.0, "running_level": 92.0, "threshold_pace": "3:53", "pred_marathon_sec": 10320.0,
                       "pred_hm_sec": 4860.0, "measured_at": datetime(2026, 9, 25, tzinfo=UTC)},
        "utmb": None,
    }
    monkeypatch.setattr(fs.db, "get_user_by_id", lambda uid: state["user"])
    monkeypatch.setattr(fs.db, "get_connection", lambda uid, p: state["connection"])
    monkeypatch.setattr(fs.db, "get_latest_fitness_assessment", lambda uid: state["assessment"])
    monkeypatch.setattr(fs.db, "get_weekly_run_volumes", lambda uid, since: WEEKS)
    monkeypatch.setattr(fs.db, "get_first_activity_at", lambda uid, p: FIRST)
    monkeypatch.setattr(fs.db, "get_utmb_index", lambda uid: state["utmb"])
    monkeypatch.setattr(fs.db, "get_recent_readiness_summary", lambda uid, days=7: {"days_recorded": 0})
    return state


class TestBuild:
    def test_measured_volume_beats_profile_value(self, stub_db):
        snap = fs.build(30, today=TODAY)
        assert snap.weekly_km_source == "coros"
        assert snap.weekly_km == pytest.approx(133.7, abs=0.1)

    def test_measured_volume_beats_a_typed_prefill(self, stub_db):
        assert fs.build(30, typed_weekly_km=90.0, today=TODAY).weekly_km_source == "coros"

    def test_athlete_override_wins(self, stub_db):
        snap = fs.build(30, typed_weekly_km=90.0, typed_is_override=True, today=TODAY)
        assert (snap.weekly_km, snap.weekly_km_source) == (90.0, "self_reported")
        assert any("athlete override" in n for n in snap.notes)

    def test_no_connection_falls_back_to_typed_then_profile(self, stub_db):
        stub_db["connection"] = None
        assert fs.build(30, typed_weekly_km=80.0, today=TODAY).weekly_km == 80.0
        assert fs.build(30, today=TODAY).weekly_km == 120.0

    def test_fresh_assessment_threshold_pace_beats_typed(self, stub_db):
        snap = fs.build(30, today=TODAY)
        assert (snap.threshold_pace, snap.threshold_pace_source) == ("3:53", "coros")

    def test_stale_assessment_is_ignored(self, stub_db):
        stub_db["assessment"]["measured_at"] = datetime(2026, 7, 1, tzinfo=UTC)
        snap = fs.build(30, today=TODAY)
        assert snap.assessment is None
        assert (snap.threshold_pace, snap.threshold_pace_source) == ("4:10", "self_reported")

    def test_regression_tier_is_not_recreational(self, stub_db):
        snap = fs.build(30, today=TODAY)
        tier = snap.resolve_tier(None, "race", None, 80.0, 134, 163)
        assert tier in ("sub_elite", "elite")
        assert snap.to_dict()["tier"] == tier

    def test_prompt_block_lists_sources_and_skips_missing(self, stub_db):
        snap = fs.build(30, today=TODAY)
        snap.resolve_tier(None, "race", None, None, 134, 163)
        block = snap.prompt_block("en")
        assert block.startswith("ATHLETE FITNESS SNAPSHOT")
        assert "134 km/week" in block and "COROS" in block
        assert "Marathon prediction 2:52:00" in block
        assert "UTMB" not in block
        assert "not used" in block
