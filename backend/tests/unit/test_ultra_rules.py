from services import ultra_rules as u
from services.plan_generator import PlanGenerator


def test_band_edges():
    assert u.band_for(44.9) is None
    assert u.band_for(45) == "50k" and u.band_for(89.99) == "50k"
    assert u.band_for(90) == "100k" and u.band_for(98) == "100k" and u.band_for(139.9) == "100k"
    assert u.band_for(140) == "100mi" and u.band_for(None) is None


def test_applies_needs_a_mountain_day():
    assert u.applies(100, ()) is None
    assert u.applies(100, ("Saturday",)) == "100k"


def test_100k_ladder_20_weeks():
    lad = u.ladder("100k", False, 20)  # peak_week = 20 - 3 - 1 = 16; deloads 4, 8, 12
    assert [lad[w] for w in (1, 2, 3, 5)] == [180, 180, 240, 240]
    assert lad[4] == lad[8] == lad[12] == 240
    assert lad[15] == 360 and lad[16] == 420
    assert set(lad) == set(range(1, 17))


def test_100mi_advanced_peaks_at_8h_and_50k_at_5h():
    assert u.ladder("100mi", True, 20)[16] == 480
    assert u.ladder("100mi", False, 20)[16] == 420
    lad = u.ladder("50k", False, 16)  # peak 12
    assert lad[12] == 300 and lad[11] == 270 and lad[1] == 180 and lad[4] == 180


def test_short_plan_enters_late_and_never_jumps_more_than_an_hour():
    lad = u.ladder("100k", False, 8)  # peak_week 5
    assert lad[5] == 420 and lad[1] >= 180
    assert u.long_run_target("100k", False, 5, 8, recent_longest=240) == 300
    assert u.long_run_target("100k", False, 6, 8, recent_longest=240) is None


def test_deload_matches_plan_generator():
    for total in range(6, 30):
        for w in range(1, total + 1):
            assert u.is_deload(w, total) == PlanGenerator.is_deload_week(w, total)


def test_numbers():
    assert u.session_cap("50k", True) == 300 and u.session_cap("100k", False) == 420
    assert u.session_cap("100mi", False) == 420 and u.session_cap("100mi", True) == 480
    assert u.weekday_minutes("50k", False) == (45, 90)
    assert u.weekday_minutes("100k", True) == (60, 90)
    assert u.weekday_minutes("100mi", True) == (60, 150)
    assert u.quality_per_week(False, False) == 1 and u.quality_per_week(True, False) == 2
    assert u.quality_per_week(True, True) == 1
    assert u.quality_work_minutes(True, False) == (40, 60) and u.quality_work_minutes(True, True) == (20, 30)
    assert [u.other_day_minutes(m) for m in (180, 240, 300, 360, 420)] == [90, 90, 60, 45, 45]


def test_quality_window_is_8_weeks_to_peak_without_deloads():
    assert u.quality_weeks(20) == frozenset({9, 10, 11, 13, 14, 15, 16})  # peak 16, deload 12
    assert u.quality_weeks(8) == frozenset({1, 2, 3, 5})  # short plan: the whole build, deload 4
